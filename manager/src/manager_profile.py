"""Perfil y carrera del mánager.

La carrera se calcula con los partidos y resúmenes de temporada ya persistidos:
no duplica estado ni inventa votos. Incluye récord, palmarés, hitos, forma
reciente y situación actual en el club.
"""

from __future__ import annotations

from typing import Any

from .competitions import competition
from .models import GameState


def _competition_label(code: str) -> str:
    try:
        return competition(code).short_name
    except Exception:
        return code


def _current_fixture_rows(state: GameState) -> list[dict[str, Any]]:
    pool = list(state.fixtures)
    for fixtures in state.league_fixtures.values():
        pool.extend(fixtures)
    by_id = {fixture.id: fixture for fixture in pool}
    rows = []
    for fixture in by_id.values():
        if not fixture.played or state.club_id not in (fixture.home_id, fixture.away_id):
            continue
        home = state.teams.get(fixture.home_id)
        away = state.teams.get(fixture.away_id)
        rows.append(
            {
                "season": state.season,
                "fixture_id": fixture.id,
                "date": fixture.date,
                "competition": fixture.phase or "regular",
                "competition_name": _competition_label(state.competition),
                "home_id": fixture.home_id,
                "away_id": fixture.away_id,
                "home_name": home.name if home else fixture.home_id,
                "away_name": away.name if away else fixture.away_id,
                "home_goals": fixture.home_goals,
                "away_goals": fixture.away_goals,
            }
        )
    return rows


def _all_matches(state: GameState) -> list[dict[str, Any]]:
    rows = list(state.match_history) + _current_fixture_rows(state)
    deduped: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = (str(row.get("season", "")), str(row.get("fixture_id", "")))
        deduped[key] = row
    return sorted(
        deduped.values(),
        key=lambda row: (str(row.get("date", "")), int(row.get("round", 0) or 0), str(row.get("fixture_id", ""))),
    )


def _result(state: GameState, match: dict[str, Any]) -> tuple[int, int, str]:
    home = match.get("home_id") == state.club_id
    gf = int(match.get("home_goals", 0) or 0) if home else int(match.get("away_goals", 0) or 0)
    ga = int(match.get("away_goals", 0) or 0) if home else int(match.get("home_goals", 0) or 0)
    return gf, ga, ("V" if gf > ga else ("E" if gf == ga else "D"))


def _position(state: GameState) -> int:
    table = state.table()
    return next((index for index, team in enumerate(table, 1) if team.id == state.club_id), 0)


def _reputation(rating: int) -> str:
    if rating >= 80:
        return "Mundial"
    if rating >= 70:
        return "Continental"
    if rating >= 60:
        return "Nacional"
    if rating >= 50:
        return "Profesional"
    return "Emergente"


def _season_rows(state: GameState) -> list[dict[str, Any]]:
    rows = []
    for summary in state.history:
        user_row = next(
            (row for row in summary.get("table", []) if row.get("team") == summary.get("user_club")),
            None,
        )
        trophies = []
        if summary.get("champion") == summary.get("user_club"):
            trophies.append("Liga")
        if summary.get("cup_winner") == summary.get("user_club"):
            trophies.append("Copa")
        if summary.get("ehl_winner") == summary.get("user_club"):
            trophies.append("EHL")
        if summary.get("user_club") in (summary.get("promoted") or []):
            trophies.append("Ascenso")
        rows.append(
            {
                "season": summary.get("season", ""),
                "competition": summary.get("competition", ""),
                "position": summary.get("user_position"),
                "points": user_row.get("points") if user_row else None,
                "champion": summary.get("champion"),
                "cup_winner": summary.get("cup_winner"),
                "ehl_winner": summary.get("ehl_winner"),
                "promoted": summary.get("promoted", []),
                "relegated": summary.get("relegated", []),
                "trophies": trophies,
                "in_progress": False,
            }
        )
    table = state.table()
    user_row = next((row for row in table if row.id == state.club_id), None)
    rows.append(
        {
            "season": state.season,
            "competition": state.competition,
            "position": _position(state),
            "points": user_row.points if user_row else 0,
            "champion": None,
            "cup_winner": state.cup_winner_id or None,
            "ehl_winner": (state.ehl or {}).get("winner") or None,
            "promoted": [],
            "relegated": [],
            "trophies": [],
            "in_progress": True,
        }
    )
    rows.sort(key=lambda row: (row["season"], row["in_progress"]))
    return rows


