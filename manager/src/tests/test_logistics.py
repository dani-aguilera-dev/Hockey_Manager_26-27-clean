from src.data_loader import load_clubs, load_teams
from src.logistics import apply_travel, distance_between, travel_options


def test_distances_and_modes():
    teams, _, cities = load_teams()
    ter = teams["cd-terrassa"]
    bar = teams["fc-barcelona"]
    tab = teams["ud-taburiente"]
    d_short = distance_between(ter, bar, cities)
    d_long = distance_between(tab, ter, cities)
    assert 20 <= d_short <= 40
    assert d_long > 1500
    short = travel_options(ter, bar, cities)
    long = travel_options(tab, ter, cities)
    assert len(short) == 2
    assert short[0]["mode"] == "bus"
    assert short[0]["hotel_nights"] == 0
    assert len(long) == 3
    assert all(o["mode"] == "avión" for o in long)
    assert long[0]["cost"] < long[1]["cost"] < long[2]["cost"]
    assert long[0]["fatigue"] > long[1]["fatigue"] > long[2]["fatigue"]


def test_apply_travel_changes_budget_and_fatigue():
    teams, _, cities = load_teams()
    ter = teams["cd-terrassa"]
    bar = teams["fc-barcelona"]
    opts = travel_options(ter, bar, cities)
    before_budget = ter.budget
    before_fatigue = sum(p.fatigue for p in ter.players) / len(ter.players)
    summary = apply_travel(ter, opts[0])
    after_budget = ter.budget
    after_fatigue = sum(p.fatigue for p in ter.players) / len(ter.players)
    assert after_budget == before_budget - opts[0]["cost"]
    assert after_fatigue > before_fatigue
    assert summary["cost"] == opts[0]["cost"]
