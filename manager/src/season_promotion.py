"""Season promotion: fases de ascenso y Final Four."""

from __future__ import annotations

import random
from datetime import date, timedelta

from .calendar import create_fixtures, league_table
from .competitions import PROMOTION_FINAL_START, PROMOTION_GROUP_START, PROMOTION_SPOTS, competition, promotion_groups
from .models import Fixture, GameState, TeamState
from .season_sim import (
    _background_table,
    _best_dhb_team,
    _recover_after_round,
    _reset_week_training,
    _simulate_fixture,
    _simulate_fixture_fast,
    _system_table,
    _system_teams,
    _update_user_after_match,
    _user_result_payload,
    make_lineup,
)


def _dhb_groups_by_strength(state: GameState) -> dict[str, list[str]]:
    teams = sorted(
        _system_teams(state, "dhb_two_phase"),
        key=lambda t: sum(t.lineup_strength(t.auto_lineup()[0])),
        reverse=True,
    )
    groups = {"A": [], "B": []}
    for i, t in enumerate(teams):
        groups["A" if i % 2 == 0 else "B"].append(t.id)
    return groups


def _dhb_group_table(state: GameState, group: str) -> list[TeamState]:
    ids = set(state.dhb_groups.get(group, []))
    teams = [t for t in state.teams.values() if t.id in ids]
    return sorted(teams, key=lambda t: (-t.points, -(t.goals_for - t.goals_against), -t.goals_for, t.name))


def setup_dhb_phase1(state: GameState, start: str) -> None:
    groups = _dhb_groups_by_strength(state)
    state.dhb_phase = 1
    state.dhb_groups = groups
    state.dhb_group = next((g for g, ids in groups.items() if state.club_id in ids), "A")
    fixtures: list[Fixture] = []
    for g, ids in groups.items():
        for f in create_fixtures(ids, start):
            f.id = f"D{g}-{f.id}"
            fixtures.append(f)
    state.fixtures = sorted(fixtures, key=lambda f: (f.round, f.date, f.id))
    state.round = 1
    state.date = state.fixtures[0].date if state.fixtures else start


def setup_dhb_phase2(state: GameState) -> None:
    a = _dhb_group_table(state, "A")
    b = _dhb_group_table(state, "B")
    group_a = [t.id for t in a[:4]] + [t.id for t in b[:4]]
    group_b = [t.id for t in a[4:]] + [t.id for t in b[4:]]
    last_date = max(
        (date.fromisoformat(f.date) for f in state.fixtures if f.phase == "regular"),
        default=date.fromisoformat(state.date),
    )
    start = (last_date + timedelta(days=7)).isoformat()
    fixtures: list[Fixture] = []
    for g, ids in (("A", group_a), ("B", group_b)):
        for f in create_fixtures(ids, start, double=False):
            f.id = f"P{g}-{f.id}"
            f.round += 14
            fixtures.append(f)
    state.fixtures.extend(fixtures)
    state.fixtures.sort(key=lambda f: (f.round, f.date, f.id))
    state.dhb_phase = 2
    state.dhb_groups = {"A": group_a, "B": group_b}
    state.dhb_group = next((g for g, ids in state.dhb_groups.items() if state.club_id in ids), "A")


def _fast_group_rows(state: GameState, ids: list[str], start: str, double: bool, rng: random.Random) -> dict[str, dict]:
    fixtures = create_fixtures(ids, start, double=double)
    rows = {tid: {"team": state.teams[tid], "points": 0, "gf": 0, "ga": 0} for tid in ids}
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
        elif ag > hg:
            a["points"] += 3
        else:
            h["points"] += 1
            a["points"] += 1
    return rows


