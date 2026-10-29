from src.analysis import analysis_overview
from src.season import new_game, play_round


def test_analysis_overview_has_metrics_timeline_and_players():
    state = new_game("cd-terrassa", "Analysis Test", seed=131)
    play_round(state)
    data = analysis_overview(state)
    assert data["match"] is not None
    assert data["metrics"]["home"]["shots"] >= data["metrics"]["home"]["shots_on_target"]
    assert data["metrics"]["home"]["danger_index"] >= 0
    assert data["timeline"]
    assert data["players"]
    assert data["recent"]
    assert data["season"]["matches"] >= 1
    assert data["source"] == "last_result"


def test_analysis_can_open_archived_match():
    state = new_game("cd-terrassa", "Analysis Test", seed=132)
    play_round(state)
    fixture_id = state.last_result["fixture_id"]
    from src.history import archive_season
    archive_season(state)
    data = analysis_overview(state, fixture_id)
    assert data["match"]["fixture_id"] == fixture_id
    assert data["metrics"]["home"]["shots"] >= 0
    assert data["source"] == "archive"
    assert data["recent"]
