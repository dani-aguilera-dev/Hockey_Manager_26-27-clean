from src.clauses import clauses_overview, set_clause
from src.models import GameState
from src.season import new_game


def test_clauses_overview_has_suggestions_and_summary():
    state = new_game("cd-terrassa", "Clause Test", seed=191)
    data = clauses_overview(state)
    assert data["players"]
    assert data["summary"]["without_clause"] == len(data["players"])
    player = data["players"][0]
    assert player["suggested_clause"] > 0
    assert player["suggested_bonus"] > 0


def test_set_clause_deducts_bonus_and_persists():
    state = new_game("cd-terrassa", "Clause Test", seed=192)
    player = clauses_overview(state)["players"][0]
    before_budget = state.user_team.budget
    result = set_clause(state, player["id"], 1_000_000, 50_000)
    assert result["ok"] is True
    assert state.user_team.budget == before_budget - 50_000
    assert state.user_team.players[0].release_clause >= 0
    restored = GameState.from_dict(state.to_dict())
    restored_row = next(row for row in clauses_overview(restored)["players"] if row["id"] == player["id"])
    assert restored_row["release_clause"] == 1_000_000
    assert restored_row["renewal_bonus"] == 50_000


def test_clause_validation():
    state = new_game("cd-terrassa", "Clause Test", seed=193)
    player = clauses_overview(state)["players"][0]
    assert set_clause(state, "no-existe", 1000, 0)["ok"] is False
    assert set_clause(state, player["id"], player["value"] * 6, 0)["ok"] is False
    assert set_clause(state, player["id"], 1000, state.user_team.budget + 1)["ok"] is False
