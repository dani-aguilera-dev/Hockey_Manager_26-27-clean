"""Análisis de partido con datos reales del parte y del archivo.

No inventa xG ni métricas de seguimiento: calcula eficiencia a partir de tiros,
PC, paradas, goles y posesión registrados por el motor.
"""

from __future__ import annotations

from typing import Any

from .competitions import competition
from .models import GameState


def _metrics(stats: dict[str, Any], goals: int) -> dict[str, Any]:
    shots = max(0, int(stats.get("shots", 0) or 0))
    on_target = max(0, int(stats.get("shots_on_target", 0) or 0))
    pc = max(0, int(stats.get("pc", 0) or 0))
    pc_goals = max(0, int(stats.get("pc_goals", 0) or 0))
    saves = max(0, int(stats.get("saves", 0) or 0))
    return {
        "goals": goals,
        "shots": shots,
        "shots_on_target": on_target,
        "pc": pc,
        "pc_goals": pc_goals,
        "saves": saves,
        "possession": float(stats.get("possession", 0) or 0),
        "goal_conversion": round(100 * goals / shots, 1) if shots else 0.0,
        "accuracy": round(100 * on_target / shots, 1) if shots else 0.0,
        "pc_conversion": round(100 * pc_goals / pc, 1) if pc else 0.0,
        "save_rate": round(100 * saves / max(1, on_target), 1),
        "danger_index": round(on_target * 1.5 + pc * 1.2 + goals * 2.0, 1),
    }


def _recent_matches(state: GameState, limit: int = 8) -> list[dict[str, Any]]:
    pool = list(state.fixtures)
    for fixtures in state.league_fixtures.values():
        pool.extend(fixtures)
    by_id = {fixture.id: fixture for fixture in pool}
    rows = [
        fixture
        for fixture in by_id.values()
        if fixture.played and state.club_id in (fixture.home_id, fixture.away_id)
    ]
    rows.sort(key=lambda fixture: (fixture.date, fixture.round), reverse=True)
    out = []
    for fixture in rows[:limit]:
        home = state.teams.get(fixture.home_id)
        away = state.teams.get(fixture.away_id)
        out.append(
            {
                "fixture_id": fixture.id,
                "date": fixture.date,
                "round": fixture.round,
                "phase": fixture.phase,
                "home_name": home.name if home else fixture.home_id,
                "away_name": away.name if away else fixture.away_id,
                "home_goals": fixture.home_goals,
                "away_goals": fixture.away_goals,
            }
        )
    return out


def _season_average(state: GameState) -> dict[str, Any]:
    pool = list(state.fixtures)
    for fixtures in state.league_fixtures.values():
        pool.extend(fixtures)
    by_id = {fixture.id: fixture for fixture in pool}
    rows = [
        fixture
        for fixture in by_id.values()
        if fixture.played and state.club_id in (fixture.home_id, fixture.away_id)
    ]
    if not rows:
        return {"matches": 0, "goals_for": 0.0, "goals_against": 0.0, "shots": 0.0, "shots_on_target": 0.0, "pc": 0.0, "possession": 0.0}
    goals_for = goals_against = shots = on_target = pc = possession = 0.0
    for fixture in rows:
        home = fixture.home_id == state.club_id
        goals_for += fixture.home_goals if home else fixture.away_goals
        goals_against += fixture.away_goals if home else fixture.home_goals
        stats = (fixture.home_stats if home else fixture.away_stats) or {}
        shots += float(stats.get("shots", 0) or 0)
        on_target += float(stats.get("shots_on_target", 0) or 0)
        pc += float(stats.get("pc", 0) or 0)
        possession += float(stats.get("possession", 0) or 0)
    count = len(rows)
    return {
        "matches": count,
        "goals_for": round(goals_for / count, 2),
        "goals_against": round(goals_against / count, 2),
        "shots": round(shots / count, 1),
        "shots_on_target": round(on_target / count, 1),
        "pc": round(pc / count, 1),
        "possession": round(possession / count, 1),
    }


