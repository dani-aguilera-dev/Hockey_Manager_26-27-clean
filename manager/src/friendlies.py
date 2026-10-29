"""Amistosos de pretemporada y parones.

Los amistosos viven separados del calendario oficial: no suman puntos, no
alteran la clasificación y no consumen jornada. Sirven para probar el once,
recuperar ritmo y generar ingresos de taquilla.
"""

from __future__ import annotations

import random
import uuid
from datetime import date, timedelta
from typing import Any

from .competitions import competition
from .models import Fixture, GameState, PlayerState


def _official_dates(state: GameState, days: int = 75) -> set[str]:
    start = date.fromisoformat(state.date)
    end = start + timedelta(days=days)
    return {
        fixture.date
        for fixture in state.fixtures
        if start <= date.fromisoformat(fixture.date) <= end
    }


def available_friendly_dates(state: GameState, days: int = 75) -> list[str]:
    """Fechas libres, ordenadas y sin partido oficial del usuario."""
    start = date.fromisoformat(state.date)
    official = _official_dates(state, days)
    booked = {fixture.date for fixture in state.friendlies if not fixture.played}
    out: list[str] = []
    for offset in range(days + 1):
        day = start + timedelta(days=offset)
        iso = day.isoformat()
        if iso in official or iso in booked:
            continue
        # Evitar el día anterior y posterior a un partido oficial.
        if (day - timedelta(days=1)).isoformat() in official or (day + timedelta(days=1)).isoformat() in official:
            continue
        out.append(iso)
    return out


def friendly_candidates(state: GameState, limit: int = 40) -> list[dict[str, Any]]:
    """Equipos disponibles para concertar un amistoso."""
    rows = []
    for team in state.teams.values():
        if team.id == state.club_id:
            continue
        meta = competition(team.league)
        rows.append(
            {
                "id": team.id,
                "name": team.name,
                "league": team.league,
                "league_name": meta.short_name,
                "country": team.country,
                "city": team.city,
                "stadium_name": team.stadium_name,
                "overall": round(
                    sum(player.overall for player in team.players) / max(1, len(team.players)),
                    1,
                ),
                "crest": team.id,
            }
        )
    rows.sort(key=lambda row: (row["country"] != state.country, -row["overall"], row["name"]))
    return rows[:limit]


def schedule_friendly(
    state: GameState,
    opponent_id: str,
    day: str,
    *,
    home: bool = True,
    notes: str = "",
) -> dict[str, Any]:
    """Concierta un amistoso y lo deja pendiente en el calendario."""
    opponent = state.teams.get(opponent_id)
    if opponent is None:
        return {"ok": False, "message": "El rival no existe."}
    if opponent.id == state.club_id:
        return {"ok": False, "message": "No puedes jugar contra tu propio equipo."}
    if day < state.date:
        return {"ok": False, "message": "No puedes programar un amistoso en el pasado."}
    if day not in available_friendly_dates(state):
        return {"ok": False, "message": "Esa fecha no está libre: hay partido oficial o ya tienes un amistoso."}
    fixture = Fixture(
        id=f"AM-{uuid.uuid4().hex[:8]}",
        round=0,
        date=day,
        home_id=state.club_id if home else opponent.id,
        away_id=opponent.id if home else state.club_id,
        phase="friendly",
    )
    fixture.travel = {
        "friendly": True,
        "notes": notes.strip(),
        "home": home,
    }
    state.friendlies.append(fixture)
    state.inbox.append(
        {
            "date": state.date,
            "from": "Secretaría técnica",
            "subject": f"Amistoso cerrado contra {opponent.name}",
            "body": (
                f"Partido {'en casa' if home else 'a domicilio'} el {day}. "
                "No cuenta para la clasificación; sirve para probar el once y dar minutos."
            ),
        }
    )
    state.inbox = state.inbox[-80:]
    return {
        "ok": True,
        "message": f"Amistoso contra {opponent.name} programado para el {day}.",
        "friendly": _friendly_payload(state, fixture),
    }


