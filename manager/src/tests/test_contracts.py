from src.contracts import contracts_overview
from src.models import GameState
from src.season import new_game


def test_contracts_overview_has_summary_and_candidates():
    state = new_game("cd-terrassa", "Contract Test", seed=171)
    data = contracts_overview(state)
    assert data["players"]
    assert data["summary"]["players"] == len(data["players"])
    assert data["summary"]["wage_bill"] > 0
    assert data["renewal_candidates"]
    assert data["top_earners"]
    assert all(row["status"] in ("expira", "renovar", "seguro", "cedido") for row in data["players"])


def test_contracts_persist_contract_dates():
    state = new_game("cd-terrassa", "Contract Test", seed=172)
    restored = GameState.from_dict(state.to_dict())
    original = {row["id"]: row["contract_until"] for row in contracts_overview(state)["players"]}
    restored_rows = {row["id"]: row["contract_until"] for row in contracts_overview(restored)["players"]}
    assert original == restored_rows
