"""Clubes afiliados y planes de mentoría.

Los afiliados son clubes de menor o igual nivel que el usuario. Aportan
beneficios de ojeo/cantera y prioridad en cesiones. La mentoría empareja a un
veterano con un joven para acelerar su desarrollo y mejorar la relación.
"""

from __future__ import annotations

import random
import zlib
from datetime import date
from typing import Any

from .competitions import competition
from .models import GameState, PlayerState, TeamState

FOCUS_OPTIONS: dict[str, dict[str, Any]] = {
    "tecnica": {
        "label": "Técnica",
        "description": "Control, pase, conducción y golpeo.",
        "attributes": ["control", "pase", "conduccion", "golpeo"],
    },
    "mentalidad": {
        "label": "Mentalidad",
        "description": "Decisiones, concentración, competitividad y liderazgo.",
        "attributes": ["decisiones", "concentracion", "competitividad", "liderazgo"],
    },
    "fisico": {
        "label": "Físico",
        "description": "Velocidad, resistencia, fuerza y agilidad.",
        "attributes": ["velocidad", "resistencia", "fuerza", "agilidad"],
    },
    "profesionalidad": {
        "label": "Profesionalidad",
        "description": "Hábitos, relación con el grupo y lectura de partido.",
        "attributes": ["posicionamiento", "transicion", "desmarque", "concentracion"],
    },
}

AFFILIATE_BENEFITS = ("Ojeo +2", "Cantera +1", "Prioridad en cesiones")


def _standard(team: TeamState) -> float:
    return competition(team.league).standard


def _affiliate_fee(team: TeamState) -> int:
    return max(15000, int(team.wage_budget * 0.02))


def _affiliate_chance(state: GameState, candidate: TeamState, fee: int) -> float:
    user = state.user_team
    chance = 0.45 + (user.brand_rating - 50) / 200 + (user.board_confidence - 50) / 300
    chance += max(0.0, _standard(user) - _standard(candidate)) / 120
    chance -= fee / max(1, user.budget) * 0.25
    return max(0.08, min(0.90, chance))


def _affiliate_row(state: GameState, candidate: TeamState) -> dict[str, Any]:
    meta = competition(candidate.league)
    fee = _affiliate_fee(candidate)
    return {
        "id": candidate.id,
        "name": candidate.name,
        "league": candidate.league,
        "league_name": meta.short_name,
        "city": candidate.city,
        "country": candidate.country,
        "standard": round(_standard(candidate), 1),
        "academy_rating": candidate.academy_rating,
        "annual_fee": fee,
        "approval_chance": round(_affiliate_chance(state, candidate, fee), 3),
        "benefits": list(AFFILIATE_BENEFITS),
    }


def affiliate_candidates(state: GameState, limit: int = 12) -> list[dict[str, Any]]:
    user = state.user_team
    existing = {item.get("club_id") for item in state.affiliates}
    rows = []
    for team in state.teams.values():
        if team.id == user.id or team.id in existing:
            continue
        if len(team.players) < 14:
            continue
        if _standard(team) >= _standard(user) - 1:
            continue
        rows.append(_affiliate_row(state, team))
    rows.sort(key=lambda row: (row["country"] != user.country, -row["academy_rating"], -row["standard"], row["name"]))
    return rows[:limit]


