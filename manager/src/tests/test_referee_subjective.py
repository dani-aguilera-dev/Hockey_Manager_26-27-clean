import random

from src.data_loader import load_teams
from src.match_engine import MatchEngine


def _engine(seed: int = 1) -> MatchEngine:
    teams, _, _ = load_teams()
    return MatchEngine(teams["cd-terrassa"], teams["sardinero"], random.Random(seed), detailed=True)


def test_dangerous_play_severity_can_force_card():
    engine = _engine()
    engine.prepare()
    engine.zone = "middle"
    engine._foul(
        0,
        foul_type="dangerous",
        advantage=False,
        distance_call=False,
        dangerous_severity="dangerous",
        dangerous_card=True,
    )
    assert engine.stats[0]["dangerous_play"] == 1
    assert engine.stats[0]["dangerous_sanction"] == 1
    assert engine.cards
    assert any(event["type"] == "dangerous_play" for event in engine.events)


def test_dangerous_play_careless_can_avoid_card():
    engine = _engine(2)
    engine.prepare()
    engine.zone = "middle"
    engine._foul(
        0,
        foul_type="dangerous",
        advantage=False,
        distance_call=False,
        dangerous_severity="careless",
        dangerous_card=False,
    )
    assert engine.stats[0]["dangerous_play"] == 1
    assert engine.stats[0]["dangerous_sanction"] == 0
    assert engine.cards == []


def test_free_hit_can_be_advanced_ten_meters():
    engine = _engine(3)
    engine.prepare()
    engine.zone = "middle"
    engine._foul(
        0,
        foul_type="physical",
        advantage=False,
        distance_call=True,
        advance_10m=True,
    )
    assert engine.stats[1]["distance_5m"] == 1
    assert engine.stats[1]["free_hit_10m"] == 1
    assert any(event["type"] == "free_hit_10m" for event in engine.events)


def test_penalty_corner_can_be_retaken():
    engine = _engine(4)
    engine.prepare()
    engine._penalty_corner(0, retake=True)
    assert engine.stats[0]["pc_retake"] == 1
    assert engine.stats[0]["pc"] == 1
    assert any(event["type"] == "pc_retake" for event in engine.events)


def test_penalty_stroke_can_be_retaken():
    engine = _engine(5)
    engine.prepare()
    engine._stroke(0, retake=True)
    assert engine.stats[0]["stroke_retake"] == 1
    assert engine.stats[0]["strokes"] == 1
    assert any(event["type"] == "stroke_retake" for event in engine.events)
