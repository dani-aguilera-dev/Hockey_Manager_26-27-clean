"""Gestión de la temporada DHA: calendario, jornadas, Final Four y playout."""

from __future__ import annotations

import random
import zlib
from dataclasses import dataclass
from datetime import date, timedelta

from .awards import archive_season_awards
from .calendar import create_fixtures, league_table, recompute_table
from .competitions import (
    DEFAULT_REGIONAL_LEAGUE,
    MARKET_SOURCE_SYSTEMS,
    MIN_MATCHDAY_SQUAD,
    MIN_ROSTER_SIZE,
    competition,
    is_regional,
)
from .cup import CUP_ACTIVATION_ROUND, CUP_OFFSETS, ROUND_PHASES, cup_round_fixtures, cup_start, new_cup
from .ehl import create_ehl, simulate_ehl
from .finance import apply_round_finances
from .history import archive_season
from .loans import return_loans
from .logistics import apply_travel, travel_options
from .managers import (
    process_manager_changes,
    process_user_sacking,
    record_manager_change,
    replacement_manager,
)
from .match_engine import MatchEngine
from .models import Fixture, GameState, PlayerState, TeamState
from .season_promotion import (
    _actual_promotion_groups as _actual_promotion_groups,
)
from .season_promotion import (
    _actual_regional_promoted as _actual_regional_promoted,
)
from .season_promotion import (
    _add_regional_team as _add_regional_team,
)
from .season_promotion import (
    _advance_promotion_groups as _advance_promotion_groups,
)
from .season_promotion import (
    _background_dhb_relegated as _background_dhb_relegated,
)
from .season_promotion import (
    _background_dhb_table as _background_dhb_table,
)
from .season_promotion import (
    _background_regional_promoted as _background_regional_promoted,
)
from .season_promotion import (
    _create_promotion_groups as _create_promotion_groups,
)
from .season_promotion import (
    _dhb_group_table as _dhb_group_table,
)
from .season_promotion import (
    _dhb_groups_by_strength as _dhb_groups_by_strength,
)
from .season_promotion import (
    _ensure_regional_league as _ensure_regional_league,
)
from .season_promotion import (
    _fast_group_rows as _fast_group_rows,
)
from .season_promotion import (
    _fast_rows_for_teams as _fast_rows_for_teams,
)
from .season_promotion import (
    _finish_promotion as _finish_promotion,
)
from .season_promotion import (
    _make_promotion_fixtures as _make_promotion_fixtures,
)
from .season_promotion import (
    _play_promotion_group as _play_promotion_group,
)
from .season_promotion import (
    _promotion_rows as _promotion_rows,
)
from .season_promotion import (
    _promotion_table_rows as _promotion_table_rows,
)
from .season_promotion import (
    _refresh_promotion_tables as _refresh_promotion_tables,
)
from .season_promotion import (
    _regional_qualifying_rows as _regional_qualifying_rows,
)
from .season_promotion import (
    _simulate_dhb_final4 as _simulate_dhb_final4,
)
from .season_promotion import (
    _simulate_promotion_auto as _simulate_promotion_auto,
)
from .season_promotion import (
    _simulate_promotion_fixtures as _simulate_promotion_fixtures,
)
from .season_promotion import (
    _table_from_fixtures as _table_from_fixtures,
)
from .season_promotion import (
    play_final_four as play_final_four,
)
from .season_promotion import (
    play_promotion_round as play_promotion_round,
)
from .season_promotion import (
    setup_dhb_phase1 as setup_dhb_phase1,
)
from .season_promotion import (
    setup_dhb_phase2 as setup_dhb_phase2,
)
from .season_sim import (
    _attendance_and_gate as _attendance_and_gate,
)
from .season_sim import (
    _background_table as _background_table,
)
from .season_sim import (
    _best_dhb_team as _best_dhb_team,
)
from .season_sim import (
    _build_world_fixtures as _build_world_fixtures,
)
from .season_sim import (
    _cities_for as _cities_for,
)
from .season_sim import (
    _clamp as _clamp,
)
from .season_sim import (
    _recover_after_round as _recover_after_round,
)
from .season_sim import (
    _reset_week_training as _reset_week_training,
)
from .season_sim import (
    _simulate_fixture as _simulate_fixture,
)
from .season_sim import (
    _simulate_fixture_fast as _simulate_fixture_fast,
)
from .season_sim import (
    _simulate_world_remaining as _simulate_world_remaining,
)
from .season_sim import (
    _sync_user_league_fixtures as _sync_user_league_fixtures,
)
from .season_sim import (
    _system_code as _system_code,
)
from .season_sim import (
    _system_table as _system_table,
)
from .season_sim import (
    _system_teams as _system_teams,
)
from .season_sim import (
    _travel_for_fixture as _travel_for_fixture,
)
from .season_sim import (
    _update_team_management as _update_team_management,
)
from .season_sim import (
    _update_user_after_match as _update_user_after_match,
)
from .season_sim import (
    _user_result_payload as _user_result_payload,
)
from .season_sim import (
    _world_fixtures as _world_fixtures,
)
from .season_sim import (
    _world_round_fixtures as _world_round_fixtures,
)
from .season_sim import (
    ensure_ai_training as ensure_ai_training,
)
from .season_sim import (
    ensure_week_training as ensure_week_training,
)
from .season_sim import (
    make_lineup as make_lineup,
)
from .youth import develop_youth, generate_youth, initial_youth, intake


# Fase Nacional de ascenso a DHB (RFEH, Circular nº1 2026-27, apartado 1.3).
# Los equipos se agrupan por zonas geográficas a partir de la clasificación de
# sus ligas autonómicas. Cada grupo juega una liguilla a partido único; los
# cuatro campeones disputan la liguilla final y los dos primeros ascienden.
def regional_league_for(team: TeamState, state: GameState) -> str:
    """Elige la liga autonómica de destino a partir de los equipos reales.

    No hay un mapa de comunidades hardcodeado: se buscan los clubes de la
    misma comunidad en las ligas regionales y se elige la competición de mayor
    nivel. Si una comunidad no tiene representación, se usa la liga de respaldo
    declarada en ``league_rules.json``.
    """
    candidates = [
        other
        for other in state.teams.values()
        if is_regional(other.league) and other.community == team.community
    ]
    if not candidates:
        return DEFAULT_REGIONAL_LEAGUE
    counts: dict[str, int] = {}
    for other in candidates:
        counts[other.league] = counts.get(other.league, 0) + 1
    return max(counts, key=lambda code: (counts[code], competition(code).standard))


















