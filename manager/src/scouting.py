"""Red de ojeadores y recomendaciones de fichaje.

El ojeador no sustituye al mercado: prioriza objetivos que encajan con el
presupuesto, el nivel del equipo y sus carencias. La confianza depende del
rating del ojeador contratado.
"""

from __future__ import annotations

import zlib
from typing import Any

from .competitions import competition
from .market import asking_price, market_players, scout_range
from .models import GameState, PlayerState, TeamState
from .responsibilities import responsibility_bonus

FOCUS_LABELS = {
    "equilibrado": "Equilibrado",
    "necesidad": "Cubrir carencias",
    "joven": "Jóvenes con proyección",
    "rendimiento": "Rendimiento inmediato",
    "ganga": "Oportunidades de mercado",
    "calidad": "Salto de calidad",
}


def _team_quality(team: TeamState) -> tuple[float, float]:
    lineup, _ = team.auto_lineup()
    pool = lineup or team.players
    if not pool:
        return 50.0, 25.0
    return sum(p.overall for p in pool) / len(pool), sum(p.age for p in pool) / len(pool)


def _needs(team: TeamState) -> list[dict[str, Any]]:
    thresholds = {"Portero": 2, "Defensa": 6, "Medio": 6, "Delantero": 5}
    needs = []
    for group, target in thresholds.items():
        members = [p for p in team.players if p.position_group == group]
        quality = sum(p.overall for p in members) / max(1, len(members))
        gap = max(0, target - len(members))
        needs.append(
            {
                "group": group,
                "count": len(members),
                "target": target,
                "gap": gap,
                "quality": round(quality, 1),
                "label": f"{group} ({len(members)}/{target})",
            }
        )
    return needs


def scout_context(state: GameState) -> dict[str, Any]:
    team = state.user_team
    scout = next((m for m in team.staff if m.role == "scout"), None)
    quality, average_age = _team_quality(team)
    rating = scout.rating if scout else 55
    rating = min(99, int(rating + responsibility_bonus(team, "scouting") * 10))
    return {
        "scout": {
            "name": scout.name if scout else "Red de ojeadores del club",
            "rating": rating,
            "confidence": "alta" if rating >= 75 else ("media" if rating >= 60 else "baja"),
            "range": scout_range(
                PlayerState(
                    id="scout-reference",
                    name="Referencia",
                    team_name=team.name,
                    position_group="Medio",
                    subposition="Medio",
                    age=25,
                    overall=quality,
                    potential=quality,
                    attributes={},
                    archetype="Referencia",
                    perfil="Jugador",
                    goals_isquad=0,
                    league=team.league,
                ),
                rating,
            ),
        },
        "team_quality": round(quality, 1),
        "average_age": round(average_age, 1),
        "transfer_budget": team.transfer_budget,
        "wage_budget": team.wage_budget,
        "needs": _needs(team),
        "focuses": [{"id": key, "label": value} for key, value in FOCUS_LABELS.items()],
    }


def _fit_score(
    player: PlayerState,
    team: TeamState,
    quality: float,
    needs: list[dict[str, Any]],
    asking: int,
    focus: str,
) -> tuple[float, list[str]]:
    reasons: list[str] = []
    budget = max(1, team.transfer_budget)
    quality_gap = player.overall - quality
    potential_gap = player.potential - quality
    age = player.age
    need = next((row for row in needs if row["group"] == player.position_group), None)
    need_bonus = 0.0
    if need and need["gap"] > 0:
        need_bonus += 8 + need["gap"] * 3
        reasons.append(f"Cubre la falta de {player.position_group.lower()}")
    if quality_gap >= 3:
        reasons.append("Sube el nivel del once")
    elif potential_gap >= 5 and age <= 23:
        reasons.append("Tiene margen de crecimiento")
    if asking <= budget * 0.55:
        reasons.append("Precio cómodo para tu presupuesto")
    elif asking <= budget:
        reasons.append("Entra en presupuesto")
    if player.rating >= 7.0 and player.apps >= 3:
        reasons.append("Rendimiento reciente alto")
    if age <= 22:
        reasons.append("Perfil joven")
    if age >= 30:
        reasons.append("Experiencia inmediata")
    if player.salary <= max(18000, team.wage_budget / 24):
        reasons.append("Salario asumible")
    if player.transfer_listed:
        reasons.append("Está en el escaparate")
    score = 48 + quality_gap * 2.2 + max(0, potential_gap) * 0.7 + need_bonus
    score += max(0, 12 - age) * 0.8
    score += max(0, 8 - (asking / budget) * 5)
    score += min(6, player.rating * 0.7) if player.apps else 0
    if focus == "necesidad":
        score += need_bonus * 1.3
    elif focus == "joven":
        score += max(0, 26 - age) * 1.4 + max(0, potential_gap) * 0.8
    elif focus == "rendimiento":
        score += (player.rating - 6.0) * 9 + player.apps * 0.15
    elif focus == "ganga":
        score += max(0, (1 - asking / budget) * 12) + max(0, 8 - player.salary / 12000)
    elif focus == "calidad":
        score += max(0, quality_gap) * 3.2
    if player.overall < quality - 8 and player.potential < quality + 2:
        score -= 24
        reasons.append("Todavía lejos del nivel del once")
    # La confianza del ojeador introduce una lectura algo imperfecta.
    noise = (zlib.crc32(player.id.encode("utf-8")) % 100) / 100 - 0.5
    score += noise * 2.5
    # No se recorta a 100 aquí: la recomendación final se normaliza por
    # ranking para que varios jugadores buenos no empaten todos en 100.
    return max(0, round(score, 1)), reasons[:4]


