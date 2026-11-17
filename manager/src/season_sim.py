"""Season sim: simulación de jornadas."""

from __future__ import annotations

import random
import zlib

from .affiliates import advance_mentoring
from .calendar import create_fixtures, league_table, recompute_table
from .competitions import COMPETITIONS, competition
from .data_loader import load_teams
from .development import advance_development
from .logistics import apply_travel, travel_options
from .match_engine import MatchEngine, MatchResult
from .models import Fixture, GameState, PlayerState, TeamState
from .scouting import advance_scouting
from .training import apply_training_plan, auto_plan
from .trials import advance_trials


def _system_code(system: str) -> str:
    return next((meta.code for meta in COMPETITIONS.values() if meta.system == system), "")


def _system_teams(state: GameState, system: str) -> list[TeamState]:
    code = _system_code(system)
    return [team for team in state.teams.values() if team.league == code] if code else []


def _system_table(state: GameState, system: str) -> list[TeamState]:
    code = _system_code(system)
    return league_table(state.teams, code) if code else []


def _world_fixtures(state: GameState) -> list[Fixture]:
    """Todos los partidos de liga regular de todas las competiciones."""
    out: list[Fixture] = []
    for fixtures in state.league_fixtures.values():
        out.extend(fixtures)
    return out


def _world_round_fixtures(state: GameState, round_no: int) -> list[Fixture]:
    return [
        fixture
        for fixture in _world_fixtures(state)
        if fixture.phase == "regular" and fixture.round == round_no and not fixture.played
    ]


def _build_world_fixtures(state: GameState, start: str | None = None) -> None:
    """Crea el calendario global mediante los sistemas de competición."""
    from .league_systems import LeagueWorld

    LeagueWorld(state).build(start)


def _sync_user_league_fixtures(state: GameState) -> None:
    if competition(state.competition).system == "dhb_two_phase" and state.fixtures:
        state.league_fixtures[state.competition] = state.fixtures


def _simulate_world_remaining(state: GameState) -> None:
    """Completa las ligas que aún tengan partidos cuando acaba la del usuario."""
    remaining = [f for f in _world_fixtures(state) if f.phase == "regular" and not f.played]
    if not remaining:
        return
    for index, fixture in enumerate(sorted(remaining, key=lambda f: (f.date, f.round, f.id))):
        if state.club_id in (fixture.home_id, fixture.away_id):
            continue
        rng = random.Random(state.seed * 1000 + fixture.round * 37 + index)
        _simulate_fixture_fast(state, fixture, rng)
    recompute_table(state.teams, _world_fixtures(state))


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _cities_for(state: GameState) -> dict[str, dict]:
    """Ciudades españolas e internacionales para el cálculo de viajes."""
    _, _, cities = load_teams()
    if competition(state.competition).international:
        from .international import international_cities

        cities.update(international_cities())
    return cities


def ensure_ai_training(state: GameState) -> None:
    """Entrenamiento automático de los clubes IA para no regalar ventaja al usuario."""
    from .season import _opponent_for_team
    if state.phase != "regular" or state.ai_training_round == state.round:
        return
    for team in state.teams.values():
        if team.league != state.competition or team.id == state.club_id:
            continue
        opponent = _opponent_for_team(state, team.id)
        rng = random.Random(state.seed * 1000 + state.round * 97 + zlib.crc32(team.id.encode("utf-8")) % 10000)
        plan = auto_plan(team, opponent, rng)
        apply_training_plan(team, plan, opponent, rng, delegated=True)
    state.ai_training_round = state.round


def ensure_week_training(state: GameState) -> dict | None:
    """Aplica el plan automático si el usuario no ha entrenado esta semana."""
    if state.phase != "regular" or state.week_trained:
        return None
    fx = state.next_user_fixture()
    opponent = None
    if fx:
        opp_id = fx.away_id if fx.home_id == state.club_id else fx.home_id
        opponent = state.teams.get(opp_id)
    rng = random.Random(state.seed * 1000 + state.round * 53 + 7)
    plan = auto_plan(state.user_team, opponent, rng)
    report = apply_training_plan(state.user_team, plan, opponent, rng, delegated=True)
    state.weekly_plan = plan
    state.training_report = report
    state.week_trained = True
    return report