def _dedupe_players(state: GameState) -> None:
    """Un jugador solo puede pertenecer a un club en todo el mundo.

    Las fuentes internacionales publican a algunos jugadores en su club
    europeo y en la India. Se conserva la ficha del club del usuario, después
    las ligas españolas y por último el resto de competiciones.
    """
    from .data_loader import norm

    def priority(team: TeamState) -> tuple[int, str]:
        if team.id == state.club_id:
            return (0, team.name)
        if competition(team.league).system in ("dha", "dhb_two_phase"):
            return (1, team.name)
        if is_regional(team.league):
            return (2, team.name)
        return (3, team.name)

    seen: set[str] = set()
    for team in sorted(state.teams.values(), key=priority):
        kept: list[PlayerState] = []
        for player in team.players:
            key = norm(player.name)
            if key in seen:
                continue
            seen.add(key)
            kept.append(player)
        team.players = kept


def _seed_free_agents(state: GameState) -> None:
    """Separa plantillas reales de invitados y agentes libres.

    No se toca la ficha de ningún jugador oficial: cada club conserva todos
    sus ``Jugador``. Los ``Invitado`` pasan al mercado y solo se reincorporan
    si un club no llega al mínimo de alineación. El cuerpo técnico no se mezcla
    con los futbolistas. No hay equipos protegidos a mano.
    """
    pool: list[PlayerState] = []
    for team in sorted(state.teams.values(), key=lambda item: item.id):
        if competition(team.league).system not in MARKET_SOURCE_SYSTEMS:
            continue
        players = [player for player in team.players if player.perfil == "Jugador"]
        guests = [player for player in team.players if player.perfil == "Invitado"]
        team.players = players
        for player in guests:
            player.origin_team = player.origin_team or team.name
            player.team_name = "Agente libre"
            player.league = team.league
            player.salary = max(player.salary, int(max(5000, (player.overall - 40) * 1100)))
            pool.append(player)
    # Regla general: ningún club empieza por debajo del mínimo de alineación.
    # Se completa con el mercado real, priorizando la misma liga y el nivel
    # más bajo disponible para no inflar plantillas ya completas.
    for team in state.teams.values():
        if len(team.players) >= MIN_MATCHDAY_SQUAD:
            continue
        candidates = [player for player in pool if player.league == team.league]
        candidates += [player for player in pool if player.league != team.league]
        candidates.sort(key=lambda player: (player.overall, player.age, player.name))
        while len(team.players) < MIN_MATCHDAY_SQUAD and candidates:
            player = candidates.pop(0)
            if player not in pool:
                continue
            pool.remove(player)
            player.team_name = team.name
            player.league = team.league
            team.players.append(player)
    state.free_agents = pool



def new_game(club_id: str, manager_name: str = "Entrenador", seed: int | None = None) -> GameState:
    # El mercado es global: todas las ligas deben estar disponibles para
    # fichar, vender y generar ofertas cruzadas desde el primer día.
    from .international import load_all_teams
    from .regional import load_regional_teams

    teams, clubs_by_id, cities_by_name = load_all_teams()
    regional_teams, regional_clubs, regional_cities = load_regional_teams()
    teams.update(regional_teams)
    clubs_by_id.update(regional_clubs)
    cities_by_name.update(regional_cities)
    if club_id not in teams:
        raise ValueError(f"Club desconocido: {club_id}")
    league = teams[club_id].league
    meta = competition(league)
    if not meta.international and meta.system not in ("regional", "dha", "dhb_two_phase"):
        raise ValueError("Solo se puede dirigir un club de una liga jugable")
    state = GameState(
        manager_name=manager_name,
        club_id=club_id,
        season="2026-27",
        competition=league,
        country=meta.country,
        seed=seed if seed is not None else random.randint(1, 999_999),
        round=1,
        date=meta.start_date,
        fixtures=[],
        teams=teams,
    )
    state.teams[club_id].manager_name = manager_name
    state.teams[club_id].manager_pressure = 0
    state.teams[club_id].manager_since_round = 0
    # pequeña pretemporada: moral y forma iniciales razonables
    for t in state.teams.values():
        if competition(t.league).system == "dha":
            t.morale = 12
            for p in t.players:
                p.form = 6.2 + random.Random(state.seed + zlib.crc32(p.id.encode("utf-8")) % 1000).random() * 0.9
    sync_player_leagues(state)
    _dedupe_players(state)
    _seed_free_agents(state)
    initial_youth(state.teams, state.seed)
    _build_world_fixtures(state)
    if meta.system == "dhb_two_phase":
        setup_dhb_phase1(state, meta.start_date)
        _sync_user_league_fixtures(state)
    first_regular = next((f.date for f in state.fixtures if f.phase == "regular"), meta.start_date)
    state.date = (date.fromisoformat(first_regular) - timedelta(days=50)).isoformat()
    state.inbox.append(
        {
            "date": "2026-08-01",
            "from": "Junta Directiva",
            "subject": f"Bienvenido al {state.user_team.name}",
            "body": (
                f"La junta te confía el primer equipo para la temporada 2026-27. "
                f"Objetivo: {state.user_team.board_expectation}. "
                f"La {meta.name} arranca el {first_regular}. "
                f"Tienes {state.total_rounds} jornadas para cumplir el objetivo de la junta."
            ),
        }
    )
    return state


def sync_player_leagues(state: GameState) -> None:
    """Mantiene la categoría del jugador alineada con la de su club."""
    for team in state.teams.values():
        for player in team.players:
            player.league = team.league
    for player in state.free_agents:
        if not player.league:
            player.league = DEFAULT_REGIONAL_LEAGUE




def _opponent_for_team(state: GameState, team_id: str) -> TeamState | None:
    for f in state.fixtures:
        if f.phase == "regular" and f.round == state.round and not f.played:
            if f.home_id == team_id:
                return state.teams.get(f.away_id)
            if f.away_id == team_id:
                return state.teams.get(f.home_id)
    return None






















