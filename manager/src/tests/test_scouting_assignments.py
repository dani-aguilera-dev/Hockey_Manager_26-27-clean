from src.models import GameState
from src.scouting import (
    advance_scouting,
    cancel_assignment,
    create_assignment,
    scouting_overview,
)
from src.season import new_game


def test_scouting_overview_has_assignment_options():
    state = new_game("cd-terrassa", "Scout Test", seed=101)
    data = scouting_overview(state)
    assert data["assignment_options"]["scouts"]
    assert data["assignment_options"]["competitions"]
    assert data["assignment_options"]["positions"]
    assert data["assignments"] == []
    assert data["recommendations"]


def test_create_assignment_and_complete_report():
    state = new_game("cd-terrassa", "Scout Test", seed=102)
    options = scouting_overview(state)["assignment_options"]
    result = create_assignment(
        state,
        options["scouts"][0]["id"],
        "DHB",
        "Delantero",
        24,
        "joven",
    )
    assert result["ok"] is True
    assignment = state.scouting_assignments[0]
    assert assignment["competition"] == "DHB"
    assert assignment["position"] == "Delantero"
    assert assignment["max_age"] == 24
    assert assignment["status"] == "activo"
    for _ in range(4):
        advance_scouting(state)
    assert assignment["status"] == "completado"
    assert state.scouting_reports
    assert state.scouting_reports[-1]["assignment_id"] == assignment["id"]
    assert "message" in state.scouting_reports[-1]


def test_assignment_limit_and_validation():
    state = new_game("cd-terrassa", "Scout Test", seed=103)
    options = scouting_overview(state)["assignment_options"]
    scout = options["scouts"][0]["id"]
    competitions = [item["code"] for item in options["competitions"][:3]]
    for code in competitions:
        assert create_assignment(state, scout, code)["ok"] is True
    assert len(state.scouting_assignments) == 3
    fourth = create_assignment(state, scout, competitions[0])
    assert fourth["ok"] is False
    assert create_assignment(state, scout, "NO-EXISTE")["ok"] is False
    assert create_assignment(state, "scout-inventado", competitions[0])["ok"] is False
    assignment_id = state.scouting_assignments[0]["id"]
    assert cancel_assignment(state, assignment_id)["ok"] is True
    assert len(state.scouting_assignments) == 2


def test_scouting_assignments_persist():
    state = new_game("cd-terrassa", "Scout Test", seed=104)
    options = scouting_overview(state)["assignment_options"]
    create_assignment(state, options["scouts"][0]["id"], "DHB", "Medio", 23, "tecnica")
    advance_scouting(state)
    restored = GameState.from_dict(state.to_dict())
    assert restored.scouting_assignments
    assert restored.scouting_assignments[0]["position"] == "Medio"
    assert restored.scouting_assignments[0]["progress"] > 0
