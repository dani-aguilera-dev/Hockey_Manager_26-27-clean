from src.commercial import set_ticket_price
from src.finance import finance_overview
from src.models import GameState
from src.season import new_game


def test_finance_overview_has_breakdown_projection_and_earners():
    state = new_game("cd-terrassa", "Finance Test", seed=121)
    data = finance_overview(state)
    assert data["cash"] == state.user_team.budget
    assert data["annual_income"] > 0
    assert data["annual_expenses"] > 0
    assert data["wage_ratio"] > 0
    assert data["top_earners"]
    assert data["ticket_scenarios"]
    assert len(data["ticket_scenarios"]) >= 5
    assert data["staff_wage_rows"] is not None


def test_finance_ticket_price_updates_and_persists():
    state = new_game("cd-terrassa", "Finance Test", seed=122)
    result = set_ticket_price(state, 22)
    assert result["ok"] is True
    data = finance_overview(state)
    assert data["ticket_price"] == 22
    assert any(row["price"] == 22 for row in data["ticket_scenarios"])
    restored = GameState.from_dict(state.to_dict())
    assert restored.user_team.ticket_price == 22
    assert restored.user_team.commercial_history[-1]["type"] == "taquilla"