def _player_rows(state: GameState, last: dict[str, Any]) -> list[dict[str, Any]]:
    ratings = last.get("ratings") or {}
    minutes = last.get("player_minutes") or {}
    events = last.get("events") or []
    by_name = {player.name: player for player in state.user_team.players}
    rows = []
    for name, rating in ratings.items():
        player = by_name.get(name)
        if player is None:
            continue
        goals = sum(1 for event in events if event.get("type") == "goal" and event.get("player_name") == name)
        assists = sum(1 for event in events if event.get("type") == "goal" and event.get("player_name") and name in str(event.get("text", "")) and event.get("player_name") != name)
        rows.append(
            {
                "id": player.id,
                "name": name,
                "position": player.subposition,
                "overall": round(float(player.overall), 1),
                "rating": round(float(rating), 2),
                "minutes": int(minutes.get(player.id, 0)),
                "goals": goals,
                "assists": assists,
            }
        )
    rows.sort(key=lambda row: (-row["rating"], row["name"]))
    return rows


def analysis_overview(state: GameState, fixture_id: str = "") -> dict[str, Any]:
    recent = _recent_matches(state)
    if fixture_id:
        match = next((row for row in state.match_history if row.get("fixture_id") == fixture_id), None)
        if match:
            home_stats = match.get("home_stats") or {}
            away_stats = match.get("away_stats") or {}
            return {
                "match": {
                    "fixture_id": match.get("fixture_id"),
                    "date": match.get("date"),
                    "round": match.get("round"),
                    "phase": match.get("phase"),
                    "competition": match.get("competition_name"),
                    "home_name": match.get("home_name"),
                    "away_name": match.get("away_name"),
                    "home_goals": match.get("home_goals", 0),
                    "away_goals": match.get("away_goals", 0),
                    "user_is_home": match.get("home_id") == state.club_id,
                },
                "metrics": {
                    "home": _metrics(home_stats, int(match.get("home_goals", 0))),
                    "away": _metrics(away_stats, int(match.get("away_goals", 0))),
                },
                "timeline": [],
                "players": [],
                "recent": recent,
                "season": _season_average(state),
                "source": "archive",
            }
    last = state.last_result or {}
    if not last:
        return {
            "match": None,
            "metrics": None,
            "timeline": [],
            "players": [],
            "recent": recent,
            "season": _season_average(state),
            "message": "Todavía no hay un partido del usuario para analizar.",
        }
    home_stats = last.get("home_stats") or {}
    away_stats = last.get("away_stats") or {}
    user_is_home = bool(last.get("user_is_home"))
    events = last.get("events") or []
    timeline = [
        {
            "minute": event.get("minute", 0),
            "quarter": event.get("quarter", 1),
            "type": event.get("type", ""),
            "text": event.get("text", ""),
            "team": event.get("team_name", ""),
            "player": event.get("player_name", ""),
        }
        for event in events
        if event.get("type") in (
            "goal",
            "pc",
            "stroke",
            "save",
            "card",
            "injury",
            "substitution",
            "chance",
            "review",
            "advantage",
            "dangerous_play",
            "distance_5m",
            "pc_decision",
        )
    ]
    return {
        "match": {
            "fixture_id": last.get("fixture_id"),
            "date": last.get("date"),
            "round": last.get("round"),
            "phase": last.get("phase"),
            "competition": competition(state.competition).short_name,
            "home_name": last.get("home_name"),
            "away_name": last.get("away_name"),
            "home_goals": last.get("home_goals", 0),
            "away_goals": last.get("away_goals", 0),
            "user_is_home": user_is_home,
        },
        "metrics": {
            "home": _metrics(home_stats, int(last.get("home_goals", 0))),
            "away": _metrics(away_stats, int(last.get("away_goals", 0))),
        },
        "timeline": timeline,
        "players": _player_rows(state, last),
        "recent": recent,
        "season": _season_average(state),
        "source": "last_result",
    }