def request_affiliate(state: GameState, club_id: str, rng: random.Random | None = None) -> dict[str, Any]:
    user = state.user_team
    candidate = state.teams.get(club_id)
    if candidate is None or candidate.id == user.id:
        return {"ok": False, "message": "El club no es válido."}
    if any(item.get("club_id") == candidate.id for item in state.affiliates):
        return {"ok": False, "message": "Ese club ya es afiliado."}
    if len(candidate.players) < 14:
        return {"ok": False, "message": "El club no tiene estructura suficiente para ser afiliado."}
    fee = _affiliate_fee(candidate)
    if user.budget < fee:
        return {"ok": False, "message": "No hay caja suficiente para la cuota de afiliación."}
    chance = _affiliate_chance(state, candidate, fee)
    rng = rng or random.Random(
        state.seed * 9501
        + date.fromisoformat(state.date).toordinal()
        + zlib.crc32(club_id.encode("utf-8"))
    )
    accepted = rng.random() < chance
    entry = {
        "date": state.date,
        "club_id": candidate.id,
        "club_name": candidate.name,
        "league": candidate.league,
        "league_name": competition(candidate.league).short_name,
        "annual_fee": fee,
        "accepted": accepted,
        "chance": round(chance, 3),
    }
    if not accepted:
        entry["message"] = f"{candidate.name} rechaza la afiliación por ahora."
        state.affiliate_history.append(entry)
        state.affiliate_history = state.affiliate_history[-40:]
        state.inbox.append(
            {"date": state.date, "from": "Secretaría técnica", "subject": "Afiliación rechazada", "body": entry["message"]}
        )
        return {"ok": True, "accepted": False, "message": entry["message"], "entry": entry}
    user.budget -= fee
    candidate.budget += fee
    affiliate = {
        "id": f"AF-{state.season}-{candidate.id}",
        "club_id": candidate.id,
        "club_name": candidate.name,
        "league": candidate.league,
        "league_name": competition(candidate.league).short_name,
        "city": candidate.city,
        "country": candidate.country,
        "since": state.date,
        "annual_fee": fee,
        "benefits": list(AFFILIATE_BENEFITS),
        "status": "activo",
    }
    state.affiliates.append(affiliate)
    user.facilities["scouting"] = min(99, int(user.facilities.get("scouting", 55)) + 2)
    user.facilities["youth"] = min(99, int(user.facilities.get("youth", 60)) + 1)
    user.academy_rating = min(95, user.academy_rating + 1)
    entry["message"] = f"{candidate.name} se convierte en club afiliado."
    state.affiliate_history.append(entry)
    state.affiliate_history = state.affiliate_history[-40:]
    state.inbox.append(
        {"date": state.date, "from": "Secretaría técnica", "subject": "Nuevo club afiliado", "body": entry["message"]}
    )
    return {"ok": True, "accepted": True, "message": entry["message"], "affiliate": affiliate, "entry": entry}


def end_affiliate(state: GameState, affiliate_id: str) -> dict[str, Any]:
    affiliate = next((item for item in state.affiliates if item.get("id") == affiliate_id), None)
    if affiliate is None:
        return {"ok": False, "message": "La afiliación no existe."}
    state.affiliates = [item for item in state.affiliates if item.get("id") != affiliate_id]
    entry = {**affiliate, "ended_on": state.date, "accepted": True, "message": "Afiliación finalizada."}
    state.affiliate_history.append(entry)
    state.affiliate_history = state.affiliate_history[-40:]
    return {"ok": True, "message": "Afiliación finalizada.", "entry": entry}


def affiliate_overview(state: GameState) -> dict[str, Any]:
    user = state.user_team
    return {
        "affiliates": state.affiliates,
        "candidates": affiliate_candidates(state),
        "history": list(reversed(state.affiliate_history[-15:])),
        "scouting": int(user.facilities.get("scouting", 55)),
        "youth": int(user.facilities.get("youth", 60)),
        "academy_rating": user.academy_rating,
        "benefits": list(AFFILIATE_BENEFITS),
    }


def _active_pair(team: TeamState, player_id: str, key: str) -> bool:
    return any(pair.get(key) == player_id and pair.get("status", "activo") == "activo" for pair in team.mentoring)


def _mentor_candidates(team: TeamState) -> list[dict[str, Any]]:
    rows = []
    for player in team.players:
        if player.loan or player.age < 27 or player.overall < 65:
            continue
        if _active_pair(team, player.id, "mentor_id"):
            continue
        rows.append(
            {
                "id": player.id,
                "name": player.name,
                "age": player.age,
                "overall": round(float(player.overall), 1),
                "position": player.subposition,
                "relationship": player.relationship,
            }
        )
    rows.sort(key=lambda row: (-row["overall"], -row["age"], row["name"]))
    return rows


def _mentee_candidates(team: TeamState) -> list[dict[str, Any]]:
    pool = list(team.players) + list(team.youth)
    rows = []
    for player in pool:
        if player.loan or player.age > 23:
            continue
        if _active_pair(team, player.id, "mentee_id"):
            continue
        rows.append(
            {
                "id": player.id,
                "name": player.name,
                "age": player.age,
                "overall": round(float(player.overall), 1),
                "potential": round(float(player.potential), 1),
                "position": player.subposition,
                "category": player.youth_category,
            }
        )
    rows.sort(key=lambda row: (-(row["potential"] - row["overall"]), row["age"], row["name"]))
    return rows


def _pair_payload(team: TeamState, pair: dict[str, Any]) -> dict[str, Any]:
    pool = {player.id: player for player in list(team.players) + list(team.youth)}
    mentor = pool.get(str(pair.get("mentor_id")))
    mentee = pool.get(str(pair.get("mentee_id")))
    return {
        **pair,
        "mentor_name": mentor.name if mentor else pair.get("mentor_name", ""),
        "mentee_name": mentee.name if mentee else pair.get("mentee_name", ""),
        "mentor_overall": round(float(mentor.overall), 1) if mentor else None,
        "mentee_overall": round(float(mentee.overall), 1) if mentee else None,
        "mentee_potential": round(float(mentee.potential), 1) if mentee else None,
        "focus_label": FOCUS_OPTIONS.get(str(pair.get("focus")), {}).get("label", pair.get("focus", "")),
    }