def play_round(
    state: GameState, user_lineup_ids: list[str] | None = None, travel_option_id: str | None = None
) -> dict | None:
    """Simula la jornada regular actual. Devuelve el parte del partido del usuario."""
    if state.phase == "promotion":
        return play_promotion_round(state, user_lineup_ids)
    if state.phase != "regular":
        return None
    ensure_week_training(state)
    ensure_ai_training(state)
    round_no = state.round
    fixtures = _world_round_fixtures(state, round_no)
    if not fixtures:
        return None
    old_status = {p.id: (p.injury, p.suspension) for t in state.teams.values() for p in t.players}
    effective_ids = user_lineup_ids if user_lineup_ids is not None else (state.manual_lineup or None)
    user_lineup, user_bench = make_lineup(state.user_team, effective_ids)
    user_fixture = next((f for f in fixtures if state.club_id in (f.home_id, f.away_id)), None)
    user_travel = None
    if user_fixture and user_fixture.away_id == state.club_id:
        cities = _cities_for(state)
        opts = travel_options(state.user_team, state.teams[user_fixture.home_id], cities, squad_size=18)
        user_travel = {"option_id": travel_option_id}
        # el resumen real se rellena al simular; aquí solo validamos que exista
        if travel_option_id and not any(o["id"] == travel_option_id for o in opts):
            user_travel["option_id"] = "equilibrado"
    user_payload = None
    for idx, fx in enumerate(fixtures):
        rng = random.Random(state.seed * 1000 + round_no * 37 + idx)
        is_user = state.club_id in (fx.home_id, fx.away_id)
        if is_user:
            result = _simulate_fixture(
                state,
                fx,
                rng,
                user_lineup=user_lineup,
                user_bench=user_bench,
                user_travel=user_travel,
                detailed=True,
            )
            user_payload = _user_result_payload(state, fx, result, fx.travel)
            state.last_result = user_payload
            _update_user_after_match(state, fx, result)
        else:
            _simulate_fixture_fast(state, fx, rng)
    # clasificación, cambios de entrenador y recuperación
    recompute_table(state.teams, _world_fixtures(state))
    process_manager_changes(state)
    process_user_sacking(state)
    _recover_after_round(state, old_status)
    apply_round_finances(state)
    _reset_week_training(state)
    state.round += 1
    _maybe_setup_dhb_phase2(state)
    _sync_user_league_fixtures(state)
    _maybe_create_cup(state)
    _maybe_create_ehl(state)
    if state.round <= state.total_rounds:
        if user_fixture:
            state.date = (date.fromisoformat(user_fixture.date) + timedelta(days=1)).isoformat()
    else:
        _simulate_world_remaining(state)
        finish_regular_season(state)
    return user_payload


@dataclass
class LiveRoundContext:
    fixture: Fixture
    engine: MatchEngine
    old_status: dict[str, tuple[int, int]]
    user_side: int
    travel: dict | None
    rng: random.Random


def prepare_live_round(
    state: GameState, user_lineup_ids: list[str] | None = None, travel_option_id: str | None = None
) -> LiveRoundContext:
    """Prepara el partido del usuario en modo directo.

    Simula primero el resto de la jornada y deja el partido del usuario listo
    para avanzar cuarto a cuarto o momento a momento. No actualiza clasificación
    ni recuperación hasta `finish_live_round`.
    """
    if state.phase not in ("regular", "promotion"):
        raise ValueError("La temporada ya ha terminado.")
    ensure_week_training(state)
    ensure_ai_training(state)
    if state.phase == "promotion":
        round_no = state.promotion_round
        stage = state.promotion.get("stage", "groups")
        phase = "promotion_group" if stage == "groups" else "promotion_final"
        fixtures = [
            fixture
            for fixture in state.league_fixtures.get("PROMOTION", [])
            if fixture.phase == phase and fixture.round == round_no and not fixture.played
        ]
    else:
        round_no = state.round
        fixtures = _world_round_fixtures(state, round_no)
    if not fixtures:
        raise ValueError("No hay partidos pendientes en esta jornada.")
    old_status = {p.id: (p.injury, p.suspension) for t in state.teams.values() for p in t.players}
    effective_ids = user_lineup_ids if user_lineup_ids is not None else (state.manual_lineup or None)
    user_lineup, user_bench = make_lineup(state.user_team, effective_ids)
    user_fixture = next((f for f in fixtures if state.club_id in (f.home_id, f.away_id)), None)
    if user_fixture is None:
        raise ValueError("El equipo del usuario no juega esta jornada.")
    # El resto de la jornada se resuelve antes del partido en directo.
    for idx, fx in enumerate(fixtures):
        if fx.id == user_fixture.id:
            continue
        rng_other = random.Random(state.seed * 1000 + round_no * 37 + idx)
        _simulate_fixture_fast(state, fx, rng_other)
    home = state.teams[user_fixture.home_id]
    away = state.teams[user_fixture.away_id]
    if user_fixture.home_id == state.club_id:
        h_line, h_bench = user_lineup, user_bench
        a_line, a_bench = away.auto_lineup()
        user_side = 0
    else:
        a_line, a_bench = user_lineup, user_bench
        h_line, h_bench = home.auto_lineup()
        user_side = 1
    travel = None
    if state.phase == "promotion":
        user_fixture.travel = {}
    elif user_fixture.away_id == state.club_id:
        cities = _cities_for(state)
        opts = travel_options(state.user_team, home, cities, squad_size=18)
        chosen = next((o for o in opts if o["id"] == travel_option_id), None)
        if chosen is None:
            chosen = next((o for o in opts if o["id"] == "equilibrado" and o["cost"] <= state.user_team.budget), None)
        if chosen is None:
            chosen = min(opts, key=lambda o: o["cost"])
        if chosen["cost"] > state.user_team.budget:
            chosen = min(opts, key=lambda o: o["cost"])
        travel = apply_travel(state.user_team, chosen, players=user_lineup + user_bench)
        travel.update(
            {
                "from": state.user_team.name,
                "to": home.name,
                "option_id": chosen["id"],
                "mode": chosen["mode"],
                "distance_km": chosen["distance_km"],
                "hotel_nights": chosen["hotel_nights"],
            }
        )
        user_fixture.travel = travel
    else:
        travel = _travel_for_fixture(state, user_fixture, None, a_line, a_bench)
        user_fixture.travel = travel or {}
    idx_user = fixtures.index(user_fixture)
    rng = random.Random(state.seed * 1000 + round_no * 37 + idx_user)
    ai_side = 1 - user_side
    opponent_id = away.id if user_side == 0 else home.id
    opposition = state.opposition_instructions.get(opponent_id, {})
    engine = MatchEngine(
        home,
        away,
        rng,
        neutral=state.phase == "promotion",
        knockout=False,
        home_lineup=h_line,
        away_lineup=a_line,
        home_bench=h_bench,
        away_bench=a_bench,
        detailed=True,
        auto_sub_sides={ai_side},
        ai_sides={ai_side},
        auto_talk_sides={ai_side},
        match_date=user_fixture.date,
        opposition=opposition,
        opposition_side=ai_side,
        match_plans=state.match_plans,
        plan_side=user_side,
    )
    return LiveRoundContext(
        fixture=user_fixture,
        engine=engine,
        old_status=old_status,
        user_side=user_side,
        travel=travel if user_side == 1 else None,
        rng=rng,
    )


