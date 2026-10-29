"""Finanzas de club: salarios, patrocinio, taquilla y viajes."""

from __future__ import annotations

from typing import Any


def sponsor_income(team) -> int:
    """Ingreso comercial por jornada: acuerdos activos + merchandising.

    Si el club todavía no tiene acuerdos, se mantiene un ingreso base de
    patrocinio para que la economía inicial siga siendo estable.
    """
    from .commercial import active_sponsor_round, merchandising_round

    active = active_sponsor_round(team)
    merchandise = merchandising_round(team)
    if active > 0:
        return int(active + merchandise)
    annual = team.wage_budget * (0.55 + max(1, team.club_tier) * 0.04)
    return int(max(0, annual) / 22)


def round_wage_cost(team) -> tuple[int, int]:
    """Salarios de jugadores y staff por jornada."""
    players = int(team.player_wage_bill() / 22)
    staff = int(team.staff_wage_bill() / 22)
    return players, staff


def apply_round_finances(state: Any) -> None:
    """Cierra las cuentas de la jornada actual para los clubes DHA."""
    if getattr(state, "finance_round", 0) == state.round:
        return
    for team in state.teams.values():
        if team.league not in ("DHA", "DHB") and team.league != state.competition:
            continue
        fixtures = [f for f in state.fixtures if f.phase == "regular" and f.round == state.round and f.played]
        gate = sum(int(f.home_stats.get("gate_revenue", 0)) for f in fixtures if f.home_id == team.id)
        travel = sum(int((f.travel or {}).get("cost", 0)) for f in fixtures if f.away_id == team.id)
        sponsor = sponsor_income(team)
        player_wages, staff_wages = round_wage_cost(team)
        wages = player_wages + staff_wages
        team.budget += sponsor - wages
        entry = {
            "round": state.round,
            "gate": gate,
            "sponsor": sponsor,
            "player_wages": player_wages,
            "staff_wages": staff_wages,
            "wages": wages,
            "travel": travel,
            "net": gate + sponsor - wages - travel,
            "cash_after": team.budget,
        }
        team.finance_log.append(entry)
        team.finance_log = team.finance_log[-30:]
        if team.id == state.club_id and team.budget < 0:
            team.board_confidence = max(0, team.board_confidence - 3)
            team.fan_confidence = max(0, team.fan_confidence - 1)
    state.finance_round = state.round


def financial_summary(team) -> dict:
    log = team.finance_log
    gate = sum(int(e.get("gate", 0)) for e in log)
    sponsor = sum(int(e.get("sponsor", 0)) for e in log)
    player_wages = sum(int(e.get("player_wages", 0)) for e in log)
    staff_wages = sum(int(e.get("staff_wages", 0)) for e in log)
    travel = sum(int(e.get("travel", 0)) for e in log)
    income = gate + sponsor
    expenses = player_wages + staff_wages + travel
    from .commercial import active_sponsor_annual

    return {
        "cash": team.budget,
        "transfer_budget": team.transfer_budget,
        "brand_rating": team.brand_rating,
        "brand_value": int(team.brand_rating**2 * 950),
        "sponsor_annual": active_sponsor_annual(team),
        "ticket_price": team.ticket_price,
        "player_wage_bill": team.player_wage_bill(),
        "staff_wage_bill": team.staff_wage_bill(),
        "annual_wage_bill": team.player_wage_bill() + team.staff_wage_bill(),
        "round_player_wages": int(team.player_wage_bill() / 22),
        "round_staff_wages": int(team.staff_wage_bill() / 22),
        "sponsor_round": sponsor_income(team),
        "gate": gate,
        "sponsor": sponsor,
        "player_wages": player_wages,
        "staff_wages": staff_wages,
        "travel": travel,
        "income": income,
        "expenses": expenses,
        "net": income - expenses,
        "entries": log[-6:],
    }


def finance_overview(state: Any) -> dict:
    """Vista completa de finanzas para la pantalla dedicada."""
    team = state.user_team
    summary = financial_summary(team)
    from .commercial import active_sponsor_annual, ticket_income_estimate

    sponsor_annual = active_sponsor_annual(team) or summary["sponsor_round"] * 22
    ticket_match = ticket_income_estimate(team)
    annual_income = sponsor_annual + ticket_match * 22
    annual_expenses = team.player_wage_bill() + team.staff_wage_bill()
    annual_net = annual_income - annual_expenses
    round_burn = max(0, int(team.player_wage_bill() / 22) + int(team.staff_wage_bill() / 22) - summary["sponsor_round"])
    runway = int(team.budget / round_burn) if round_burn > 0 else 99
    top_earners = sorted(team.players, key=lambda player: player.salary, reverse=True)[:8]
    wage_bill = max(1, team.player_wage_bill())
    scenarios = []
    base_attendance = max(1, int(team.stadium_capacity * 0.62))
    for price in sorted({10, 15, 20, 25, 30, 35, int(team.ticket_price)}):
        factor = max(0.45, min(1.12, 1 - (price - 15) * 0.018))
        attendance = int(base_attendance * factor)
        scenarios.append(
            {
                "price": price,
                "attendance": attendance,
                "revenue": attendance * price,
                "season_revenue": attendance * price * 22,
            }
        )
    return {
        **summary,
        "log": list(reversed(team.finance_log[-12:])),
        "top_earners": [
            {
                "id": player.id,
                "name": player.name,
                "position": player.subposition,
                "overall": round(float(player.overall), 1),
                "salary": int(player.salary),
                "share": round(100 * player.salary / wage_bill, 1),
            }
            for player in top_earners
        ],
        "staff_wage_rows": [
            {"name": member.name, "role": member.role, "salary": int(member.salary)}
            for member in sorted(team.staff, key=lambda item: item.salary, reverse=True)
        ],
        "annual_income": annual_income,
        "annual_expenses": annual_expenses,
        "annual_net": annual_net,
        "wage_ratio": round(100 * annual_expenses / max(1, annual_income), 1),
        "runway_rounds": runway,
        "ticket_scenarios": scenarios,
        "active_sponsors": [deal for deal in team.sponsor_deals if deal.get("active", True)],
        "equipment_deals": [deal for deal in team.equipment_deals if deal.get("active", True)],
        "commercial_history": team.commercial_history[-10:],
    }