def _background_dhb_table(state: GameState) -> list[dict]:
    teams = _system_teams(state, "dhb_two_phase")
    if len(teams) < 8:
        return []
    groups = _dhb_groups_by_strength(state)
    rng = random.Random(state.seed + 707 + int(state.season[:4]))
    start = state.date
    rows_a = _fast_group_rows(state, groups["A"], start, True, rng)
    rows_b = _fast_group_rows(state, groups["B"], start, True, rng)

    def top(rows):
        return sorted(rows.values(), key=lambda r: (-r["points"], -(r["gf"] - r["ga"]), -r["gf"]))[:4]

    group_a = [r["team"].id for r in top(rows_a)] + [r["team"].id for r in top(rows_b)]
    phase1_points = {tid: r["points"] for tid, r in {**rows_a, **rows_b}.items()}
    phase1_gf = {tid: r["gf"] for tid, r in {**rows_a, **rows_b}.items()}
    phase1_ga = {tid: r["ga"] for tid, r in {**rows_a, **rows_b}.items()}
    last_start = (date.fromisoformat(state.fixtures[0].date) + timedelta(days=98)).isoformat()
    rows2 = _fast_group_rows(state, group_a, last_start, False, rng)
    for tid, r in rows2.items():
        r["points"] += phase1_points.get(tid, 0)
        r["gf"] += phase1_gf.get(tid, 0)
        r["ga"] += phase1_ga.get(tid, 0)
    return sorted(rows2.values(), key=lambda r: (-r["points"], -(r["gf"] - r["ga"]), -r["gf"], r["team"].name))


def _background_dhb_relegated(state: GameState) -> list[TeamState]:
    """Calcula los dos últimos de DHB cuando el usuario juega en regional.

    En una partida regional no se disputa la DHB, pero sus dos últimos deben
    bajar para que la temporada siguiente mantenga el equilibrio de la
    pirámide. Se simula la segunda fase con el mismo criterio que la DHB.
    """
    teams = _system_teams(state, "dhb_two_phase")
    if len(teams) < 16:
        return []
    groups = _dhb_groups_by_strength(state)
    rng = random.Random(state.seed + 909 + int(state.season[:4]))
    start = state.date
    rows_a = _fast_group_rows(state, groups["A"], start, True, rng)
    rows_b = _fast_group_rows(state, groups["B"], start, True, rng)

    def ordered(rows):
        return sorted(rows.values(), key=lambda r: (-r["points"], -(r["gf"] - r["ga"]), -r["gf"], r["team"].name))

    # La segunda fase de DHB la forman los cuatro peores de cada grupo inicial.
    group_b = [r["team"].id for r in ordered(rows_a)[-4:] + ordered(rows_b)[-4:]]
    phase1 = {**rows_a, **rows_b}
    rows2 = _fast_group_rows(state, group_b, start, False, rng)
    for tid, row in rows2.items():
        first = phase1.get(tid, {})
        row["points"] += first.get("points", 0)
        row["gf"] += first.get("gf", 0)
        row["ga"] += first.get("ga", 0)
    return [r["team"] for r in ordered(rows2)[-2:]]


def _fast_rows_for_teams(
    teams: list[TeamState], start: str, double: bool, rng: random.Random
) -> dict[str, dict]:
    """Versión de la liguilla rápida para equipos que aún no están en el estado."""
    if len(teams) < 2:
        return {}
    fixtures = create_fixtures([team.id for team in teams], start, double=double)
    rows = {team.id: {"team": team, "points": 0, "gf": 0, "ga": 0} for team in teams}
    for fixture in fixtures:
        home, away = rows[fixture.home_id], rows[fixture.away_id]
        home_line, _ = home["team"].auto_lineup()
        away_line, _ = away["team"].auto_lineup()
        home_attack, home_defense = home["team"].lineup_strength(home_line)
        away_attack, away_defense = away["team"].lineup_strength(away_line)
        home_goals = max(0, int(rng.gauss(2.4 + (home_attack + 4 - away_defense) / 14, 1.4)))
        away_goals = max(0, int(rng.gauss(2.2 + (away_attack - home_defense) / 14, 1.4)))
        home["gf"] += home_goals
        home["ga"] += away_goals
        away["gf"] += away_goals
        away["ga"] += home_goals
        if home_goals > away_goals:
            home["points"] += 3
        elif away_goals > home_goals:
            away["points"] += 3
        else:
            home["points"] += 1
            away["points"] += 1
    return rows


def _add_regional_team(state: GameState, team: TeamState) -> None:
    """Incorpora un equipo autonómico sin duplicar a sus jugadores en el mercado."""
    from .data_loader import norm

    if team.id in state.teams:
        return
    state.teams[team.id] = team
    names = {norm(player.name) for player in team.players}
    if names:
        state.free_agents = [player for player in state.free_agents if norm(player.name) not in names]


