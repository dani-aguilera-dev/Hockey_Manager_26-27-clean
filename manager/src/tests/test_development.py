from src.development import advance_development, clear_development_plan, development_overview, set_development_plan
from src.models import GameState
from src.season import new_game


def test_development_overview_has_players_and_focuses():
    state = new_game("cd-terrassa", "Dev Test", seed=151)
    data = development_overview(state)
    assert data["players"]
    assert data["focuses"]
    assert data["intensities"]
    assert data["active"] == 0


def test_development_plan_progresses_and_gains_attributes():
    state = new_game("cd-terrassa", "Dev Test", seed=152)
    player = development_overview(state)["players"][0]
    result = set_development_plan(state, player["player_id"], "tecnica", "normal", "mejorar pase")
    assert result["ok"] is True
    for _ in range(4):
        advance_development(state)
    updated = next(row for row in development_overview(state)["players"] if row["player_id"] == player["player_id"])
    assert updated["sessions"] == 4
    assert updated["progress"] > 0
    assert updated["last_gain"]
    restored = GameState.from_dict(state.to_dict())
    restored_player = next(row for row in development_overview(restored)["players"] if row["player_id"] == player["player_id"])
    assert restored_player["focus"] == "tecnica"


def test_development_validation_and_clear():
    state = new_game("cd-terrassa", "Dev Test", seed=153)
    player = development_overview(state)["players"][0]
    assert set_development_plan(state, "no-existe", "tecnica")["ok"] is False
    assert set_development_plan(state, player["player_id"], "no-existe")["ok"] is False
    assert set_development_plan(state, player["player_id"], "tecnica", "no-existe")["ok"] is False
    assert set_development_plan(state, player["player_id"], "fisico", "intensa")["ok"] is True
    assert clear_development_plan(state, player["player_id"])["ok"] is True
    assert development_overview(state)["active"] == 0