def recommendations(
    state: GameState,
    focus: str = "equilibrado",
    limit: int = 16,
    max_age: int | None = None,
    position: str | None = None,
) -> list[dict[str, Any]]:
    if focus not in FOCUS_LABELS:
        focus = "equilibrado"
    team = state.user_team
    quality, _ = _team_quality(team)
    needs = _needs(team)
    budget = max(0, team.transfer_budget)
    pool = market_players(state, limit=2000, max_age=max_age, position=position)
    owners: dict[str, TeamState] = {p.id: t for t in state.teams.values() for p in t.players}
    rows = []
    for player in pool:
        asking = asking_price(player)
        if asking > budget * 1.12 and player.id not in {p.id for p in state.free_agents}:
            continue
        if asking > budget and player.id not in {p.id for p in state.free_agents}:
            continue
        score, reasons = _fit_score(player, team, quality, needs, asking, focus)
        owner = owners.get(player.id)
        rows.append(
            {
                "player": player,
                "score": score,
                "reasons": reasons or ["Perfil interesante para el club"],
                "asking": asking,
                "owner_name": owner.name if owner else "Agente libre",
                "league": player.league,
                "league_name": competition(player.league).short_name,
                "age": player.age,
                "overall": round(player.overall, 1),
                "potential": round(player.potential, 1),
                "salary": player.salary,
                "rating": round(player.rating, 2),
                "apps": player.apps,
                "goals": player.season_goals,
                "assists": player.season_assists,
                "affordable": asking <= budget,
                "need_group": player.position_group,
            }
        )
    rows.sort(key=lambda row: row["score"], reverse=True)
    rows = rows[:limit]
    # El score bruto satura cuando hay varios jugadores por encima del nivel
    # del once. Se normaliza dentro de la terna recomendada para que el
    # ojeador distinga al mejor del resto (100 = mejor, 60 = último).
    if len(rows) > 1:
        high = max(row["score"] for row in rows)
        low = min(row["score"] for row in rows)
        if high > low:
            for row in rows:
                row["score"] = round(60 + 40 * (row["score"] - low) / (high - low), 1)
    return rows


def scout_summary(state: GameState, focus: str = "equilibrado", max_age: int | None = None, position: str | None = None) -> dict[str, Any]:
    context = scout_context(state)
    context["focus"] = focus
    context["recommendations"] = recommendations(state, focus=focus, limit=16, max_age=max_age, position=position)
    return context


SCOUT_POSITIONS = ("Portero", "Central", "Lateral", "Medio", "Delantero")
MAX_ACTIVE_ASSIGNMENTS = 3


def _scout_staff(state: GameState) -> list[dict[str, Any]]:
    rows = [
        {"id": member.name, "name": member.name, "rating": int(member.rating)}
        for member in state.user_team.staff
        if member.role == "scout"
    ]
    if not rows:
        rows.append(
            {
                "id": "",
                "name": "Red de ojeadores del club",
                "rating": state.user_team.staff_rating("scout", 55),
            }
        )
    return rows


def assignment_options(state: GameState) -> dict[str, Any]:
    competitions = []
    seen = set()
    for team in state.teams.values():
        if team.league in seen:
            continue
        seen.add(team.league)
        meta = competition(team.league)
        competitions.append({"code": meta.code, "name": meta.short_name, "country": meta.country})
    competitions.sort(key=lambda item: (item["country"], item["name"]))
    return {
        "scouts": _scout_staff(state),
        "competitions": competitions,
        "positions": [{"id": "", "label": "Todas"}, *({"id": pos, "label": pos} for pos in SCOUT_POSITIONS)],
        "focuses": [{"id": key, "label": value} for key, value in FOCUS_LABELS.items()],
        "max_active": MAX_ACTIVE_ASSIGNMENTS,
    }