def _ensure_regional_league(state: GameState, code: str) -> None:
    """Carga una liga autonómica completa si el usuario baja a ella."""
    from .data_loader import norm
    from .regional import load_regional_teams

    regional, _, _ = load_regional_teams()
    added_names: set[str] = set()
    for tid, team in regional.items():
        if team.league != code or tid in state.teams:
            continue
        state.teams[tid] = team
        added_names.update(norm(player.name) for player in team.players)
    if added_names:
        state.free_agents = [player for player in state.free_agents if norm(player.name) not in added_names]


def _background_regional_promoted(state: GameState) -> list[TeamState]:
    """Dos ascensos autonómicos cuando el usuario juega en DHA o DHB.

    Se simula la fase nacional con un catálogo temporal de las ligas
    autonómicas, sin añadir 59 equipos al estado ni vaciar el mercado.
    """
    from .regional import load_regional_teams

    regional, _, _ = load_regional_teams()
    by_league: dict[str, list[TeamState]] = {}
    for team in regional.values():
        by_league.setdefault(team.league, []).append(team)
    rng = random.Random(state.seed + 1200 + int(state.season[:4]))
    winners: list[TeamState] = []
    for _, leagues in promotion_groups():
        qualifiers: list[TeamState] = []
        seen: set[str] = set()
        for code in leagues:
            teams = by_league.get(code, [])
            if len(teams) < 2:
                continue
            rows = _fast_rows_for_teams(teams, state.date, True, rng)
            for row in _promotion_rows(list(rows.values()))[: competition(code).promotion_qualifiers]:
                team = row["team"]
                if team.id not in seen:
                    seen.add(team.id)
                    qualifiers.append(team)
        if len(qualifiers) < 2:
            continue
        rows = _fast_rows_for_teams(qualifiers[:4], state.date, False, rng)
        ordered = _promotion_rows(list(rows.values()))
        if ordered:
            winners.append(ordered[0]["team"])
    if len(winners) < 2:
        return []
    rows = _fast_rows_for_teams(winners[:4], state.date, False, rng)
    return [row["team"] for row in _promotion_rows(list(rows.values()))[:PROMOTION_SPOTS]]


def _regional_qualifying_rows(state: GameState, code: str) -> list[dict]:
    """Clasificación de una liga autonómica para formar los cuatro grupos."""
    if code == state.competition:
        return [
            {
                "team": team,
                "points": team.points,
                "gf": team.goals_for,
                "ga": team.goals_against,
            }
            for team in state.table()
        ]
    return _background_table(state, code)


def _promotion_rows(rows: list[dict]) -> list[dict]:
    return sorted(
        rows,
        key=lambda row: (
            -row["points"],
            -((row["gf"]) - (row["ga"])),
            -row["gf"],
            row["team"].name,
        ),
    )


def _play_promotion_group(
    state: GameState,
    name: str,
    leagues: tuple[str, ...],
    teams: list[TeamState],
    start: str,
    phase: str,
    rng: random.Random,
) -> dict:
    """Liguilla a partido único: todos contra todos una sola vez."""
    fixtures = create_fixtures([team.id for team in teams], start, double=False)
    rows = {
        team.id: {
            "team": team,
            "points": 0,
            "gf": 0,
            "ga": 0,
            "won": 0,
            "drawn": 0,
            "lost": 0,
        }
        for team in teams
    }
    matches: list[dict] = []
    for index, fixture in enumerate(fixtures, 1):
        fixture.id = f"{phase}-{index}"
        fixture.phase = phase
        home, away = state.teams[fixture.home_id], state.teams[fixture.away_id]
        ids = state.manual_lineup or None
        line, bench = make_lineup(state.user_team, ids) if state.club_id in (home.id, away.id) else (None, None)
        result = _simulate_fixture(
            state,
            fixture,
            rng,
            user_lineup=line,
            user_bench=bench,
            neutral=True,
            knockout=False,
        )
        h, a = rows[home.id], rows[away.id]
        h["gf"] += result.home_goals
        h["ga"] += result.away_goals
        a["gf"] += result.away_goals
        a["ga"] += result.home_goals
        if result.home_goals > result.away_goals:
            h["points"] += 3
            h["won"] += 1
            a["lost"] += 1
        elif result.home_goals < result.away_goals:
            a["points"] += 3
            a["won"] += 1
            h["lost"] += 1
        else:
            h["points"] += 1
            a["points"] += 1
            h["drawn"] += 1
            a["drawn"] += 1
        if state.club_id in (home.id, away.id):
            state.last_result = _user_result_payload(state, fixture, result, None)
        state.fixtures.append(fixture)
        matches.append(
            {
                "id": fixture.id,
                "round": fixture.round,
                "date": fixture.date,
                "home_id": home.id,
                "away_id": away.id,
                "home": home.name,
                "away": away.name,
                "home_goals": result.home_goals,
                "away_goals": result.away_goals,
            }
        )
    ordered = _promotion_rows(list(rows.values()))
    table = []
    for position, row in enumerate(ordered, 1):
        table.append(
            {
                "position": position,
                "team_id": row["team"].id,
                "team": row["team"].name,
                "points": row["points"],
                "played": row["won"] + row["drawn"] + row["lost"],
                "won": row["won"],
                "drawn": row["drawn"],
                "lost": row["lost"],
                "gf": row["gf"],
                "ga": row["ga"],
                "gd": row["gf"] - row["ga"],
            }
        )
    winner_id = table[0]["team_id"] if table else ""
    return {
        "name": name,
        "leagues": list(leagues),
        "teams": [{"id": team.id, "name": team.name, "league": team.league} for team in teams],
        "table": table,
        "matches": matches,
        "winner_id": winner_id,
        "winner": state.teams[winner_id].name if winner_id in state.teams else "",
    }


