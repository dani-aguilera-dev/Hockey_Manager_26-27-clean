"""Historial consultable: temporadas, competiciones, partidos, jugadores y récords.

El historial se construye con los resúmenes de temporada, un archivo compacto
de partidos y las fichas de rendimiento de los jugadores. Los datos se guardan
en la partida, de modo que sobreviven a la carga y al cambio de temporada.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .competitions import competition
from .models import Fixture, GameState


def _competition_for(state: GameState, fixture: Fixture) -> tuple[str, str]:
    phase = str(fixture.phase or "regular")
    if phase.startswith("cup"):
        return "CUP", "Copa del Rey"
    if phase.startswith("ehl"):
        return "EHL", "EHL"
    if phase.startswith("promotion"):
        return "PROMOTION", "Fase de ascenso"
    if phase.startswith("intl"):
        code = state.teams[fixture.home_id].league if fixture.home_id in state.teams else state.competition
    else:
        home = state.teams.get(fixture.home_id)
        away = state.teams.get(fixture.away_id)
        code = home.league if home and away and home.league == away.league else state.competition
    try:
        meta = competition(code)
        return code, meta.short_name
    except Exception:
        return code, code


def _match_record(state: GameState, fixture: Fixture, season: str) -> dict[str, Any]:
    home = state.teams.get(fixture.home_id)
    away = state.teams.get(fixture.away_id)
    code, label = _competition_for(state, fixture)
    scorers = [
        {"player": event.get("player_name"), "team": event.get("team_name")}
        for event in fixture.events
        if event.get("type") == "goal"
    ]
    return {
        "season": season,
        "fixture_id": fixture.id,
        "date": fixture.date,
        "phase": fixture.phase,
        "round": fixture.round,
        "competition": code,
        "competition_name": label,
        "home_id": fixture.home_id,
        "home_name": home.name if home else fixture.home_id,
        "away_id": fixture.away_id,
        "away_name": away.name if away else fixture.away_id,
        "home_goals": fixture.home_goals,
        "away_goals": fixture.away_goals,
        "attendance": fixture.attendance,
        "home_stats": fixture.home_stats,
        "away_stats": fixture.away_stats,
        "scorers": scorers,
    }


def _all_fixtures(state: GameState) -> list[Fixture]:
    pool = list(state.fixtures)
    for fixtures in state.league_fixtures.values():
        pool.extend(fixtures)
    by_id = {fixture.id: fixture for fixture in pool}
    return sorted(by_id.values(), key=lambda fixture: (fixture.date, fixture.round, fixture.id))


def archive_season_matches(state: GameState) -> int:
    """Guarda los partidos jugados de la temporada actual en el archivo."""
    existing = {(item.get("season"), item.get("fixture_id")) for item in state.match_history}
    added = 0
    for fixture in _all_fixtures(state):
        if not fixture.played:
            continue
        key = (state.season, fixture.id)
        if key in existing:
            continue
        state.match_history.append(_match_record(state, fixture, state.season))
        existing.add(key)
        added += 1
    return added


def archive_season_players(state: GameState) -> int:
    """Guarda una foto de rendimiento de cada jugador con minutos o goles."""
    existing = {(item.get("season"), item.get("player_id")) for item in state.player_history}
    added = 0
    for team in state.teams.values():
        for player in team.players:
            if not (player.apps or player.season_goals or player.season_assists):
                continue
            key = (state.season, player.id)
            if key in existing:
                continue
            state.player_history.append(
                {
                    "season": state.season,
                    "player_id": player.id,
                    "name": player.name,
                    "team_id": team.id,
                    "team": team.name,
                    "league": team.league,
                    "position": player.subposition,
                    "age": player.age,
                    "apps": player.apps,
                    "goals": player.season_goals,
                    "assists": player.season_assists,
                    "rating": round(float(player.rating), 2),
                    "overall": round(float(player.overall), 1),
                }
            )
            existing.add(key)
            added += 1
    return added


def archive_season(state: GameState) -> dict[str, int]:
    return {"matches": archive_season_matches(state), "players": archive_season_players(state)}


def _current_match_records(state: GameState) -> list[dict[str, Any]]:
    existing = {(item.get("season"), item.get("fixture_id")) for item in state.match_history}
    rows = []
    for fixture in _all_fixtures(state):
        if not fixture.played or (state.season, fixture.id) in existing:
            continue
        rows.append(_match_record(state, fixture, state.season))
    return rows


def _player_rows(state: GameState) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}

    def add(entry: dict[str, Any]) -> None:
        key = str(entry.get("player_id") or entry.get("name") or "")
        if not key:
            return
        row = rows.setdefault(
            key,
            {
                "player_id": key,
                "name": entry.get("name", ""),
                "seasons": set(),
                "teams": set(),
                "apps": 0,
                "goals": 0,
                "assists": 0,
                "ratings": [],
                "overall": 0.0,
                "position": entry.get("position", ""),
            },
        )
        if entry.get("season"):
            row["seasons"].add(str(entry["season"]))
        if entry.get("team"):
            row["teams"].add(str(entry["team"]))
        row["apps"] += int(entry.get("apps", 0) or 0)
        row["goals"] += int(entry.get("goals", 0) or 0)
        row["assists"] += int(entry.get("assists", 0) or 0)
        if entry.get("rating"):
            row["ratings"].append(float(entry["rating"]))
        row["overall"] = max(row["overall"], float(entry.get("overall", 0) or 0))
        row["position"] = row["position"] or entry.get("position", "")

    for entry in state.player_history:
        add(entry)
    archived = {(item.get("season"), item.get("player_id")) for item in state.player_history}
    for team in state.teams.values():
        for player in team.players:
            if (state.season, player.id) in archived:
                continue
            if player.apps or player.season_goals or player.season_assists:
                add(
                    {
                        "season": state.season,
                        "player_id": player.id,
                        "name": player.name,
                        "team": team.name,
                        "team_id": team.id,
                        "position": player.subposition,
                        "apps": player.apps,
                        "goals": player.season_goals,
                        "assists": player.season_assists,
                        "rating": round(float(player.rating), 2),
                        "overall": round(float(player.overall), 1),
                    }
                )
            # Respaldo para partidas antiguas sin archivo de jugadores.
            if not state.player_history:
                for career in player.career:
                    add({**career, "player_id": player.id, "name": player.name, "team": career.get("club", "")})
    result = []
    for row in rows.values():
        ratings = row.pop("ratings")
        row["seasons"] = sorted(row["seasons"])
        row["teams"] = sorted(row["teams"])
        row["rating"] = round(sum(ratings) / len(ratings), 2) if ratings else 0.0
        result.append(row)
    result.sort(key=lambda item: (-item["goals"], -item["assists"], -item["apps"], item["name"]))
    return result


def _competition_rows(state: GameState) -> list[dict[str, Any]]:
    rows = []
    for summary in state.history:
        user_row = next(
            (row for row in summary.get("table", []) if row.get("team") == summary.get("user_club")),
            None,
        )
        rows.append(
            {
                "season": summary.get("season", ""),
                "competition": summary.get("competition", ""),
                "user_club": summary.get("user_club", ""),
                "user_position": summary.get("user_position"),
                "points": user_row.get("points") if user_row else None,
                "champion": summary.get("champion"),
                "cup_winner": summary.get("cup_winner"),
                "ehl_winner": summary.get("ehl_winner"),
                "promoted": summary.get("promoted", []),
                "relegated": summary.get("relegated", []),
            }
        )
    return rows


def _records(state: GameState, players: list[dict[str, Any]], matches: list[dict[str, Any]], competitions: list[dict[str, Any]]) -> dict[str, Any]:
    top_scorer = players[0] if players else None
    most_apps = max(players, key=lambda item: item["apps"], default=None)
    rated = [item for item in players if item["apps"] >= 10 and item["rating"]]
    best_rating = max(rated, key=lambda item: item["rating"], default=None)
    biggest = max(
        matches,
        key=lambda item: abs(int(item["home_goals"]) - int(item["away_goals"])),
        default=None,
    )
    title_counts: dict[str, int] = defaultdict(int)
    for row in competitions:
        for key in ("champion", "cup_winner", "ehl_winner"):
            name = row.get(key)
            if name:
                title_counts[name] += 1
    best_points = None
    for summary in state.history:
        for row in summary.get("table", []):
            if best_points is None or int(row.get("points", 0)) > int(best_points.get("points", 0)):
                best_points = {**row, "season": summary.get("season"), "competition": summary.get("competition")}
    user_finishes = [row["user_position"] for row in competitions if row.get("user_position")]
    return {
        "top_scorer": top_scorer,
        "most_apps": most_apps,
        "best_rating": best_rating,
        "biggest_win": biggest,
        "most_titles": [
            {"team": team, "titles": count}
            for team, count in sorted(title_counts.items(), key=lambda item: (-item[1], item[0]))[:8]
        ],
        "best_points": best_points,
        "best_user_finish": min(user_finishes) if user_finishes else None,
    }


def history_overview(
    state: GameState,
    season: str = "",
    competition_code: str = "",
    team_id: str = "",
    player_query: str = "",
    limit: int = 200,
) -> dict[str, Any]:
    seasons = [row for row in state.history if not season or row.get("season") == season]
    if competition_code:
        seasons = [row for row in seasons if row.get("competition") == competition_code]
    matches = list(state.match_history) + _current_match_records(state)
    if season:
        matches = [row for row in matches if row.get("season") == season]
    if competition_code:
        matches = [row for row in matches if row.get("competition") == competition_code]
    if team_id:
        matches = [row for row in matches if team_id in (row.get("home_id"), row.get("away_id"))]
    matches.sort(key=lambda row: (row.get("date", ""), row.get("round", 0), row.get("fixture_id", "")))
    matches = list(reversed(matches))[:limit]
    players = _player_rows(state)
    if season:
        players = [
            row
            for row in players
            if season in row.get("seasons", [])
        ]
    if team_id:
        team_name = state.teams.get(team_id).name if team_id in state.teams else ""
        players = [row for row in players if team_name in row.get("teams", [])]
    if player_query:
        needle = player_query.lower()
        players = [row for row in players if needle in row.get("name", "").lower()]
    competitions = _competition_rows(state)
    if season:
        competitions = [row for row in competitions if row.get("season") == season]
    if competition_code:
        competitions = [row for row in competitions if row.get("competition") == competition_code]
    all_players = _player_rows(state)
    all_matches = list(state.match_history) + _current_match_records(state)
    all_competitions = _competition_rows(state)
    records = _records(state, all_players, all_matches, all_competitions)
    user_titles = sum(
        1 for row in all_competitions if row.get("champion") == state.user_team.name
    )
    season_options = sorted({state.season} | {row.get("season", "") for row in state.history}, reverse=True)
    competition_codes = {row.get("competition") for row in all_competitions}
    competition_codes.add(state.competition)
    competition_options = []
    for code in sorted(competition_codes):
        if not code:
            continue
        try:
            meta = competition(code)
            competition_options.append({"code": code, "name": meta.short_name})
        except Exception:
            competition_options.append({"code": code, "name": code})
    team_options = sorted(
        ({"id": team.id, "name": team.name} for team in state.teams.values()),
        key=lambda item: item["name"],
    )
    return {
        "seasons": list(reversed(seasons)),
        "competitions": list(reversed(competitions)),
        "matches": matches,
        "players": players[:limit],
        "records": records,
        "summary": {
            "seasons": len(state.history),
            "matches": len(all_matches),
            "players": len(all_players),
            "user_titles": user_titles,
            "current_season": state.season,
            "current_competition": competition(state.competition).short_name,
        },
        "filters": {
            "season": season,
            "competition": competition_code,
            "team_id": team_id,
            "player_query": player_query,
        },
        "options": {
            "seasons": season_options,
            "competitions": competition_options,
            "teams": team_options,
        },
    }
