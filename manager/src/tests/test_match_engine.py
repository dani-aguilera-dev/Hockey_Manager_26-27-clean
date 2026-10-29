import random
import statistics

from src.data_loader import dha_teams, load_teams
from src.match_engine import MatchEngine


def test_match_is_deterministic():
    teams1, _, _ = load_teams()
    teams2, _, _ = load_teams()
    r1 = MatchEngine(teams1["cd-terrassa"], teams1["ud-taburiente"], random.Random(123), detailed=True).simulate()
    r2 = MatchEngine(teams2["cd-terrassa"], teams2["ud-taburiente"], random.Random(123), detailed=True).simulate()
    assert (r1.home_goals, r1.away_goals) == (r2.home_goals, r2.away_goals)
    assert [e["text"] for e in r1.events] == [e["text"] for e in r2.events]
    assert r1.home_stats["shots"] == r2.home_stats["shots"]


def test_match_statistics_and_balance():
    teams, _, _ = load_teams()
    dha = dha_teams(teams)
    rows = []
    for i in range(120):
        h, a = random.Random(i).sample(dha, 2)
        r = MatchEngine(h, a, random.Random(1000 + i)).simulate()
        assert r.home_stats["goals"] == r.home_goals
        assert r.away_stats["goals"] == r.away_goals
        assert r.home_stats["pc"] >= r.home_stats["pc_goals"]
        assert r.home_stats["shots"] >= r.home_stats["shots_on_target"]
        assert r.home_stats["strokes"] >= r.home_stats["stroke_goals"]
        for e in r.events:
            if e["type"] == "goal":
                assert e["player_id"]
        rows.append(
            (
                r.home_goals + r.away_goals,
                r.home_stats["shots"] + r.away_stats["shots"],
                r.home_stats["pc"] + r.away_stats["pc"],
            )
        )
    goals = statistics.mean(x[0] for x in rows)
    shots = statistics.mean(x[1] for x in rows)
    pcs = statistics.mean(x[2] for x in rows)
    assert 3.5 <= goals <= 6.5, goals
    assert 10 <= shots <= 23, shots
    assert 4 <= pcs <= 9, pcs


def test_set_pieces_have_events():
    teams, _, _ = load_teams()
    a = teams["atletic-terrassa"]
    b = teams["club-egara"]
    r = MatchEngine(a, b, random.Random(7), detailed=True).simulate()
    types = {e["type"] for e in r.events}
    assert "pc" in types
    assert any(e["type"] in ("goal", "save") for e in r.events)