def _actual_promotion_groups(state: GameState) -> list[dict]:
    """Cuatro grupos con los dos primeros reales de cada liga autonómica."""
    groups: list[dict] = []
    for group_name, leagues in promotion_groups():
        team_ids: list[str] = []
        seen: set[str] = set()
        for code in leagues:
            for team in league_table(state.teams, code)[: competition(code).promotion_qualifiers]:
                if team.id not in seen:
                    seen.add(team.id)
                    team_ids.append(team.id)
        if len(team_ids) < 4:
            for code in leagues:
                for team in league_table(state.teams, code):
                    if team.id not in seen:
                        seen.add(team.id)
                        team_ids.append(team.id)
                    if len(team_ids) >= 4:
                        break
                if len(team_ids) >= 4:
                    break
        groups.append(
            {
                "name": group_name,
                "leagues": list(leagues),
                "team_ids": team_ids[:4],
                "table": [],
                "winner_id": "",
            }
        )
    return groups


def _table_from_fixtures(state: GameState, team_ids: list[str], fixtures: list[Fixture]) -> list[dict]:
    rows = {
        tid: {"team": state.teams[tid], "points": 0, "gf": 0, "ga": 0, "won": 0, "drawn": 0, "lost": 0}
        for tid in team_ids
        if tid in state.teams
    }
    for fixture in fixtures:
        if not fixture.played or fixture.home_id not in rows or fixture.away_id not in rows:
            continue
        home, away = rows[fixture.home_id], rows[fixture.away_id]
        home["gf"] += fixture.home_goals
        home["ga"] += fixture.away_goals
        away["gf"] += fixture.away_goals
        away["ga"] += fixture.home_goals
        if fixture.home_goals > fixture.away_goals:
            home["points"] += 3
            home["won"] += 1
            away["lost"] += 1
        elif fixture.home_goals < fixture.away_goals:
            away["points"] += 3
            away["won"] += 1
            home["lost"] += 1
        else:
            home["points"] += 1
            away["points"] += 1
            home["drawn"] += 1
            away["drawn"] += 1
    ordered = sorted(
        rows.values(),
        key=lambda row: (-row["points"], -(row["gf"] - row["ga"]), -row["gf"], row["team"].name),
    )
    return [
        {
            "position": position,
            "team_id": row["team"].id,
            "team": row["team"].name,
            "points": row["points"],
            "played": row["won"] + row["drawn"] + row["lost"],
            "won": row["won"],
            "drawn": row["drawn"],
            "lost": row["lost"],
            "gf": row["gf"],
            "ga": row["ga"],
            "gd": row["gf"] - row["ga"],
        }
        for position, row in enumerate(ordered, 1)
    ]