def cancel_friendly(state: GameState, friendly_id: str) -> dict[str, Any]:
    fixture = next((item for item in state.friendlies if item.id == friendly_id and not item.played), None)
    if fixture is None:
        return {"ok": False, "message": "El amistoso no existe o ya se jugó."}
    state.friendlies = [item for item in state.friendlies if item.id != friendly_id]
    return {"ok": True, "message": "Amistoso cancelado."}


def play_friendly(
    state: GameState,
    friendly_id: str,
    user_lineup_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Juega un amistoso con el motor real, sin tocar la liga."""
    fixture = next((item for item in state.friendlies if item.id == friendly_id), None)
    if fixture is None:
        return {"ok": False, "message": "El amistoso no existe."}
    if fixture.played:
        return {"ok": False, "message": "Ese amistoso ya se jugó."}
    if state.date < fixture.date:
        return {"ok": False, "message": f"El amistoso es el {fixture.date}; avanza el calendario hasta esa fecha."}
    # Importar aquí evita un ciclo de importación con season.
    from .season import _simulate_fixture, _user_result_payload, _update_user_after_match, make_lineup

    lineup, bench = make_lineup(state.user_team, user_lineup_ids or state.manual_lineup or None)
    rng = random.Random(state.seed * 9001 + date.fromisoformat(fixture.date).toordinal() + sum(ord(c) for c in fixture.id))
    old_status = {p.id: (p.injury, p.suspension) for team in state.teams.values() for p in team.players}
    result = _simulate_fixture(
        state,
        fixture,
        rng,
        user_lineup=lineup,
        user_bench=bench,
        user_travel={"option_id": "equilibrado"},
        detailed=True,
    )
    payload = _user_result_payload(state, fixture, result, fixture.travel)
    state.last_result = payload
    _update_user_after_match(state, fixture, result)
    # La taquilla del amistoso va a caja, sin pasar por la jornada oficial.
    gate = int(result.home_stats.get("gate_revenue", 0) or 0)
    if gate:
        state.teams[fixture.home_id].budget += gate
    # Recuperación ligera: un amistoso no debe dejar la plantilla como una final.
    for player in state.user_team.players:
        player.fatigue = max(0.0, min(100.0, player.fatigue - 3.0))
    state.inbox.append(
        {
            "date": state.date,
            "from": "Amistoso",
            "subject": f"{fixture.home_id} {result.home_goals}-{result.away_goals} {fixture.away_id}",
            "body": "Partido de preparación disputado. No afecta a la clasificación.",
        }
    )
    state.inbox = state.inbox[-80:]
    return {"ok": True, "message": "Amistoso disputado.", "report": payload, "friendly": _friendly_payload(state, fixture)}


def friendlies_payload(state: GameState) -> dict[str, Any]:
    return {
        "items": [_friendly_payload(state, fixture) for fixture in sorted(state.friendlies, key=lambda f: (f.date, f.id))],
        "dates": available_friendly_dates(state),
        "candidates": friendly_candidates(state),
        "played": sum(1 for fixture in state.friendlies if fixture.played),
        "pending": sum(1 for fixture in state.friendlies if not fixture.played),
    }


def _friendly_payload(state: GameState, fixture: Fixture) -> dict[str, Any]:
    home = state.teams.get(fixture.home_id)
    away = state.teams.get(fixture.away_id)
    return {
        "id": fixture.id,
        "date": fixture.date,
        "home_id": fixture.home_id,
        "away_id": fixture.away_id,
        "home_name": home.name if home else fixture.home_id,
        "away_name": away.name if away else fixture.away_id,
        "home_goals": fixture.home_goals,
        "away_goals": fixture.away_goals,
        "played": fixture.played,
        "phase": fixture.phase,
        "is_home": fixture.home_id == state.club_id,
        "notes": (fixture.travel or {}).get("notes", ""),
    }
