import random

from src.data_loader import load_teams
from src.match_engine import MatchEngine


def _engine(seed: int = 1) -> MatchEngine:
    teams, _, _ = load_teams()
    return MatchEngine(teams["cd-terrassa"], teams["sardinero"], random.Random(seed), detailed=True)


def test_advantage_failure_brings_back_free_hit():
    engine = _engine()
    engine.prepare()
    engine.zone = "attacking_23"
    engine._foul(0, foul_type="physical", advantage=True)
    assert engine.pending_advantage is not None
    engine.possession = 0
    engine._resolve_advantage()
    assert engine.stats[1]["advantage_failed"] == 1
    assert engine.possession == 1
    assert engine.zone == "attacking_23"
    assert any(event["type"] == "advantage_failed" for event in engine.events)
    assert any(event["type"] == "free_hit" for event in engine.events)


def test_advantage_failure_in_circle_awards_penalty_corner():
    engine = _engine(2)
    engine.prepare()
    engine.zone = "circle"
    engine._foul(0, foul_type="physical", advantage=True)
    assert engine.pending_advantage is not None
    engine.possession = 0
    engine._resolve_advantage()
    assert engine.stats[1]["advantage_failed"] == 1
    assert engine.stats[1]["pc"] == 1
    assert any(event["type"] == "advantage_failed" for event in engine.events)
    assert any(event["type"] == "pc" for event in engine.events)


def test_advantage_success_clears_pending_without_failure():
    engine = _engine(3)
    engine.prepare()
    engine.zone = "attacking_23"
    engine._foul(0, foul_type="physical", advantage=True)
    assert engine.pending_advantage is not None
    engine._shot(1)
    assert engine.pending_advantage is None
    assert engine.stats[1]["advantage_failed"] == 0