def _actual_regional_promoted(state: GameState) -> list[TeamState]:
    """Resuelve la fase autonómica con los resultados reales ya jugados."""
    groups = _actual_promotion_groups(state)
    rng = random.Random(state.seed + 1200 + int(state.season[:4]))
    winners: list[TeamState] = []
    for group in groups:
        fixtures = create_fixtures(group["team_ids"], PROMOTION_GROUP_START, double=False)
        for index, fixture in enumerate(fixtures):
            fixture.phase = "promotion_group"
            fixture.id = f"BG-{len(winners)}-{index}"
            _simulate_fixture_fast(state, fixture, rng)
        table = _table_from_fixtures(state, group["team_ids"], fixtures)
        if table:
            winners.append(state.teams[table[0]["team_id"]])
    if len(winners) < 2:
        return []
    final_fixtures = create_fixtures([team.id for team in winners[:4]], PROMOTION_FINAL_START, double=False)
    for index, fixture in enumerate(final_fixtures):
        fixture.phase = "promotion_final"
        fixture.id = f"BF-{index}"
        _simulate_fixture_fast(state, fixture, rng)
    table = _table_from_fixtures(state, [team.id for team in winners[:4]], final_fixtures)
    return [state.teams[row["team_id"]] for row in table[:PROMOTION_SPOTS]]


def _promotion_table_rows(state: GameState, team_ids: list[str], phase: str) -> list[dict]:
    ids = set(team_ids)
    rows = {
        tid: {"team": state.teams[tid], "points": 0, "gf": 0, "ga": 0, "won": 0, "drawn": 0, "lost": 0}
        for tid in team_ids
        if tid in state.teams
    }
    fixtures = [
        fixture
        for fixture in state.league_fixtures.get("PROMOTION", [])
        if fixture.phase == phase
        and fixture.played
        and fixture.home_id in ids
        and fixture.away_id in ids
    ]
    for fixture in fixtures:
        home, away = rows[fixture.home_id], rows[fixture.away_id]
        home["gf"] += fixture.home_goals
        home["ga"] += fixture.away_goals
        away["gf"] += fixture.away_goals
        away["ga"] += fixture.home_goals
        if fixture.home_goals > fixture.away_goals:
            home["points"] += 3
            home["won"] += 1
            away["lost"] += 1
        elif fixture.home_goals < fixture.away_goals:
            away["points"] += 3
            away["won"] += 1
            home["lost"] += 1
        else:
            home["points"] += 1
            away["points"] += 1
            home["drawn"] += 1
            away["drawn"] += 1
    ordered = sorted(
        rows.values(),
        key=lambda row: (-row["points"], -(row["gf"] - row["ga"]), -row["gf"], row["team"].name),
    )
    return [
        {
            "position": position,
            "team_id": row["team"].id,
            "team": row["team"].name,
            "points": row["points"],
            "played": row["won"] + row["drawn"] + row["lost"],
            "won": row["won"],
            "drawn": row["drawn"],
            "lost": row["lost"],
            "gf": row["gf"],
            "ga": row["ga"],
            "gd": row["gf"] - row["ga"],
        }
        for position, row in enumerate(ordered, 1)
    ]


def _refresh_promotion_tables(state: GameState) -> None:
    group_fixtures = [
        fixture
        for fixture in state.league_fixtures.get("PROMOTION", [])
        if fixture.phase == "promotion_group"
    ]
    if group_fixtures:
        for group in state.promotion.get("groups", []):
            table = _promotion_table_rows(state, group.get("team_ids", []), "promotion_group")
            group["table"] = table
            group["winner_id"] = table[0]["team_id"] if table else ""
    final_group = state.promotion.get("final_group")
    if final_group:
        table = _promotion_table_rows(state, final_group.get("team_ids", []), "promotion_final")
        final_group["table"] = table
        final_group["champion_id"] = table[0]["team_id"] if table else ""
        final_group["promoted_ids"] = [row["team_id"] for row in table[:PROMOTION_SPOTS]]


def _make_promotion_fixtures(
    state: GameState, groups: list[dict], phase: str, start: str
) -> list[Fixture]:
    fixtures: list[Fixture] = []
    for group_index, group in enumerate(groups, 1):
        team_ids = group.get("team_ids", [])
        if len(team_ids) < 2:
            continue
        for fixture_index, fixture in enumerate(create_fixtures(team_ids, start, double=False), 1):
            fixture.id = f"PROM-{phase}-{group_index}-{fixture_index}"
            fixture.phase = phase
            fixtures.append(fixture)
    state.league_fixtures["PROMOTION"] = fixtures
    state.fixtures = fixtures
    return fixtures