def finish_live_round(state: GameState, ctx: LiveRoundContext) -> dict:
    """Cierra el partido en directo, actualiza la jornada y devuelve el parte."""
    engine = ctx.engine
    if engine.result is None:
        engine.simulate()
    result = engine.result
    if result is None:
        raise ValueError("El partido no tiene resultado.")
    fixture = ctx.fixture
    home = state.teams[fixture.home_id]
    away = state.teams[fixture.away_id]
    fixture.played = True
    fixture.home_goals = result.home_goals
    fixture.away_goals = result.away_goals
    fixture.home_stats = result.home_stats
    fixture.away_stats = result.away_stats
    fixture.events = result.events
    if not engine.neutral:
        fixture.attendance, gate = _attendance_and_gate(home, away, ctx.rng)
        result.home_stats["gate_revenue"] = gate
    _update_team_management(
        home, engine.home_starters, away, engine.away_starters, result.home_goals, result.away_goals
    )
    _update_team_management(
        away, engine.away_starters, home, engine.home_starters, result.away_goals, result.home_goals
    )
    user_payload = _user_result_payload(state, fixture, result, ctx.travel)
    state.last_result = user_payload
    _update_user_after_match(state, fixture, result)
    if state.phase == "promotion":
        _refresh_promotion_tables(state)
        _recover_after_round(state, ctx.old_status)
        _reset_week_training(state)
        stage = state.promotion.get("stage", "groups")
        state.promotion_round += 1
        if state.promotion_round > 3:
            if stage == "groups":
                _advance_promotion_groups(state)
            else:
                _finish_promotion(state)
        else:
            state.date = (date.fromisoformat(fixture.date) + timedelta(days=1)).isoformat()
        return user_payload
    recompute_table(state.teams, _world_fixtures(state))
    process_manager_changes(state)
    process_user_sacking(state)
    _recover_after_round(state, ctx.old_status)
    apply_round_finances(state)
    _reset_week_training(state)
    state.round += 1
    _maybe_setup_dhb_phase2(state)
    _sync_user_league_fixtures(state)
    _maybe_create_cup(state)
    _maybe_create_ehl(state)
    if state.round <= state.total_rounds:
        if fixture:
            state.date = (date.fromisoformat(fixture.date) + timedelta(days=1)).isoformat()
    else:
        _simulate_world_remaining(state)
        finish_regular_season(state)
    return user_payload


def _maybe_setup_dhb_phase2(state: GameState) -> None:
    if (
        competition(state.competition).system == "dhb_two_phase"
        and state.dhb_phase == 1
        and state.round == 15
    ):
        setup_dhb_phase2(state)










def simulate_cup_round(state: GameState, user_lineup_ids: list[str] | None = None) -> dict | None:
    """Simula cuartos, semifinal o final/tercer puesto a partido único."""
    if not state.cup_active:
        return None
    fixtures = cup_round_fixtures(state)
    if not fixtures:
        return None
    current_round = state.cup_round
    payload = None
    winners = []
    losers = []
    for idx, fx in enumerate(fixtures):
        if fx.played:
            home_won = fx.home_goals > fx.away_goals
            winners.append(fx.home_id if home_won else fx.away_id)
            losers.append(fx.away_id if home_won else fx.home_id)
            continue
        rng = random.Random(state.seed + current_round * 300 + idx)
        is_user = state.club_id in (fx.home_id, fx.away_id)
        line, bench = (
            make_lineup(
                state.user_team, user_lineup_ids if user_lineup_ids is not None else (state.manual_lineup or None)
            )
            if is_user
            else (None, None)
        )
        res = _simulate_fixture(state, fx, rng, user_lineup=line, user_bench=bench, neutral=False, knockout=True)
        home_won = res.shootout.get("winner_id") == fx.home_id if res.shootout else fx.home_goals > fx.away_goals
        winner = fx.home_id if home_won else fx.away_id
        loser = fx.away_id if home_won else fx.home_id
        winners.append(winner)
        losers.append(loser)
        if is_user:
            payload = _user_result_payload(state, fx, res, fx.travel)
            state.last_result = payload
    if current_round == 1:
        next_phase = ROUND_PHASES[2]
        from datetime import date as _date

        base = cup_start(state).toordinal() + CUP_OFFSETS[1]
        for i in range(0, len(winners), 2):
            state.fixtures.append(
                Fixture(
                    id=f"C2-{i // 2 + 1}",
                    round=102,
                    date=_date.fromordinal(base).isoformat(),
                    home_id=winners[i],
                    away_id=winners[i + 1],
                    phase=next_phase,
                )
            )
        state.cup_round = 2
    elif current_round == 2:
        from datetime import date as _date

        base = cup_start(state).toordinal() + CUP_OFFSETS[2]
        date_s = _date.fromordinal(base).isoformat()
        state.fixtures.append(
            Fixture(
                id="C3-F",
                round=103,
                date=date_s,
                home_id=winners[0],
                away_id=winners[1],
                phase=ROUND_PHASES[3],
            )
        )
        state.fixtures.append(
            Fixture(
                id="C3-T",
                round=103,
                date=date_s,
                home_id=losers[0],
                away_id=losers[1],
                phase="cup_third",
            )
        )
        state.cup_round = 3
    else:
        final = next((f for f in fixtures if f.phase == ROUND_PHASES[3]), None)
        third = next((f for f in fixtures if f.phase == "cup_third"), None)
        if final:
            winner = final.home_id if final.home_goals > final.away_goals else final.away_id
            if final.home_goals == final.away_goals:
                winner = state.seed % 2 == 0 and final.home_id or final.away_id
            state.cup_winner_id = winner
            if winner in state.teams:
                state.teams[winner].budget += 50000
                state.teams[winner].board_confidence = min(100, state.teams[winner].board_confidence + 4)
            if winner == state.club_id:
                state.user_team.fan_confidence = min(100, state.user_team.fan_confidence + 8)
                state.inbox.append(
                    {
                        "date": state.date,
                        "from": "Prensa",
                        "subject": "¡Campeón de Copa!",
                        "body": "El club ha ganado la Copa del Rey. La afición está eufórica.",
                    }
                )
        if third:
            state.cup_third_id = third.home_id if third.home_goals > third.away_goals else third.away_id
        state.cup_active = False
        _maybe_create_ehl(state)
    played_dates = [date.fromisoformat(f.date) for f in state.fixtures if f.phase.startswith("cup_") and f.played]
    if played_dates:
        state.date = max(date.fromisoformat(state.date), max(played_dates) + timedelta(days=1)).isoformat()
    return payload