def create_assignment(
    state: GameState,
    scout_id: str,
    competition_code: str,
    position: str = "",
    max_age: int | None = None,
    focus: str = "equilibrado",
) -> dict[str, Any]:
    scouts = _scout_staff(state)
    scout = next((item for item in scouts if item["id"] == scout_id), None)
    if scout is None:
        return {"ok": False, "message": "El ojeador no está disponible."}
    if competition_code not in {team.league for team in state.teams.values()}:
        return {"ok": False, "message": "La competición no es válida."}
    if position and position not in SCOUT_POSITIONS:
        return {"ok": False, "message": "La posición no es válida."}
    if focus not in FOCUS_LABELS:
        focus = "equilibrado"
    if max_age is not None:
        max_age = max(14, min(40, int(max_age)))
    active = [item for item in state.scouting_assignments if item.get("status") == "activo"]
    if len(active) >= MAX_ACTIVE_ASSIGNMENTS:
        return {"ok": False, "message": f"Solo puedes tener {MAX_ACTIVE_ASSIGNMENTS} asignaciones activas."}
    meta = competition(competition_code)
    assignment = {
        "id": f"SC-{state.season}-{state.round}-{zlib.crc32((scout_id + competition_code + position).encode('utf-8')) % 10000}",
        "scout_id": scout["id"],
        "scout_name": scout["name"],
        "scout_rating": scout["rating"],
        "competition": competition_code,
        "competition_name": meta.short_name,
        "position": position,
        "max_age": max_age,
        "focus": focus,
        "focus_label": FOCUS_LABELS[focus],
        "created": state.date,
        "progress": 0,
        "status": "activo",
        "reports": 0,
    }
    state.scouting_assignments.append(assignment)
    state.inbox.append(
        {
            "date": state.date,
            "from": "Red de ojeadores",
            "subject": f"Nueva asignación: {meta.short_name}",
            "body": f"{scout['name']} buscará {position.lower() if position else 'jugadores'} en {meta.short_name}.",
        }
    )
    state.inbox = state.inbox[-80:]
    return {"ok": True, "message": "Asignación de ojeo creada.", "assignment": assignment}


def cancel_assignment(state: GameState, assignment_id: str) -> dict[str, Any]:
    assignment = next((item for item in state.scouting_assignments if item.get("id") == assignment_id), None)
    if assignment is None:
        return {"ok": False, "message": "La asignación no existe."}
    state.scouting_assignments = [item for item in state.scouting_assignments if item.get("id") != assignment_id]
    return {"ok": True, "message": "Asignación cancelada."}


def advance_scouting(state: GameState) -> dict[str, Any]:
    """Avanza una semana de ojeo y genera informes al completar una asignación."""
    completed = 0
    active = 0
    for assignment in state.scouting_assignments:
        if assignment.get("status") != "activo":
            continue
        progress = min(100, int(assignment.get("progress", 0)) + 22 + int(assignment.get("scout_rating", 55)) // 10)
        assignment["progress"] = progress
        if progress < 100:
            active += 1
            continue
        rows = recommendations(
            state,
            focus=str(assignment.get("focus", "equilibrado")),
            limit=30,
            max_age=assignment.get("max_age"),
            position=assignment.get("position") or None,
        )
        league_rows = [row for row in rows if row.get("league") == assignment.get("competition")]
        chosen = league_rows[:5]
        report = {
            "id": f"SR-{state.season}-{assignment['id']}",
            "assignment_id": assignment["id"],
            "date": state.date,
            "season": state.season,
            "scout_name": assignment.get("scout_name", ""),
            "competition": assignment.get("competition", ""),
            "competition_name": assignment.get("competition_name", ""),
            "position": assignment.get("position", ""),
            "focus": assignment.get("focus", ""),
            "message": (
                f"{len(chosen)} objetivos encontrados en {assignment.get('competition_name', '')}."
                if chosen
                else f"Sin objetivos que encajen en {assignment.get('competition_name', '')} con los filtros actuales."
            ),
            "players": [
                {
                    "id": row["player"].id,
                    "name": row["player"].name,
                    "team": row.get("owner_name", ""),
                    "league": row.get("league_name", ""),
                    "age": row.get("age"),
                    "overall": row.get("overall"),
                    "potential": row.get("potential"),
                    "score": row.get("score"),
                    "reasons": row.get("reasons", []),
                }
                for row in chosen
            ],
        }
        assignment["status"] = "completado"
        assignment["completed"] = state.date
        assignment["reports"] = int(assignment.get("reports", 0)) + 1
        state.scouting_reports.append(report)
        state.scouting_reports = state.scouting_reports[-30:]
        state.inbox.append(
            {
                "date": state.date,
                "from": "Red de ojeadores",
                "subject": f"Informe de {assignment.get('competition_name', '')}",
                "body": f"{assignment.get('scout_name', 'El ojeador')} ha entregado un informe con {len(chosen)} objetivos.",
            }
        )
        state.inbox = state.inbox[-80:]
        completed += 1
    return {"completed": completed, "active": active}


def scouting_overview(
    state: GameState,
    focus: str = "equilibrado",
    max_age: int | None = None,
    position: str | None = None,
) -> dict[str, Any]:
    payload = scout_summary(state, focus=focus, max_age=max_age, position=position)
    payload["assignments"] = [item for item in state.scouting_assignments if item.get("status") == "activo"]
    payload["assignment_options"] = assignment_options(state)
    payload["reports"] = list(reversed(state.scouting_reports[-10:]))
    return payload