def _create_promotion_groups(state: GameState) -> None:
    groups = _actual_promotion_groups(state)
    state.promotion = {
        "format": "regional_promotion",
        "stage": "groups",
        "groups": groups,
        "final_group": None,
        "promoted_ids": [],
        "champion_id": "",
    }
    _make_promotion_fixtures(state, groups, "promotion_group", PROMOTION_GROUP_START)
    state.phase = "promotion"
    state.promotion_round = 1
    first = next((f for f in state.fixtures if not f.played), None)
    if first:
        state.date = (date.fromisoformat(first.date) - timedelta(days=1)).isoformat()
    _refresh_promotion_tables(state)


def _simulate_promotion_fixtures(state: GameState, fixtures: list[Fixture]) -> None:
    for index, fixture in enumerate(sorted(fixtures, key=lambda f: (f.round, f.id))):
        if fixture.played:
            continue
        rng = random.Random(state.seed * 1000 + fixture.round * 37 + index)
        _simulate_fixture_fast(state, fixture, rng)


def _finish_promotion(state: GameState) -> None:
    from .season import _board_review, _process_age_and_retirements, record_season_career, season_summary
    _refresh_promotion_tables(state)
    final_group = state.promotion.get("final_group") or {}
    table = final_group.get("table", [])
    promoted_ids = [row["team_id"] for row in table[:PROMOTION_SPOTS]]
    champion_id = table[0]["team_id"] if table else ""
    dhb_table = _system_table(state, "dhb_two_phase")
    dha_table = _system_table(state, "dha")
    state.playout = {
        "format": "regional_promotion",
        "groups": state.promotion.get("groups", []),
        "semifinals": [],
        "final_group": final_group,
        "final": final_group,
        "champion_id": champion_id,
        "promoted_id": promoted_ids[0] if promoted_ids else "",
        "promoted_ids": promoted_ids,
        "dhb_promoted_ids": [team.id for team in dhb_table[:2]],
        "dha_relegated_ids": [team.id for team in dha_table[-2:]],
    }
    state.final4 = {
        "format": "regional_promotion_final_group",
        "champion_id": champion_id,
        "promoted_ids": promoted_ids,
    }
    state.promoted_ids = promoted_ids
    state.relegated_ids = [team.id for team in dhb_table[-2:]]
    state.promotion_round = 0
    record_season_career(state)
    _process_age_and_retirements(state)
    state.phase = "season_end"
    state.date = f"{int(state.season[:4]) + 1}-06-30"
    _board_review(state)
    state.history.append(season_summary(state))
    promoted_names = [state.teams[tid].name for tid in promoted_ids if tid in state.teams]
    state.inbox.append(
        {
            "date": state.date,
            "from": "Prensa",
            "subject": f"Fin de la temporada {state.season}",
            "body": (
                "Fase Nacional de ascenso a DHB: cuatro grupos y liguilla final. "
                f"Ascienden: {', '.join(promoted_names) if promoted_names else '—'}."
            ),
        }
    )


def _simulate_promotion_auto(state: GameState) -> None:
    """Resuelve la fase completa cuando el usuario no está implicado."""
    if state.phase != "promotion":
        _create_promotion_groups(state)
    _simulate_promotion_fixtures(
        state, [f for f in state.league_fixtures.get("PROMOTION", []) if f.phase == "promotion_group"]
    )
    _refresh_promotion_tables(state)
    winners = [group["winner_id"] for group in state.promotion.get("groups", []) if group.get("winner_id")]
    final_group = {
        "name": "Fase final",
        "leagues": [],
        "team_ids": winners[:4],
        "table": [],
        "winner_id": "",
    }
    state.promotion["final_group"] = final_group
    state.promotion["stage"] = "final"
    _make_promotion_fixtures(state, [final_group], "promotion_final", PROMOTION_FINAL_START)
    _simulate_promotion_fixtures(
        state, [f for f in state.league_fixtures.get("PROMOTION", []) if f.phase == "promotion_final"]
    )
    _finish_promotion(state)