def make_lineup(team: TeamState, player_ids: list[str] | None = None) -> tuple[list[PlayerState], list[PlayerState]]:
    if not player_ids:
        return team.auto_lineup()
    ids = list(dict.fromkeys(player_ids))
    by_id = {p.id: p for p in team.available_players}
    chosen = [by_id[i] for i in ids if i in by_id]
    if len(chosen) != 11:
        return team.auto_lineup()
    used = {p.id for p in chosen}
    bench = [p for p in sorted(team.available_players, key=lambda x: x.overall, reverse=True) if p.id not in used][:7]
    return chosen, bench


def _travel_for_fixture(
    state: GameState,
    fixture: Fixture,
    user_option_id: str | None,
    user_lineup: list[PlayerState],
    user_bench: list[PlayerState],
) -> dict | None:
    """Aplica el viaje del equipo visitante. Devuelve resumen para el parte."""
    away = state.teams[fixture.away_id]
    home = state.teams[fixture.home_id]
    cities_by_name = _cities_for(state)
    opts = travel_options(away, home, cities_by_name, squad_size=len(user_lineup) + len(user_bench) or 18)
    if not opts:
        return None
    chosen = None
    if away.id == state.club_id and user_option_id:
        chosen = next((o for o in opts if o["id"] == user_option_id), None)
    if not chosen:
        # IA o usuario sin elección: equilibrado si cabe, si no el más barato
        chosen = next((o for o in opts if o["id"] == "equilibrado" and o["cost"] <= away.budget), None)
        if not chosen:
            chosen = min(opts, key=lambda o: o["cost"])
    # si el usuario no puede pagar, usar el más barato
    if away.id == state.club_id and chosen["cost"] > away.budget:
        chosen = min(opts, key=lambda o: o["cost"])
    players = user_lineup + user_bench if away.id == state.club_id else None
    summary = apply_travel(away, chosen, players=players)
    summary["from"] = away.name
    summary["to"] = home.name
    summary["option_id"] = chosen["id"]
    summary["mode"] = chosen["mode"]
    summary["distance_km"] = chosen["distance_km"]
    summary["hotel_nights"] = chosen["hotel_nights"]
    return summary


def _attendance_and_gate(home: TeamState, away: TeamState, rng: random.Random) -> tuple[int, int]:
    cap = max(300, home.stadium_capacity or 1000)
    occ = 0.45 + rng.random() * 0.22
    # rival atractivo / derbi
    if away.name in ("Atlètic Terrassa HC", "Club Egara", "Junior FC", "FC Barcelona", "RC Polo"):
        occ += 0.08
    price = max(8, min(40, int(home.ticket_price or 15)))
    occ += (home.fan_confidence - 50) / 500
    occ -= (price - 15) * 0.012
    attendance = int(cap * min(0.98, max(0.18, occ)))
    revenue = attendance * price
    home.budget += revenue
    return attendance, revenue


def _update_team_management(
    team: TeamState,
    lineup: list[PlayerState],
    opponent: TeamState,
    opponent_lineup: list[PlayerState],
    gf: int,
    ga: int,
) -> None:
    """Premia o castiga la gestión: continuidad, resultado, descanso y encaje."""
    if not lineup:
        return
    result = 1 if gf > ga else (0 if gf == ga else -1)
    previous = set(team.last_lineup)
    current = {p.id for p in lineup}
    continuity = len(previous & current) / max(1, len(lineup)) if previous else 0.65
    target_cohesion = 8.0 + continuity * 8.0 + result * 1.2
    team.cohesion = int(round(_clamp(team.cohesion * 0.65 + target_cohesion * 0.35, 1, 20)))
    team_strength = sum(team.lineup_strength(lineup)) / 2
    opp_strength = sum(opponent.lineup_strength(opponent_lineup)) / 2 if opponent_lineup else 60.0
    upset = 2.0 if result > 0 and opp_strength > team_strength + 4 else 0.0
    management = team.management_score(lineup)
    delta = result * 1.2 + (management - 55.0) * 0.02 + upset
    team.manager_rating = int(round(_clamp(team.manager_rating + delta, 0, 100)))
    team.last_lineup = [p.id for p in lineup]