def mentoring_overview(state: GameState) -> dict[str, Any]:
    team = state.user_team
    return {
        "pairs": [_pair_payload(team, pair) for pair in team.mentoring if pair.get("status", "activo") == "activo"],
        "mentors": _mentor_candidates(team),
        "mentees": _mentee_candidates(team),
        "focus_options": [{"id": key, **value} for key, value in FOCUS_OPTIONS.items()],
        "history": list(reversed(team.mentoring_history[-10:])),
    }


def assign_mentor(state: GameState, mentor_id: str, mentee_id: str, focus: str) -> dict[str, Any]:
    team = state.user_team
    mentor = next((player for player in team.players if player.id == mentor_id), None)
    mentee = next((player for player in list(team.players) + list(team.youth) if player.id == mentee_id), None)
    if mentor is None or mentee is None or mentor.id == mentee.id:
        return {"ok": False, "message": "El mentor o el joven no son válidos."}
    if mentor.loan or mentee.loan:
        return {"ok": False, "message": "Un jugador cedido no puede participar en la mentoría."}
    if mentor.age < 27 or mentor.overall < 65:
        return {"ok": False, "message": "El mentor debe tener al menos 27 años y 65 de overall."}
    if mentee.age > 23:
        return {"ok": False, "message": "El joven debe tener 23 años o menos."}
    if focus not in FOCUS_OPTIONS:
        return {"ok": False, "message": "El plan de mentoría no es válido."}
    if _active_pair(team, mentor.id, "mentor_id"):
        return {"ok": False, "message": "Ese jugador ya es mentor de otro joven."}
    if _active_pair(team, mentee.id, "mentee_id"):
        return {"ok": False, "message": "Ese joven ya tiene un mentor."}
    pair = {
        "id": f"MT-{state.season}-{mentor.id}-{mentee.id}",
        "mentor_id": mentor.id,
        "mentor_name": mentor.name,
        "mentee_id": mentee.id,
        "mentee_name": mentee.name,
        "focus": focus,
        "since": state.date,
        "sessions": 0,
        "progress": 0,
        "status": "activo",
    }
    team.mentoring.append(pair)
    mentor.relationship = min(100, mentor.relationship + 1)
    mentee.relationship = min(100, mentee.relationship + 3)
    return {"ok": True, "message": f"{mentor.name} será el mentor de {mentee.name}.", "pair": _pair_payload(team, pair)}


def end_mentoring(state: GameState, pair_id: str) -> dict[str, Any]:
    team = state.user_team
    pair = next((item for item in team.mentoring if item.get("id") == pair_id), None)
    if pair is None:
        return {"ok": False, "message": "El plan de mentoría no existe."}
    team.mentoring = [item for item in team.mentoring if item.get("id") != pair_id]
    entry = {**pair, "status": "finalizado", "ended_on": state.date}
    team.mentoring_history.append(entry)
    team.mentoring_history = team.mentoring_history[-20:]
    return {"ok": True, "message": "Plan de mentoría finalizado.", "entry": entry}


def advance_mentoring(state: GameState) -> dict[str, Any]:
    """Avanza una semana de mentoría y aplica pequeñas mejoras al joven."""
    team = state.user_team
    pool = {player.id: player for player in list(team.players) + list(team.youth)}
    updated = []
    kept = []
    for pair in team.mentoring:
        mentor = pool.get(str(pair.get("mentor_id")))
        mentee = pool.get(str(pair.get("mentee_id")))
        if mentor is None or mentee is None or mentee.age > 23:
            entry = {**pair, "status": "finalizado", "ended_on": state.date}
            team.mentoring_history.append(entry)
            continue
        pair["sessions"] = int(pair.get("sessions", 0)) + 1
        gain = 10 + max(0.0, mentor.overall - mentee.overall) * 0.4 + (mentor.relationship - 50) * 0.1
        pair["progress"] = min(100, int(pair.get("progress", 0)) + round(gain))
        if pair["sessions"] % 4 == 0:
            attrs = FOCUS_OPTIONS[pair["focus"]]["attributes"]
            for attr in attrs[:2]:
                if attr in mentee.attributes:
                    mentee.attributes[attr] = min(99, int(mentee.attributes[attr]) + 1)
            mentee.overall = round(min(mentee.potential, mentee.overall + 0.1), 1)
            mentee.relationship = min(100, mentee.relationship + 1)
            updated.append({"mentee": mentee.name, "focus": pair["focus"], "session": pair["sessions"]})
        kept.append(pair)
    team.mentoring = kept
    return {"updated": updated, "active": len(kept)}