def _advance_promotion_groups(state: GameState) -> None:
    _refresh_promotion_tables(state)
    winners = [group["winner_id"] for group in state.promotion.get("groups", []) if group.get("winner_id")]
    final_group = {
        "name": "Fase final",
        "leagues": [],
        "team_ids": winners[:4],
        "table": [],
        "winner_id": "",
    }
    state.promotion["final_group"] = final_group
    state.promotion["stage"] = "final"
    _make_promotion_fixtures(state, [final_group], "promotion_final", PROMOTION_FINAL_START)
    state.promotion_round = 1
    if state.club_id not in final_group["team_ids"]:
        _simulate_promotion_fixtures(
            state, [f for f in state.league_fixtures.get("PROMOTION", []) if f.phase == "promotion_final"]
        )
        _finish_promotion(state)
    else:
        first = next((f for f in state.fixtures if not f.played), None)
        if first:
            state.date = (date.fromisoformat(first.date) - timedelta(days=1)).isoformat()
        _refresh_promotion_tables(state)


def play_promotion_round(
    state: GameState, user_lineup_ids: list[str] | None = None
) -> dict | None:
    if state.phase != "promotion":
        return None
    stage = state.promotion.get("stage", "groups")
    phase = "promotion_group" if stage == "groups" else "promotion_final"
    fixtures = [
        fixture
        for fixture in state.league_fixtures.get("PROMOTION", [])
        if fixture.phase == phase and fixture.round == state.promotion_round and not fixture.played
    ]
    if not fixtures:
        return None
    old_status = {p.id: (p.injury, p.suspension) for t in state.teams.values() for p in t.players}
    effective_ids = user_lineup_ids if user_lineup_ids is not None else (state.manual_lineup or None)
    user_lineup, user_bench = make_lineup(state.user_team, effective_ids)
    user_fixture = next((f for f in fixtures if state.club_id in (f.home_id, f.away_id)), None)
    user_payload = None
    for index, fixture in enumerate(fixtures):
        is_user = state.club_id in (fixture.home_id, fixture.away_id)
        rng = random.Random(state.seed * 1000 + state.promotion_round * 37 + index + 7000)
        if is_user:
            result = _simulate_fixture(
                state,
                fixture,
                rng,
                user_lineup=user_lineup,
                user_bench=user_bench,
                neutral=True,
                knockout=False,
                detailed=True,
            )
            user_payload = _user_result_payload(state, fixture, result, None)
            state.last_result = user_payload
            _update_user_after_match(state, fixture, result)
        else:
            _simulate_fixture_fast(state, fixture, rng)
    _refresh_promotion_tables(state)
    _recover_after_round(state, old_status)
    _reset_week_training(state)
    state.promotion_round += 1
    if state.promotion_round > 3:
        if stage == "groups":
            _advance_promotion_groups(state)
        else:
            _finish_promotion(state)
    elif user_fixture:
        state.date = (date.fromisoformat(user_fixture.date) + timedelta(days=1)).isoformat()
    return user_payload


def _simulate_dhb_final4(state: GameState, user_lineup_ids: list[str] | None = None) -> str | None:
    table = _dhb_group_table(state, "A")
    if len(table) < 4:
        return None
    semis = [(table[0], table[3]), (table[1], table[2])]
    winners = []
    results = []
    for i, (a, b) in enumerate(semis, 1):
        fx = Fixture(id=f"DHB-SF{i}", round=200 + i, date="2027-04-10", home_id=a.id, away_id=b.id, phase="dhb_sf")
        rng = random.Random(state.seed + 1700 + i)
        ids = user_lineup_ids if user_lineup_ids is not None else (state.manual_lineup or None)
        line, bench = make_lineup(state.user_team, ids) if state.club_id in (a.id, b.id) else (None, None)
        res = _simulate_fixture(state, fx, rng, user_lineup=line, user_bench=bench, neutral=True, knockout=True)
        state.fixtures.append(fx)
        win = res.shootout.get("winner_id") if res.shootout else (a.id if res.home_goals > res.away_goals else b.id)
        winners.append(state.teams[win])
        results.append((fx, res, win))
    final = Fixture(
        id="DHB-F", round=204, date="2027-04-11", home_id=winners[0].id, away_id=winners[1].id, phase="dhb_final"
    )
    rng = random.Random(state.seed + 1800)
    ids = user_lineup_ids if user_lineup_ids is not None else (state.manual_lineup or None)
    line, bench = make_lineup(state.user_team, ids) if state.club_id in (winners[0].id, winners[1].id) else (None, None)
    res = _simulate_fixture(state, final, rng, user_lineup=line, user_bench=bench, neutral=True, knockout=True)
    state.fixtures.append(final)
    champion = (
        res.shootout.get("winner_id")
        if res.shootout
        else (winners[0].id if res.home_goals > res.away_goals else winners[1].id)
    )
    state.final4 = {
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
            "winner_id": champion,
        },
        "champion_id": champion,
    }
    return champion