def _simulate_fixture(
    state: GameState,
    fixture: Fixture,
    rng: random.Random,
    user_lineup: list[PlayerState] | None = None,
    user_bench: list[PlayerState] | None = None,
    user_travel: dict | None = None,
    neutral: bool = False,
    knockout: bool = False,
    detailed: bool = True,
) -> MatchResult:
    home = state.teams[fixture.home_id]
    away = state.teams[fixture.away_id]
    if user_lineup and fixture.home_id == state.club_id:
        h_line, h_bench = user_lineup, user_bench or []
    else:
        h_line, h_bench = home.auto_lineup()
    if user_lineup and fixture.away_id == state.club_id:
        a_line, a_bench = user_lineup, user_bench or []
    else:
        a_line, a_bench = away.auto_lineup()
    # viaje del visitante (el usuario ya lo eligió; la IA usa equilibrado)
    if not neutral:
        tr = _travel_for_fixture(
            state,
            fixture,
            user_travel.get("option_id") if user_travel and away.id == state.club_id else None,
            a_line,
            a_bench,
        )
        fixture.travel = tr or {}
    user_side = 0 if fixture.home_id == state.club_id else (1 if fixture.away_id == state.club_id else None)
    if user_side is None:
        ai_sides = {0, 1}
        auto_talk_sides = {0, 1}
    else:
        ai_sides = {1 - user_side}
        auto_talk_sides = {0, 1}  # en simulación rápida el segundo entrenador asume la charla
    opposition: dict[str, str] = {}
    opposition_side = None
    if user_side is not None:
        opponent_id = away.id if user_side == 0 else home.id
        opposition = state.opposition_instructions.get(opponent_id, {})
        opposition_side = 1 - user_side
    engine = MatchEngine(
        home,
        away,
        rng,
        neutral=neutral,
        knockout=knockout,
        home_lineup=h_line,
        away_lineup=a_line,
        home_bench=h_bench,
        away_bench=a_bench,
        detailed=detailed,
        ai_sides=ai_sides,
        auto_talk_sides=auto_talk_sides,
        auto_sub_sides={0, 1},
        match_date=fixture.date,
        opposition=opposition,
        opposition_side=opposition_side,
        match_plans=state.match_plans if user_side is not None else [],
        plan_side=user_side,
    )
    result = engine.simulate()
    fixture.played = True
    fixture.home_goals = result.home_goals
    fixture.away_goals = result.away_goals
    fixture.home_stats = result.home_stats
    fixture.away_stats = result.away_stats
    fixture.events = result.events
    if not neutral:
        fixture.attendance, gate = _attendance_and_gate(home, away, rng)
        result.home_stats["gate_revenue"] = gate
    _update_team_management(
        home, engine.home_starters, away, engine.away_starters, result.home_goals, result.away_goals
    )
    _update_team_management(
        away, engine.away_starters, home, engine.home_starters, result.away_goals, result.home_goals
    )
    return result


