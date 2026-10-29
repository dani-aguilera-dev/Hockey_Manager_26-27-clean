import random

from src.data_loader import load_teams
from src.match_engine import MatchEngine


def _engine(seed: int = 1) -> MatchEngine:
    teams, _, _ = load_teams()
    return MatchEngine(teams["cd-terrassa"], teams["sardinero"], random.Random(seed), detailed=True)


def test_advantage_keeps_possession_and_is_recorded():
    engine = _engine()
    engine.zone = "attacking_23"
    engine._foul(0, foul_type="physical", advantage=True)
    assert engine.possession == 1
    assert engine.stats[1]["advantage"] == 1
    assert any(event["type"] == "advantage" for event in engine.events)
    assert not any(event["type"] == "free_hit" for event in engine.events)


def test_dangerous_play_is_recorded_and_can_award_pc():
    engine = _engine(2)
    engine.zone = "circle"
    engine._foul(0, foul_type="dangerous", advantage=False, pc_decision="pc")
    assert engine.stats[0]["dangerous_play"] == 1
    assert any(event["type"] == "dangerous_play" for event in engine.events)
    assert engine.stats[1]["pc"] >= 1


def test_five_meters_is_enforced_on_free_hit():
    engine = _engine(3)
    engine.zone = "middle"
    engine._foul(0, foul_type="physical", advantage=False, distance_call=True)
    assert engine.stats[1]["distance_5m"] == 1
    assert any(event["type"] == "distance_5m" for event in engine.events)


def test_pc_can_be_denied_by_referee():
    engine = _engine(4)
    engine.zone = "circle"
    engine._foul(0, foul_type="physical", advantage=False, pc_decision="denied")
    assert engine.stats[1]["pc_denied"] == 1
    assert engine.stats[1]["pc"] == 0
    assert any(event["type"] == "pc_decision" for event in engine.events)


def test_dangerous_play_can_upgrade_pc_to_stroke():
    engine = _engine(5)
    engine.zone = "circle"
    engine._foul(0, foul_type="dangerous", advantage=False, pc_decision="stroke")
    assert engine.stats[1]["stroke_awarded"] == 1
    assert engine.stats[1]["strokes"] >= 1
    assert any(event["type"] == "stroke" for event in engine.events)
