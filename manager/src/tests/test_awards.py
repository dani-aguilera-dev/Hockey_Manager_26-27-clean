from src.awards import archive_season_awards, awards_overview, season_awards
from src.models import GameState
from src.season import new_game, play_round


def test_season_awards_and_best_xi():
    state = new_game("cd-terrassa", "Awards Test", seed=161)
    play_round(state)
    data = season_awards(state)
    assert data["awards"]
    assert {award["id"] for award in data["awards"]} >= {"top_scorer", "mvp"}
    assert len(data["best_xi"]) == 11
    assert all(player["player_name"] for player in data["best_xi"])


def test_awards_overview_includes_last_match_and_history():
    state = new_game("cd-terrassa", "Awards Test", seed=162)
    play_round(state)
    data = awards_overview(state)
    assert data["last_match"]
    archive_season_awards(state)
    assert state.awards_history
    restored = GameState.from_dict(state.to_dict())
    assert restored.awards_history
    assert restored.awards_history[0]["season"] == state.season