def _simulate_fixture_fast(state: GameState, fixture: Fixture, rng: random.Random) -> None:
    """Resuelve un partido de IA sin el motor detallado.

    El usuario sí juega con MatchEngine. Para que las 16 competiciones avancen
    a la vez sin multiplicar el coste por cada partido, la IA usa el mismo
    modelo de fuerza de plantilla que las tablas de fondo, pero guarda el
    resultado en el calendario real y actualiza la clasificación.
    """
    home = state.teams[fixture.home_id]
    away = state.teams[fixture.away_id]
    home_line, _ = home.auto_lineup()
    away_line, _ = away.auto_lineup()
    home_attack, home_defense = home.lineup_strength(home_line)
    away_attack, away_defense = away.lineup_strength(away_line)
    home_goals = max(0, int(rng.gauss(2.4 + (home_attack + 4 - away_defense) / 14, 1.4)))
    away_goals = max(0, int(rng.gauss(2.2 + (away_attack - home_defense) / 14, 1.4)))
    fixture.played = True
    fixture.home_goals = home_goals
    fixture.away_goals = away_goals
    total_strength = max(1.0, home_attack + home_defense + away_attack + away_defense)
    home_possession = round(100 * (home_attack + home_defense) / total_strength, 1)
    fixture.home_stats = {
        "possession": home_possession,
        "shots": max(home_goals, int(home_goals * 2.5 + 2)),
        "shots_on_target": max(home_goals, int(home_goals * 1.5 + 1)),
        "pc": max(0, int(rng.gauss(4, 2))),
        "saves": max(0, int(rng.gauss(4, 2))),
        "green": 0,
        "yellow": 0,
        "red": 0,
        "gate_revenue": 0,
    }
    fixture.away_stats = {
        "possession": round(100 - home_possession, 1),
        "shots": max(away_goals, int(away_goals * 2.5 + 2)),
        "shots_on_target": max(away_goals, int(away_goals * 1.5 + 1)),
        "pc": max(0, int(rng.gauss(3, 2))),
        "saves": max(0, int(rng.gauss(4, 2))),
        "green": 0,
        "yellow": 0,
        "red": 0,
        "gate_revenue": 0,
    }
    for team, lineup, goals in ((home, home_line, home_goals), (away, away_line, away_goals)):
        for player in lineup:
            player.apps += 1
            player.rating_sum += 6.5
        candidates = [p for p in lineup if p.position_group in ("Delantero", "Medio")] or lineup
        for _ in range(goals):
            scorer = rng.choice(candidates)
            scorer.season_goals += 1
        if goals > (away_goals if team is home else home_goals):
            team.morale = min(20, team.morale + 1)
        elif goals < (away_goals if team is home else home_goals):
            team.morale = max(1, team.morale - 1)


def _reset_week_training(state: GameState) -> None:
    state.week_trained = False
    state.weekly_plan = []
    state.training_report = {}
    for t in state.teams.values():
        t.prep_bonus = 0.0
    advance_mentoring(state)
    advance_scouting(state)
    advance_development(state)
    advance_trials(state)


def _user_result_payload(state: GameState, fixture: Fixture, result: MatchResult, travel: dict | None) -> dict:
    home = state.teams[fixture.home_id]
    away = state.teams[fixture.away_id]
    user_is_home = fixture.home_id == state.club_id
    gf = result.home_goals if user_is_home else result.away_goals
    ga = result.away_goals if user_is_home else result.home_goals
    user_ratings = result.home_ratings if user_is_home else result.away_ratings
    user_stats = result.home_stats if user_is_home else result.away_stats
    players = {p.id: p.name for p in state.user_team.players}
    ratings = {players.get(pid, pid): r for pid, r in user_ratings.items() if pid in players}
    return {
        "fixture_id": fixture.id,
        "round": fixture.round,
        "phase": fixture.phase,
        "home_id": home.id,
        "home_name": home.name,
        "away_id": away.id,
        "away_name": away.name,
        "home_goals": result.home_goals,
        "away_goals": result.away_goals,
        "user_is_home": user_is_home,
        "user_goals": gf,
        "user_against": ga,
        "result": "Victoria" if gf > ga else ("Empate" if gf == ga else "Derrota"),
        "events": result.events,
        "home_stats": result.home_stats,
        "away_stats": result.away_stats,
        "user_stats": user_stats,
        "ratings": ratings,
        "injuries": result.injuries,
        "cards": result.cards,
        "player_minutes": result.player_minutes,
        "attendance": fixture.attendance,
        "travel": (travel or {}) if not user_is_home else {},
        "home_management": home.management_profile(),
        "away_management": away.management_profile(),
        "prep_bonus": state.user_team.prep_bonus,
        "shootout": result.shootout,
        "referee": result.referee,
        "reviews": result.reviews,
        "added_time": result.added_time,
        "date": fixture.date,
    }


