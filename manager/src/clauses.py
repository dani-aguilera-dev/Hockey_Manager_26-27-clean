"""Cláusulas contractuales y primas de renovación.

La cláusula de rescisión protege al jugador en el mercado; la prima de
renovación es un pago único que mejora la relación y la predisposición a
firmar. Ambas quedan guardadas en la ficha del jugador.
"""

from __future__ import annotations

from typing import Any

from .models import GameState, PlayerState


def _clause_status(player: PlayerState) -> str:
    if player.release_clause <= 0:
        return "sin_clausula"
    if player.release_clause >= int(player.value * 1.8):
        return "alta"
    if player.release_clause >= int(player.value * 1.2):
        return "protegida"
    return "baja"


def clauses_overview(state: GameState) -> dict[str, Any]:
    team = state.user_team
    rows = []
    for player in sorted(team.squad, key=lambda item: (-item.overall, item.name)):
        rows.append(
            {
                "id": player.id,
                "name": player.name,
                "age": player.age,
                "position": player.subposition,
                "overall": round(float(player.overall), 1),
                "salary": int(player.salary),
                "value": int(player.value),
                "contract_until": player.contract_until,
                "release_clause": int(player.release_clause),
                "renewal_bonus": int(player.renewal_bonus),
                "clause_status": _clause_status(player),
                "suggested_clause": int(max(player.value * 1.5, player.salary * 4)),
                "suggested_bonus": int(max(5000, player.salary * 0.10)),
            }
        )
    protected = sum(1 for row in rows if row["release_clause"] > 0)
    return {
        "players": rows,
        "summary": {
            "players": len(rows),
            "protected": protected,
            "without_clause": len(rows) - protected,
            "total_clause": sum(row["release_clause"] for row in rows),
            "total_bonus": sum(row["renewal_bonus"] for row in rows),
            "budget": int(team.budget),
        },
    }


def set_clause(
    state: GameState,
    player_id: str,
    release_clause: int,
    renewal_bonus: int,
) -> dict[str, Any]:
    player = next((item for item in state.user_team.squad if item.id == player_id), None)
    if player is None:
        return {"ok": False, "message": "El jugador no está en la plantilla."}
    release_clause = max(0, int(release_clause))
    renewal_bonus = max(0, int(renewal_bonus))
    if release_clause > int(player.value * 5):
        return {"ok": False, "message": "La cláusula no puede superar cinco veces el valor del jugador."}
    if renewal_bonus > state.user_team.budget:
        return {"ok": False, "message": "No hay caja suficiente para la prima de renovación."}
    state.user_team.budget -= renewal_bonus
    player.release_clause = release_clause
    player.renewal_bonus = renewal_bonus
    if renewal_bonus > 0:
        player.relationship = min(100, player.relationship + 3)
        player.morale = min(20, player.morale + 1)
    state.market_history.append(
        {
            "type": "clausula",
            "round": state.round,
            "season": state.season,
            "player": player.name,
            "overall": round(player.overall, 1),
            "from": state.user_team.name,
            "to": state.user_team.name,
            "fee": renewal_bonus,
            "salary": player.salary,
            "clause": release_clause,
        }
    )
    return {
        "ok": True,
        "message": f"Cláusula de {player.name} actualizada a {release_clause:,} €.".replace(",", "."),
        "player_id": player.id,
        "release_clause": release_clause,
        "renewal_bonus": renewal_bonus,
    }
