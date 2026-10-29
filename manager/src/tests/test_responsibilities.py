from src.models import GameState
from src.responsibilities import responsibility_bonus, responsibilities_overview, set_responsibility
from src.season import new_game
from src.training import apply_training_plan
import random


def test_responsibilities_overview_has_areas_and_staff():
    state = new_game("cd-terrassa", "Resp Test", seed=141)
    data = responsibilities_overview(state)
    assert len(data["areas"]) == 10
    assert data["staff"]
    assert all("options" in area for area in data["areas"])
    assert data["assigned"] == 0


def test_responsibility_assignment_and_bonus():
    state = new_game("cd-terrassa", "Resp Test", seed=142)
    staff = state.user_team.staff[0]
    result = set_responsibility(state, "attack", staff.name)
    assert result["ok"] is True
    assert state.user_team.staff_assignments["attack"] == staff.name
    assert responsibility_bonus(state.user_team, "attack") > 0
    report = apply_training_plan(
        state.user_team,
        ["recuperacion", "ataque", "set_pieces", "video", "activacion"],
        rng=random.Random(1),
    )
    assert "prep_bonus" in report
    cleared = set_responsibility(state, "attack", "")
    assert cleared["ok"] is True
    assert "attack" not in state.user_team.staff_assignments


def test_responsibility_validation_and_persistence():
    state = new_game("cd-terrassa", "Resp Test", seed=143)
    assert set_responsibility(state, "no-existe", "x")["ok"] is False
    assert set_responsibility(state, "attack", "no-existe")["ok"] is False
    staff = state.user_team.staff[0]
    assert set_responsibility(state, "defense", staff.name)["ok"] is True
    restored = GameState.from_dict(state.to_dict())
    assert restored.user_team.staff_assignments["defense"] == staff.name