def _trophies(state: GameState) -> dict[str, Any]:
    league = cup = ehl = promotions = 0
    details = []
    club_name = state.user_team.name
    for summary in state.history:
        if summary.get("champion") == club_name:
            league += 1
            details.append({"season": summary.get("season"), "title": "Liga", "competition": summary.get("competition")})
        if summary.get("cup_winner") == club_name:
            cup += 1
            details.append({"season": summary.get("season"), "title": "Copa", "competition": "Copa"})
        if summary.get("ehl_winner") == club_name:
            ehl += 1
            details.append({"season": summary.get("season"), "title": "EHL", "competition": "EHL"})
        if club_name in (summary.get("promoted") or []):
            promotions += 1
            details.append({"season": summary.get("season"), "title": "Ascenso", "competition": summary.get("competition")})
    return {
        "total": league + cup + ehl + promotions,
        "league": league,
        "cup": cup,
        "ehl": ehl,
        "promotions": promotions,
        "details": details,
    }


def _record(state: GameState, matches: list[dict[str, Any]]) -> dict[str, Any]:
    wins = draws = losses = goals_for = goals_against = 0
    for match in matches:
        gf, ga, result = _result(state, match)
        goals_for += gf
        goals_against += ga
        if result == "V":
            wins += 1
        elif result == "E":
            draws += 1
        else:
            losses += 1
    played = len(matches)
    seasons = [row for row in _season_rows(state) if not row["in_progress"]]
    finishes = [row["position"] for row in seasons if row.get("position")]
    points = [row["points"] for row in seasons if row.get("points") is not None]
    return {
        "matches": played,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "goals_for": goals_for,
        "goals_against": goals_against,
        "goal_difference": goals_for - goals_against,
        "win_rate": round(100 * wins / played, 1) if played else 0.0,
        "points_per_match": round((3 * wins + draws) / played, 2) if played else 0.0,
        "best_finish": min(finishes) if finishes else None,
        "best_points": max(points) if points else None,
    }


def _milestones(state: GameState, record: dict[str, Any], trophies: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        ("first_match", "Primer partido", "Dirige tu primer partido oficial.", record["matches"], 1),
        ("first_win", "Primera victoria", "Gana tu primer partido.", record["wins"], 1),
        ("matches_25", "25 partidos", "Alcanza 25 partidos dirigidos.", record["matches"], 25),
        ("matches_50", "50 partidos", "Alcanza 50 partidos dirigidos.", record["matches"], 50),
        ("goals_50", "50 goles", "Tu equipo marca 50 goles.", record["goals_for"], 50),
        ("goals_100", "100 goles", "Tu equipo marca 100 goles.", record["goals_for"], 100),
        ("first_title", "Primer título", "Gana una competición.", trophies["total"], 1),
        ("promotion", "Ascenso", "Consigue un ascenso.", trophies["promotions"], 1),
    ]
    return [
        {
            "id": key,
            "label": label,
            "description": description,
            "value": int(value),
            "target": int(target),
            "achieved": int(value) >= int(target),
            "progress": round(100 * min(1.0, int(value) / max(1, int(target))), 1),
        }
        for key, label, description, value, target in rows
    ]


def manager_profile_overview(state: GameState) -> dict[str, Any]:
    team = state.user_team
    matches = _all_matches(state)
    record = _record(state, matches)
    trophies = _trophies(state)
    seasons = _season_rows(state)
    recent = []
    for match in matches[-5:]:
        gf, ga, result = _result(state, match)
        recent.append(
            {
                "date": match.get("date"),
                "competition": match.get("competition_name") or match.get("competition"),
                "opponent": match.get("away_name") if match.get("home_id") == state.club_id else match.get("home_name"),
                "goals_for": gf,
                "goals_against": ga,
                "result": result,
            }
        )
    return {
        "manager": {
            "name": state.manager_name,
            "club": team.name,
            "club_id": team.id,
            "season": state.season,
            "competition": competition(state.competition).short_name,
            "rating": team.manager_rating,
            "reputation": _reputation(team.manager_rating),
            "formation": team.tactics.formation,
        },
        "current": {
            "position": _position(state),
            "phase": state.phase,
            "board_confidence": team.board_confidence,
            "fan_confidence": team.fan_confidence,
            "manager_rating": team.manager_rating,
            "budget": int(team.budget),
            "transfer_budget": int(team.transfer_budget),
        },
        "record": record,
        "trophies": trophies,
        "seasons": list(reversed(seasons)),
        "milestones": _milestones(state, record, trophies),
        "recent": list(reversed(recent)),
    }
