from src.history import archive_season, history_overview
from src.models import GameState
from src.season import new_game, play_round


def test_history_current_matches_and_archive():
    state = new_game("cd-terrassa", "History Test", seed=91)
    play_round(state)
    current = history_overview(state)
    assert current["matches"]
    assert current["players"]
    assert current["summary"]["current_season"] == state.season
    archived = archive_season(state)
    assert archived["matches"] > 0
    assert archived["players"] > 0
    data = history_overview(state)
    assert len(data["matches"]) == len(current["matches"])
    assert data["summary"]["matches"] > 0
    assert data["records"]["biggest_win"] is not None


def test_history_filters_and_records():
    state = new_game("cd-terrassa", "History Test", seed=92)
    play_round(state)
    archive_season(state)
    data = history_overview(state, team_id=state.club_id)
    assert data["matches"]
    assert all(state.club_id in (row["home_id"], row["away_id"]) for row in data["matches"])
    player_name = data["players"][0]["name"].split()[0]
    filtered = history_overview(state, player_query=player_name)
    assert all(player_name.lower() in row["name"].lower() for row in filtered["players"])
    season_data = history_overview(state, season=state.season)
    assert season_data["matches"]
    assert season_data["summary"]["matches"] > 0
    assert data["records"]["top_scorer"]
    assert data["records"]["most_apps"]


def test_history_archive_is_idempotent_and_persists():
    state = new_game("cd-terrassa", "History Test", seed=93)
    play_round(state)
    first = archive_season(state)
    second = archive_season(state)
    assert first["matches"] > 0
    assert second == {"matches": 0, "players": 0}
    restored = GameState.from_dict(state.to_dict())
    assert len(restored.match_history) == len(state.match_history)
    assert len(restored.player_history) == len(state.player_history)
    assert restored.match_history[0]["season"] == state.season