def simulate_cup_remaining(state: GameState) -> None:
    while state.cup_active:
        simulate_cup_round(state)
        if state.cup_round > 3:
            break


def _maybe_create_cup(state: GameState) -> None:
    """La Copa se crea tras la primera vuelta (jornada 11) con los 8 mejores de DHA."""
    if competition(state.competition).system != "dha":
        return
    if state.cup_active or state.cup_winner_id:
        return
    if state.round == CUP_ACTIVATION_ROUND:
        new_cup(state)


def _maybe_create_ehl(state: GameState) -> None:
    if competition(state.competition).system not in ("dha", "dhb_two_phase"):
        return
    if state.ehl and (state.ehl.get("active") or state.ehl.get("winner_id")):
        return
    if state.round < 12:
        return
    # En DHA esperamos a la final de Copa para que el campeón sea uno de los
    # tres clasificados españoles. En DHB no hay Copa y se crea tras la primera vuelta.
    if competition(state.competition).system == "dha" and state.cup_active:
        return
    create_ehl(state)


























































def _board_target(team: TeamState, code: str) -> int:
    e = (team.board_expectation or "").lower()
    if "ganar la liga" in e or "título" in e:
        return 1
    if "final four" in e or "top 4" in e:
        return 4
    if "top 6" in e:
        return 6
    if "top 8" in e:
        return 8
    if "ascenso" in e:
        return 2
    if "play-off" in e or "playoff" in e:
        return 4
    if "permanencia" in e or "salvación" in e:
        return 10 if competition(code).system == "dha" else 12
    return 8


def _board_review(state: GameState) -> dict:
    table = state.table()
    pos = next((i for i, t in enumerate(table, 1) if t.id == state.club_id), len(table))
    target = _board_target(state.user_team, state.competition)
    met = pos <= target
    before = state.user_team.board_confidence
    if met:
        delta = 10 if pos < target else 6
        budget_factor = 1.12
        message = "La junta está satisfecha con el objetivo cumplido."
    else:
        delta = -12 if pos > target + 3 else -8
        budget_factor = 0.90
        message = "La junta considera que el equipo se ha quedado corto."
    state.user_team.board_confidence = max(0, min(100, before + delta))
    state.user_team.transfer_budget = int(state.user_team.transfer_budget * budget_factor)
    if state.user_team.board_confidence <= 15:
        message += " Hay riesgo de destitución."
    review = {
        "target": target,
        "position": pos,
        "met": met,
        "confidence_before": before,
        "confidence_after": state.user_team.board_confidence,
        "transfer_budget_after": state.user_team.transfer_budget,
        "message": message,
    }
    state.board_review = review
    state.inbox.append(
        {
            "date": state.date,
            "from": "Junta Directiva",
            "subject": "Revisión de temporada",
            "body": f"{message} Objetivo: {target}º · Posición: {pos}º.",
        }
    )
    return review


def _process_age_and_retirements(state: GameState) -> None:
    """Envejece a los jugadores y decide retiradas al final de la temporada."""
    state.retirements = []
    rng = random.Random(state.seed + int(state.season[:4]) + 313)
    for team in state.teams.values():
        if competition(team.league).system not in ("dha", "dhb_two_phase") and team.league != state.competition:
            continue
        kept = []
        for p in team.players:
            p.age += 1
            chance = 0.0
            if p.age >= 40:
                chance = 1.0
            elif p.age >= 37:
                chance = 0.75
            elif p.age >= 35:
                chance = 0.40
            elif p.age >= 33:
                chance = 0.15
            elif p.age >= 31:
                chance = 0.03
            if p.overall < 58 and p.age >= 30:
                chance += 0.05
            # Las estrellas cuidan más su carrera y se retiran algo más tarde.
            if p.overall >= 85:
                chance *= 0.50
            elif p.overall >= 78:
                chance *= 0.75
            if rng.random() < chance:
                state.retirements.append(
                    {
                        "season": state.season,
                        "player": p.name,
                        "club": team.name,
                        "age": p.age,
                        "overall": round(p.overall, 1),
                        "goals": p.season_goals,
                    }
                )
                if p.overall >= 78 or team.id == state.club_id:
                    state.inbox.append(
                        {
                            "date": state.date,
                            "from": "Club",
                            "subject": f"Retirada de {p.name}",
                            "body": f"{p.name} se retira a los {p.age} años tras una carrera en {team.name}.",
                        }
                    )
                continue
            kept.append(p)
        team.players = kept
    kept_free = []
    for p in state.free_agents:
        p.age += 1
        chance = 0.95 if p.age >= 37 else (0.55 if p.age >= 35 else (0.25 if p.age >= 33 else 0.0))
        if rng.random() < chance:
            state.retirements.append(
                {
                    "season": state.season,
                    "player": p.name,
                    "club": "Agente libre",
                    "age": p.age,
                    "overall": round(p.overall, 1),
                    "goals": p.season_goals,
                }
            )
        else:
            kept_free.append(p)
    state.free_agents = kept_free


def record_season_career(state: GameState) -> None:
    """Guarda una foto de la temporada en el histórico de cada jugador."""
    for team in state.teams.values():
        if competition(team.league).system not in ("dha", "dhb_two_phase") and team.league != state.competition:
            continue
        for player in team.players:
            if not (player.apps or player.season_goals or player.season_assists):
                continue
            entry = {
                "season": state.season,
                "club": team.name,
                "league": team.league,
                "apps": player.apps,
                "goals": player.season_goals,
                "assists": player.season_assists,
                "rating": round(player.rating, 2),
                "overall": round(player.overall, 1),
            }
            player.career = [
                e for e in player.career if not (e.get("season") == state.season and e.get("club") == team.name)
            ]
            player.career.append(entry)
            player.career = player.career[-30:]