def play_final_four(state: GameState, user_lineup_ids: list[str] | None = None) -> dict:
    """Simula semifinales, final y playout de DHA."""
    table = _system_table(state, "dha")
    if len(table) < 12:
        return {}
    semis = [(table[0], table[3]), (table[1], table[2])]
    results = []
    winners = []
    for i, (a, b) in enumerate(semis, 1):
        fx = Fixture(id=f"SF{i}", round=23, date="2027-04-10", home_id=a.id, away_id=b.id, phase="final4_sf")
        rng = random.Random(state.seed + 800 + i)
        ids = user_lineup_ids if user_lineup_ids is not None else (state.manual_lineup or None)
        line, bench = make_lineup(state.user_team, ids) if state.club_id in (a.id, b.id) else (None, None)
        res = _simulate_fixture(state, fx, rng, user_lineup=line, user_bench=bench, neutral=True, knockout=True)
        state.fixtures.append(fx)
        winner_id = (
            res.shootout.get("winner_id") if res.shootout else (a.id if res.home_goals > res.away_goals else b.id)
        )
        winners.append(state.teams[winner_id])
        results.append({"fixture": fx, "result": res, "winner_id": winner_id})
        if state.club_id in (a.id, b.id):
            state.last_result = _user_result_payload(state, fx, res, None)
    final = Fixture(
        id="F1", round=24, date="2027-04-11", home_id=winners[0].id, away_id=winners[1].id, phase="final4_final"
    )
    rng = random.Random(state.seed + 900)
    ids = user_lineup_ids if user_lineup_ids is not None else (state.manual_lineup or None)
    line, bench = make_lineup(state.user_team, ids) if state.club_id in (winners[0].id, winners[1].id) else (None, None)
    res = _simulate_fixture(state, final, rng, user_lineup=line, user_bench=bench, neutral=True, knockout=True)
    state.fixtures.append(final)
    champion_id = (
        res.shootout.get("winner_id")
        if res.shootout
        else (winners[0].id if res.home_goals > res.away_goals else winners[1].id)
    )
    state.final4 = {
        "semifinals": [
            {
                "home_id": r["fixture"].home_id,
                "away_id": r["fixture"].away_id,
                "home_goals": r["result"].home_goals,
                "away_goals": r["result"].away_goals,
                "shootout": r["result"].shootout,
                "winner_id": r["winner_id"],
            }
            for r in results
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
    if state.club_id in (final.home_id, final.away_id):
        state.last_result = _user_result_payload(state, final, res, None)
    eleventh = table[10]
    dhb = _best_dhb_team(state)
    playout = {}
    if dhb:
        fx = Fixture(id="PO1", round=25, date="2027-04-17", home_id=eleventh.id, away_id=dhb.id, phase="playout")
        rng = random.Random(state.seed + 1000)
        ids = user_lineup_ids if user_lineup_ids is not None else (state.manual_lineup or None)
        line, bench = make_lineup(state.user_team, ids) if state.club_id in (eleventh.id, dhb.id) else (None, None)
        res = _simulate_fixture(state, fx, rng, user_lineup=line, user_bench=bench, neutral=True, knockout=True)
        state.fixtures.append(fx)
        winner_id = (
            res.shootout.get("winner_id")
            if res.shootout
            else (eleventh.id if res.home_goals > res.away_goals else dhb.id)
        )
        stays_id = eleventh.id if winner_id == eleventh.id else None
        promoted_id = None if stays_id else dhb.id
        relegated_id = None if stays_id else eleventh.id
        playout = {
            "home_id": eleventh.id,
            "away_id": dhb.id,
            "home_goals": res.home_goals,
            "away_goals": res.away_goals,
            "shootout": res.shootout,
            "winner_id": winner_id,
            "stays_id": stays_id,
            "promoted_id": promoted_id,
            "relegated_id": relegated_id,
            "direct_relegated_id": table[11].id,
            "note": "El representante DHB se elige por potencial de plantilla (modelo).",
        }
        if state.club_id in (eleventh.id, dhb.id):
            state.last_result = _user_result_payload(state, fx, res, None)
    state.playout = playout
    return state.final4
