import random

from src.facilities import facilities_overview, upgrade_facility
from src.models import GameState
from src.season import new_game


def test_facilities_overview_has_levels_and_upgrades():
    state = new_game("cd-terrassa", "Facilities Test", seed=181)
    data = facilities_overview(state)
    assert len(data["facilities"]) == 6
    assert data["summary"]["average"] > 0
    assert data["upgrades"]
    assert data["stadium"]["name"]


def test_facility_upgrade_and_persistence():
    state = new_game("cd-terrassa", "Facilities Test", seed=182)
    team = state.user_team
    team.budget = 5_000_000
    team.board_confidence = 100
    team.fan_confidence = 100
    before = team.facilities["training"]
    result = upgrade_facility(state, "training", rng=random.Random(1))
    assert result["ok"] is True
    assert result["facilities"]["history"]
    if result.get("approved"):
        assert team.facilities["training"] > before
    restored = GameState.from_dict(state.to_dict())
    assert restored.user_team.board_requests
    assert facilities_overview(restored)["history"]
