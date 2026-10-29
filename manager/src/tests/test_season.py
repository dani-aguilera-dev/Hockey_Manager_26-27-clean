from src.calendar import dha_table
from src.season import new_game, play_round, season_summary


def test_full_dha_season():
    state = new_game("cd-terrassa", "Test", seed=2026)
    for _ in range(22):
        play_round(state, user_lineup_ids=None, travel_option_id="equilibrado")
    assert state.phase == "season_end"
    assert state.round == 23
    assert len([f for f in state.fixtures if f.phase == "regular"]) == 132
    assert all(f.played for f in state.fixtures if f.phase == "regular")
    table = dha_table(state.teams)
    assert len(table) == 12
    assert sum(t.played for t in table) == 264
    assert state.final4.get("champion_id")
    summ = season_summary(state)
    assert len(summ["table"]) == 12
    assert summ["top_scorers"]
    assert state.playout.get("winner_id")
    assert state.playout.get("direct_relegated_id")
    assert state.playout.get("stays_id") or state.playout.get("promoted_id")


def test_manual_lineup_players_get_minutes():
    state = new_game("cd-terrassa", "Test", seed=99)
    ids = [p.id for p in state.user_team.available_players[:11]]
    assert len(ids) == 11
    play_round(state, user_lineup_ids=ids)
    for pid in ids:
        p = next(x for x in state.user_team.players if x.id == pid)
        assert p.apps == 1
