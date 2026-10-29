from datetime import date

from src.daily import simulate_days
from src.market import market_players
from src.season import new_game, play_round, record_season_career, simulate_cup_remaining, simulate_cup_round


def test_daily_simulation_stops_at_next_match():
    state = new_game("cd-terrassa", "Test", seed=801)
    assert state.date == "2026-08-01"
    fixture = state.next_user_fixture()
    assert fixture
    result = simulate_days(state, target_date=fixture.date, stop_at_match=True)
    assert result["ok"]
    assert result["stopped_at_match"]
    assert state.date == fixture.date
    assert state.daily_events
    assert any(e["category"] == "Partido" for e in state.daily_events)


def test_daily_simulation_to_exact_date():
    state = new_game("cd-terrassa", "Test", seed=802)
    result = simulate_days(state, target_date="2026-08-10", stop_at_match=False)
    assert result["days"] == 9
    assert state.date == "2026-08-10"
    assert state.daily_events


def test_market_players_include_other_teams_and_stats():
    state = new_game("cd-terrassa", "Test", seed=803)
    players = market_players(state, limit=500)
    assert players
    other = [p for p in players if p.team_name != state.user_team.name]
    assert other
    assert all(p.team_name for p in other)


def test_cup_is_in_the_daily_calendar():
    state = new_game("cd-terrassa", "Test", seed=805)
    for _ in range(11):
        play_round(state, None, "equilibrado")
    assert state.cup_active
    from src.cup import cup_round_fixtures

    state.club_id = cup_round_fixtures(state)[0].home_id
    fixture = state.next_user_fixture()
    assert fixture is not None
    assert fixture.phase.startswith("cup_")
    assert fixture.date == "2026-12-02"
    payload = simulate_cup_round(state, state.manual_lineup or None)
    assert payload
    assert state.cup_round == 2
    next_fixture = state.next_user_fixture()
    if next_fixture and next_fixture.phase.startswith("cup_"):
        assert next_fixture.phase == "cup_sf"


def test_ehl_is_scheduled_and_simulated_on_its_date():
    state = new_game("cd-terrassa", "Test", seed=806)
    for _ in range(11):
        play_round(state, None, "equilibrado")
    simulate_cup_remaining(state)
    for _ in range(5):
        play_round(state, None, "equilibrado")
    assert state.ehl.get("dates") == ["2027-01-07", "2027-01-08", "2027-01-09"]
    simulate_days(state, target_date="2027-01-08", stop_at_match=True)
    assert state.ehl.get("results")
    assert any(event["category"] == "EHL" for event in state.daily_events)


def test_player_career_is_recorded():
    state = new_game("cd-terrassa", "Test", seed=804)
    player = state.user_team.players[0]
    player.apps = 12
    player.season_goals = 7
    player.season_assists = 4
    player.rating_sum = 84.0
    record_season_career(state)
    assert player.career
    row = player.career[-1]
    assert row["season"] == state.season
    assert row["club"] == state.user_team.name
    assert row["goals"] == 7
    assert date.fromisoformat(state.date).year == 2026


def test_daily_simulation_can_stop_at_a_decision():
    state = new_game("cd-terrassa", "Test", seed=807)
    for player in state.user_team.players:
        player.fatigue = 80
    result = simulate_days(state, days=30, stop_at_match=False, stop_at_decision=True)
    assert result["ok"]
    assert result["stopped_at_decision"]
    assert state.pending_events
