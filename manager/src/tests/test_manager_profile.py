from src.manager_profile import manager_profile_overview
from src.models import GameState
from src.season import new_game, play_round


def test_manager_profile_has_current_status_and_empty_record():
    state = new_game("cd-terrassa", "Manager Test", seed=221)
    data = manager_profile_overview(state)
    assert data["manager"]["name"] == "Manager Test"
    assert data["manager"]["club"] == state.user_team.name
    assert data["current"]["position"] >= 1
    assert data["record"]["matches"] == 0
    assert data["trophies"]["total"] == 0
    assert data["milestones"]
    assert any(milestone["id"] == "first_match" for milestone in data["milestones"])


def test_manager_profile_counts_played_matches():
    state = new_game("cd-terrassa", "Manager Test", seed=222)
    play_round(state)
    data = manager_profile_overview(state)
    record = data["record"]
    assert record["matches"] >= 1
    assert record["wins"] + record["draws"] + record["losses"] == record["matches"]
    assert record["goals_for"] >= 0
    assert data["recent"]
    assert data["recent"][0]["result"] in ("V", "E", "D")


def test_manager_profile_trophies_milestones_and_persistence():
    state = new_game("cd-terrassa", "Manager Test", seed=223)
    club = state.user_team.name
    state.history = [
        {
            "season": "2025-26",
            "competition": "DHA",
            "user_club": club,
            "user_position": 1,
            "champion": club,
            "cup_winner": club,
            "ehl_winner": club,
            "promoted": [club],
            "relegated": [],
            "table": [{"team": club, "points": 50}],
        }
    ]
    data = manager_profile_overview(state)
    assert data["trophies"]["total"] == 4
    assert data["trophies"]["league"] == 1
    assert data["trophies"]["cup"] == 1
    assert data["trophies"]["ehl"] == 1
    assert data["trophies"]["promotions"] == 1
    assert data["record"]["best_finish"] == 1
    assert data["record"]["best_points"] == 50
    achieved = {milestone["id"] for milestone in data["milestones"] if milestone["achieved"]}
    assert "first_title" in achieved
    assert "promotion" in achieved
    restored = GameState.from_dict(state.to_dict())
    restored_data = manager_profile_overview(restored)
    assert restored_data["trophies"]["total"] == 4
    assert restored_data["record"]["best_finish"] == 1