def _finish_international_season(state: GameState, user_lineup_ids: list[str] | None = None) -> None:
    """Cierra una liga internacional y resuelve sus play-offs.

    NED, BEL, ENG, GER e IND usan un top-4 genérico (semifinales 1v4 y 2v3,
    final). Argentina usa el mismo formato hasta que se modele su bracket de
    seis equipos. No hay ascensos ni descensos porque no se simula la pirámide
    inferior de cada país.
    """
    table = state.table()
    champion_id = table[0].id if table else ""
    state.final4 = {"champion_id": champion_id, "format": "regular_league"}
    meta = competition(state.competition)
    if len(table) >= 4 and meta.playoffs >= 4:
        last_date = max(
            (date.fromisoformat(f.date) for f in state.fixtures if f.phase == "regular"),
            default=date.fromisoformat(state.date),
        )
        base_round = state.total_rounds + 1
        semi_date = (last_date + timedelta(days=7)).isoformat()
        final_date = (last_date + timedelta(days=8)).isoformat()
        semis = [(table[0], table[3]), (table[1], table[2])]
        results = []
        winners = []
        for i, (a, b) in enumerate(semis, 1):
            fx = Fixture(
                id=f"IP-SF{i}",
                round=base_round,
                date=semi_date,
                home_id=a.id,
                away_id=b.id,
                phase="intl_sf",
            )
            rng = random.Random(state.seed + 2600 + i)
            line, bench = (
                make_lineup(state.user_team, user_lineup_ids if user_lineup_ids is not None else (state.manual_lineup or None))
                if state.club_id in (a.id, b.id)
                else (None, None)
            )
            res = _simulate_fixture(state, fx, rng, user_lineup=line, user_bench=bench, neutral=True, knockout=True)
            state.fixtures.append(fx)
            winner = res.shootout.get("winner_id") if res.shootout else (a.id if res.home_goals > res.away_goals else b.id)
            winners.append(winner)
            results.append((fx, res, winner))
            if state.club_id in (a.id, b.id):
                state.last_result = _user_result_payload(state, fx, res, None)
        final = Fixture(
            id="IP-F",
            round=base_round + 1,
            date=final_date,
            home_id=winners[0],
            away_id=winners[1],
            phase="intl_final",
        )
        rng = random.Random(state.seed + 2700)
        line, bench = (
            make_lineup(state.user_team, user_lineup_ids if user_lineup_ids is not None else (state.manual_lineup or None))
            if state.club_id in (winners[0], winners[1])
            else (None, None)
        )
        res = _simulate_fixture(state, final, rng, user_lineup=line, user_bench=bench, neutral=True, knockout=True)
        state.fixtures.append(final)
        champion_id = res.shootout.get("winner_id") if res.shootout else (winners[0] if res.home_goals > res.away_goals else winners[1])
        if state.club_id in (winners[0], winners[1]):
            state.last_result = _user_result_payload(state, final, res, None)
        state.final4 = {
            "format": "intl_playoffs",
            "semifinals": [
                {
                    "home_id": fx.home_id,
                    "away_id": fx.away_id,
                    "home_goals": r.home_goals,
                    "away_goals": r.away_goals,
                    "shootout": r.shootout,
                    "winner_id": w,
                }
                for fx, r, w in results
            ],
            "final": {
                "home_id": final.home_id,
                "away_id": final.away_id,
                "home_goals": res.home_goals,
                "away_goals": res.away_goals,
                "shootout": res.shootout,
                "winner_id": champion_id,
            },
            "champion_id": champion_id,
        }
    state.playout = {}
    state.promoted_ids = []
    state.relegated_ids = []
    state.cup_active = False
    record_season_career(state)
    _process_age_and_retirements(state)
    state.phase = "season_end"
    state.date = f"{int(state.season[:4]) + 1}-06-30"
    _board_review(state)
    summary = season_summary(state)
    state.history.append(summary)
    state.inbox.append(
        {
            "date": state.date,
            "from": "Prensa",
            "subject": f"Fin de la temporada {state.season}",
            "body": f"Campeón de {meta.name}: {summary.get('champion') or '—'}.",
        }
    )


def _finish_regional_season(state: GameState) -> None:
    """Cierra la liga autonómica y abre la fase de ascenso.

    Si el usuario se ha clasificado, la fase nacional queda jugable: se crean
    los cuatro grupos con los resultados reales de todas las ligas y el usuario
    disputa sus partidos. Si no se clasificó, la fase se resuelve con el motor
    para que la pirámide avance igualmente.
    """
    table = state.table()
    if not table:
        state.phase = "season_end"
        return
    _create_promotion_groups(state)
    qualified = any(state.club_id in group.get("team_ids", []) for group in state.promotion.get("groups", []))
    if not qualified:
        _simulate_promotion_auto(state)
        return
    state.inbox.append(
        {
            "date": state.date,
            "from": "RFEH",
            "subject": f"Fase Nacional de ascenso a DHB · {state.season}",
            "body": (
                "Te has clasificado para la fase nacional. Cuatro grupos de cuatro equipos; "
                "los campeones disputan la liguilla final y los dos primeros ascienden. "
                "Todos los partidos son a partido único."
            ),
        }
    )


def finish_regular_season(state: GameState, user_lineup_ids: list[str] | None = None) -> None:
    meta = competition(state.competition)
    if meta.system == "regional":
        _finish_regional_season(state)
        return
    if meta.system not in ("dha", "dhb_two_phase"):
        _finish_international_season(state, user_lineup_ids)
        return
    if meta.system == "dha" and not state.cup_active and not state.cup_winner_id:
        new_cup(state)
    if state.cup_active:
        simulate_cup_remaining(state)
    if meta.system == "dha":
        play_final_four(state, user_lineup_ids)
        table = _system_table(state, "dha")
        dhb_table = _system_table(state, "dhb_two_phase")
        p = state.playout or {}
        if p.get("promoted_id"):
            # El playout lo gana un equipo DHB: sube el campeón DHB y el ganador del playout.
            promoted = [dhb_table[0].id] if dhb_table else []
            if p["promoted_id"] not in promoted:
                promoted.append(p["promoted_id"])
            for team in dhb_table:
                if len(promoted) >= 2:
                    break
                if team.id not in promoted:
                    promoted.append(team.id)
            relegated = [table[10].id, table[11].id] if len(table) >= 12 else []
        else:
            # El 11º se mantiene: solo baja el 12º y sube el campeón DHB.
            promoted = [dhb_table[0].id] if dhb_table else []
            relegated = [table[11].id] if len(table) >= 12 else []
        state.promoted_ids = list(dict.fromkeys(promoted))
        state.relegated_ids = list(dict.fromkeys(relegated))
        regional_promoted = _actual_regional_promoted(state)
        for team in regional_promoted:
            _add_regional_team(state, team)
        state.playout = dict(state.playout or {})
        state.playout["regional_promoted_ids"] = [team.id for team in regional_promoted]
        state.playout["dhb_relegated_ids"] = [team.id for team in dhb_table[-2:]]
    else:
        _simulate_dhb_final4(state, user_lineup_ids)
        table_a = _dhb_group_table(state, "A")
        table_b = _dhb_group_table(state, "B")
        state.promoted_ids = [t.id for t in table_a[:2]]
        # Los dos últimos de la segunda fase bajan a su liga autonómica.
        state.relegated_ids = [t.id for t in table_b[-2:]]
        dha_rows = _system_table(state, "dha")
        regional_promoted = _actual_regional_promoted(state)
        for team in regional_promoted:
            _add_regional_team(state, team)
        state.playout = {
            "format": "dhb_relegation",
            "promoted_ids": list(state.promoted_ids),
            "relegated_ids": list(state.relegated_ids),
            "promoted_id": state.promoted_ids[0] if state.promoted_ids else "",
            "relegated_id": state.relegated_ids[-1] if state.relegated_ids else "",
            # Los dos últimos de DHA bajan a DHB y los dos campeones
            # autonómicos suben para mantener los 16 equipos.
            "dha_relegated_ids": [team.id for team in dha_rows[-2:]],
            "regional_promoted_ids": [team.id for team in regional_promoted],
        }
    _maybe_create_ehl(state)
    if state.ehl.get("active"):
        simulate_ehl(state)
    record_season_career(state)
    _process_age_and_retirements(state)
    state.phase = "season_end"
    state.date = f"{int(state.season[:4]) + 1}-06-30"
    _board_review(state)
    state.history.append(season_summary(state))
    champ = season_summary(state).get("champion") or "—"
    state.inbox.append(
        {
            "date": state.date,
            "from": "Prensa",
            "subject": f"Fin de la temporada {state.season}",
            "body": f"Campeón: {champ}. Consulta el resumen de temporada y decide si continúas el proyecto.",
        }
    )


