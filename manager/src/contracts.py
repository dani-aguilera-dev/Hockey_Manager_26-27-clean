"""Centro de contratos: vencimientos, salarios y situación de la plantilla."""

from __future__ import annotations

from typing import Any

from .models import GameState


def _contract_year(player) -> int:
    try:
        return int(str(player.contract_until)[:4])
    except (TypeError, ValueError):
        return 0


def contracts_overview(state: GameState) -> dict[str, Any]:
    team = state.user_team
    season_end = int(state.season[:4]) + 1
    rows = []
    for player in sorted(team.squad, key=lambda item: (_contract_year(item), -item.salary, item.name)):
        end_year = _contract_year(player)
        years = max(0, end_year - season_end)
        if player.loan:
            status = "cedido"
        elif end_year <= season_end:
            status = "expira"
        elif years <= 1:
            status = "renovar"
        else:
            status = "seguro"
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
                "years_remaining": years,
                "status": status,
                "loan": bool(player.loan),
            }
        )
    wage_bill = team.player_wage_bill()
    return {
        "players": rows,
        "summary": {
            "players": len(rows),
            "wage_bill": wage_bill,
            "average_salary": int(wage_bill / max(1, len(rows))),
            "expiring": sum(1 for row in rows if row["status"] == "expira"),
            "renewal": sum(1 for row in rows if row["status"] == "renovar"),
            "secure": sum(1 for row in rows if row["status"] == "seguro"),
            "loaned": sum(1 for row in rows if row["status"] == "cedido"),
            "budget": int(team.budget),
            "wage_budget": int(team.wage_budget),
            "total_value": sum(row["value"] for row in rows),
        },
        "top_earners": sorted(rows, key=lambda row: row["salary"], reverse=True)[:8],
        "renewal_candidates": [row for row in rows if row["status"] in ("expira", "renovar")],
    }