def _update_user_after_match(state: GameState, fixture: Fixture, result: MatchResult) -> None:
    user = state.user_team
    is_home = fixture.home_id == user.id
    gf = result.home_goals if is_home else result.away_goals
    ga = result.away_goals if is_home else result.home_goals
    if gf > ga:
        user.board_confidence = _clamp(user.board_confidence + 2, 0, 100)
        user.fan_confidence = _clamp(user.fan_confidence + 2, 0, 100)
        for p in user.players:
            p.morale = _clamp(p.morale + 1, 1, 20)
    elif gf < ga:
        user.board_confidence = _clamp(user.board_confidence - 2, 0, 100)
        user.fan_confidence = _clamp(user.fan_confidence - 2, 0, 100)
        for p in user.players:
            p.morale = _clamp(p.morale - 1, 1, 20)
    else:
        user.fan_confidence = _clamp(user.fan_confidence, 0, 100)
    if user.budget < 0:
        user.board_confidence = _clamp(user.board_confidence - 3, 0, 100)
    # goleadores: subida de moral
    for p in user.players:
        if p.season_goals and p.id in {e.get("player_id") for e in result.events if e.get("type") == "goal"}:
            p.morale = _clamp(p.morale + 1, 1, 20)


def _recover_after_round(state: GameState, old_status: dict[str, tuple[int, int]]) -> None:
    for t in state.teams.values():
        for p in t.players:
            p.fatigue = max(0.0, p.fatigue - 14.0)
            inj, sus = old_status.get(p.id, (0, 0))
            if inj > 0:
                p.injury = max(0, p.injury - 1)
            if sus > 0:
                p.suspension = max(0, p.suspension - 1)
            if p.injury <= 0:
                p.injury_type = ""
                p.injury_severity = ""
                p.injury_started = ""
                p.injury_expected = 0
            if p.suspension <= 0:
                p.suspension_reason = ""
                p.suspension_started = ""
            if p.injury <= 0 and p.suspension <= 0:
                p.absence_note = ""


def _best_dhb_team(state: GameState) -> TeamState:
    dhb = _system_teams(state, "dhb_two_phase")
    if not dhb:
        return None

    def strength(t):
        line, _ = t.auto_lineup()
        a, d = t.lineup_strength(line)
        return a + d

    return max(dhb, key=strength)


def _background_table(state: GameState, league: str) -> list[dict]:
    teams = [t for t in state.teams.values() if t.league == league]
    if len(teams) < 2:
        return []
    ids = sorted(t.id for t in teams)
    fixtures = create_fixtures(ids, state.date)
    rng = random.Random(state.seed + zlib.crc32(league.encode("utf-8")) + int(state.season[:4]))
    rows = {t.id: {"team": t, "points": 0, "gf": 0, "ga": 0, "won": 0, "drawn": 0, "lost": 0} for t in teams}
    for fx in fixtures:
        h, a = rows[fx.home_id], rows[fx.away_id]
        hl, _ = h["team"].auto_lineup()
        al, _ = a["team"].auto_lineup()
        ha, hd = h["team"].lineup_strength(hl)
        aa, ad = a["team"].lineup_strength(al)
        hg = max(0, int(rng.gauss(2.4 + (ha + 4 - ad) / 14, 1.4)))
        ag = max(0, int(rng.gauss(2.2 + (aa - hd) / 14, 1.4)))
        h["gf"] += hg
        h["ga"] += ag
        a["gf"] += ag
        a["ga"] += hg
        if hg > ag:
            h["points"] += 3
            h["won"] += 1
            a["lost"] += 1
        elif hg < ag:
            a["points"] += 3
            a["won"] += 1
            h["lost"] += 1
        else:
            h["points"] += 1
            a["points"] += 1
            h["drawn"] += 1
            a["drawn"] += 1
    return sorted(rows.values(), key=lambda r: (-r["points"], -(r["gf"] - r["ga"]), -r["gf"], r["team"].name))