def season_summary(state: GameState) -> dict:
    meta = competition(state.competition)
    table = state.table() if meta.system == "dhb_two_phase" else league_table(state.teams, state.competition)
    scorers = []
    for t in state.teams.values():
        if t.league == state.competition:
            for p in t.players:
                if p.season_goals:
                    scorers.append(
                        {"player": p.name, "team": t.name, "goals": p.season_goals, "assists": p.season_assists}
                    )
    scorers.sort(key=lambda x: (-x["goals"], -x["assists"], x["player"]))
    champion_id = state.final4.get("champion_id")
    if not champion_id and table:
        champion_id = table[0].id
    promoted_names = [state.teams[i].name for i in state.promoted_ids if i in state.teams]
    relegated_names = [state.teams[i].name for i in state.relegated_ids if i in state.teams]
    return {
        "season": state.season,
        "competition": state.competition,
        "group": state.dhb_group if meta.system == "dhb_two_phase" else "A",
        "champion": state.teams[champion_id].name if champion_id in state.teams else None,
        "user_club": state.user_team.name,
        "user_position": next((i for i, t in enumerate(table, 1) if t.id == state.club_id), None),
        "table": [
            {
                "position": i,
                "team": t.name,
                "points": t.points,
                "played": t.played,
                "won": t.won,
                "drawn": t.drawn,
                "lost": t.lost,
                "gf": t.goals_for,
                "ga": t.goals_against,
                "gd": t.goals_for - t.goals_against,
            }
            for i, t in enumerate(table, 1)
        ],
        "top_scorers": scorers[:10],
        "final4": state.final4,
        "playout": state.playout,
        "promoted": promoted_names,
        "relegated": relegated_names,
        "cup_winner": state.teams[state.cup_winner_id].name if state.cup_winner_id in state.teams else None,
        "cup_third": state.teams[state.cup_third_id].name if state.cup_third_id in state.teams else None,
        "ehl_winner": state.ehl.get("winner_name", "") if state.ehl else None,
        "ehl_participants": state.ehl.get("participants", []) if state.ehl else [],
        "retirements": state.retirements,
        "board_review": state.board_review,
        "direct_relegated": state.teams[state.playout["direct_relegated_id"]].name
        if state.playout.get("direct_relegated_id") in state.teams
        else None,
    }


def _apply_pending_job(state: GameState, new_year: int) -> None:
    """Aplica un acuerdo de cambio de liga al empezar la nueva temporada."""
    pending = state.pending_job
    if not pending:
        return
    new_team = state.teams.get(str(pending.get("club_id", "")))
    if new_team is None:
        state.pending_job = {}
        return
    old_team = state.user_team
    old_club = old_team.name
    old_manager = old_team.manager_name
    old_team.manager_name = replacement_manager(old_team)
    old_team.manager_pressure = 0
    old_team.manager_since_round = state.round
    record_manager_change(
        state,
        old_team,
        old_manager,
        old_team.manager_name,
        "user_left",
        "El mánager cambia de club al inicio de la temporada.",
    )
    new_old_manager = new_team.manager_name
    state.club_id = new_team.id
    new_team.manager_name = state.manager_name
    new_team.manager_pressure = 0
    new_team.manager_since_round = state.round
    record_manager_change(
        state,
        new_team,
        new_old_manager,
        state.manager_name,
        "user_hired",
        "Nuevo mánager al frente del club.",
    )
    state.competition = new_team.league
    state.country = new_team.country or state.country
    for player in new_team.players:
        player.apps = player.season_goals = player.season_assists = 0
        player.rating_sum = 0.0
        player.fatigue = 0
        player.injury = 0
        player.suspension = 0
        player.form = 6.5
    new_team.played = new_team.won = new_team.drawn = new_team.lost = 0
    new_team.goals_for = new_team.goals_against = new_team.points = 0
    new_team.last_lineup = []
    new_team.prep_bonus = 0.0
    new_team.cohesion = 12
    if len(new_team.players) < MIN_ROSTER_SIZE:
        from .international import replacement_player

        while len(new_team.players) < MIN_ROSTER_SIZE:
            new_team.players.append(
                replacement_player(new_team, new_year, len(new_team.players) + 1)
            )
    meta = competition(state.competition)
    start = date.fromisoformat(f"{new_year}-{meta.start_date[5:]}")
    if meta.system == "dhb_two_phase":
        state.dhb_groups = {}
        setup_dhb_phase1(state, start.isoformat())
        _sync_user_league_fixtures(state)
    else:
        state.fixtures = state.league_fixtures.get(state.competition, [])
        if not state.fixtures:
            team_ids = [team.id for team in state.teams.values() if team.league == state.competition]
            state.fixtures = create_fixtures(team_ids, start.isoformat())
            state.league_fixtures[state.competition] = state.fixtures
        state.dhb_phase = 1
        state.dhb_groups = {}
        state.dhb_group = "A"
        state.cup_active = False
        state.cup_winner_id = ""
        state.cup_third_id = ""
        state.ehl = {}
        if meta.system == "dha":
            new_cup(state)
    state.round = 1
    first_regular = next((fixture.date for fixture in state.fixtures if fixture.phase == "regular"), start.isoformat())
    state.date = (date.fromisoformat(first_regular) - timedelta(days=50)).isoformat()
    years = int(pending.get("years", 2))
    state.manager_contract = {
        "club_id": new_team.id,
        "club_name": new_team.name,
        "salary": int(pending.get("salary", 0)),
        "years": years,
        "started": state.date,
        "until": f"{new_year + years}-06-30",
    }
    state.pending_job = {}
    state.manual_lineup = []
    state.weekly_plan = []
    state.training_report = {}
    state.week_trained = False
    state.last_result = {}
    state.inbox.append(
        {
            "date": state.date,
            "from": "Junta directiva",
            "subject": f"Bienvenido a {new_team.name}",
            "body": f"Has cambiado de {old_club} a {new_team.name}. Nueva temporada en {meta.short_name}.",
        }
    )
    state.inbox = state.inbox[-80:]


def advance_to_next_season(state: GameState) -> None:
    """Cierra la temporada y prepara la siguiente, con ascensos y descensos."""
    if state.phase != "season_end":
        return
    new_year = int(state.season[:4]) + 1
    archive_season(state)
    archive_season_awards(state)
    return_loans(state)
    old_system = competition(state.competition).system
    top_code = _system_code("dha")
    second_code = _system_code("dhb_two_phase")
    regional_season = old_system == "regional"
    # Movimientos de las divisiones que no ha jugado el usuario.
    if regional_season:
        for tid in state.playout.get("dhb_promoted_ids", []):
            if tid in state.teams:
                state.teams[tid].league = top_code
    if regional_season or old_system == "dhb_two_phase":
        for tid in state.playout.get("dha_relegated_ids", []):
            if tid in state.teams:
                state.teams[tid].league = second_code
    if old_system == "dha":
        for tid in state.playout.get("regional_promoted_ids", []):
            if tid in state.teams:
                state.teams[tid].league = second_code
        for tid in state.playout.get("dhb_relegated_ids", []):
            if tid in state.teams:
                state.teams[tid].league = regional_league_for(state.teams[tid], state)
    elif old_system == "dhb_two_phase":
        for tid in state.playout.get("regional_promoted_ids", []):
            if tid in state.teams:
                state.teams[tid].league = second_code
    for tid in state.promoted_ids:
        if tid not in state.teams:
            continue
        if regional_season:
            state.teams[tid].league = second_code
        elif old_system in ("dha", "dhb_two_phase"):
            # En ambas ligas los ascendidos son los dos primeros de DHB.
            state.teams[tid].league = top_code
    for tid in state.relegated_ids:
        if tid not in state.teams:
            continue
        team = state.teams[tid]
        if regional_season or old_system == "dhb_two_phase":
            # DHB -> Primera División autonómica.
            team.league = regional_league_for(team, state)
        elif old_system == "dha":
            # DHA -> DHB.
            team.league = second_code
    rng = random.Random(state.seed + new_year * 100)
    for team in state.teams.values():
        if competition(team.league).system not in ("dha", "dhb_two_phase") and team.league != state.competition:
            continue
        kept = []
        for p in team.players:
            expired = int(p.contract_until[:4]) <= new_year
            if expired:
                continue
            p.apps = p.season_goals = p.season_assists = 0
            p.rating_sum = 0.0
            p.fatigue = 0
            p.injury = 0
            p.suspension = 0
            p.form = 6.5
            kept.append(p)
        team.players = kept
        if competition(team.league).system in ("dha", "dhb_two_phase"):
            develop_youth(team, rng, new_year)
            intake(team, rng, new_year)
        while len(team.players) < MIN_ROSTER_SIZE:
            if competition(team.league).system in ("dha", "dhb_two_phase"):
                # Solo se sube al primer equipo a canteranos en edad Sub-21 o mayor.
                eligible = [p for p in team.youth if p.age >= 18]
                if eligible:
                    p = eligible[0]
                    team.youth.remove(p)
                    p.perfil = "Jugador"
                    p.team_name = team.name
                    team.players.append(p)
                    continue
                p = generate_youth(team, rng, new_year, len(team.players) + 1, age=18)
                p.perfil = "Jugador"
            else:
                from .international import replacement_player

                p = replacement_player(team, new_year, len(team.players) + 1)
            team.players.append(p)
        team.played = team.won = team.drawn = team.lost = 0
        team.goals_for = team.goals_against = team.points = 0
        team.finance_log = []
        team.prep_bonus = 0.0
        team.last_lineup = []
        team.cohesion = 12
    sync_player_leagues(state)
    state.competition = state.user_team.league
    if is_regional(state.competition):
        _ensure_regional_league(state, state.competition)
    meta = competition(state.competition)
    start = date.fromisoformat(f"{new_year}-{meta.start_date[5:]}")
    state.season = f"{new_year}-{str(new_year + 1)[-2:]}"
    state.phase = "regular"
    state.promotion = {}
    state.promotion_round = 0
    _build_world_fixtures(state, start.isoformat())
    if meta.system == "dhb_two_phase":
        state.dhb_groups = {}
        setup_dhb_phase1(state, start.isoformat())
        _sync_user_league_fixtures(state)
    else:
        state.fixtures = state.league_fixtures.get(state.competition, [])
        state.dhb_phase = 1
        state.dhb_groups = {}
        state.dhb_group = "A"
        state.cup_active = False
        state.cup_winner_id = ""
        state.cup_third_id = ""
        state.ehl = {}
    state.round = 1
    for team in state.teams.values():
        team.manager_pressure = 0
        team.manager_since_round = 0
    first_regular = next((f.date for f in state.fixtures if f.phase == "regular"), start.isoformat())
    state.date = (date.fromisoformat(first_regular) - timedelta(days=50)).isoformat()
    state.final4 = {}
    state.playout = {}
    state.last_result = {}
    state.manual_lineup = []
    state.week_trained = False
    state.weekly_plan = []
    state.training_report = {}
    state.ai_training_round = 0
    state.finance_round = 0
    state.transfer_offers = []
    state.market_offers_round = 0
    state.promoted_ids = []
    state.relegated_ids = []
    new_cup(state)
    state.inbox.append(
        {
            "date": state.date,
            "from": "Junta Directiva",
            "subject": f"Temporada {state.season} · {state.competition}",
            "body": f"Comienza una nueva temporada en {state.competition}. Revisa plantilla, contratos y mercado de verano.",
        }
    )
    _apply_pending_job(state, new_year)
