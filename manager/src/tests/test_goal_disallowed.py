import random

from src.data_loader import load_teams
from src.match_engine import MatchEngine


class _FixedRng:
    """RNG mínimo para forzar tiros y revisiones deterministas."""

    def __init__(self, value: float):
        self.value = value

    def random(self) -> float:
        return self.value

    def gauss(self, mu: float, sigma: float) -> float:
        return 0.0

    def choice(self, seq):
        return seq[0]

    def choices(self, seq, weights=None, k=1):
        return [seq[0]] * k

    def sample(self, seq, k):
        return list(seq)[:k]


def _engine(seed: int = 1) -> MatchEngine:
    teams, _, _ = load_teams()
    engine = MatchEngine(
        teams["cd-terrassa"], teams["sardinero"], random.Random(seed), detailed=True
    )
    engine.prepare()
    engine.match_date = "2026-09-20"
    return engine


def test_goal_disallowed_for_foot_records_event_and_stats():
    engine = _engine()
    scorer = engine._lineup(0)[0]
    engine._disallowed_goal(0, scorer, None, "open", "foot")
    assert engine.score == [0, 0]
    assert engine.stats[0]["goals"] == 0
    assert engine.stats[0]["goals_disallowed"] == 1
    assert engine.stats[0]["foot_goals_disallowed"] == 1
    assert engine.stats[0]["back_stick_goals_disallowed"] == 0
    assert engine.last_decision["type"] == "goal_disallowed"
    assert engine.last_decision["disallowed_reason"] == "foot"
    assert engine.last_decision["goal"] is False
    event = next(event for event in engine.events if event["type"] == "goal_disallowed")
    assert "pie" in event["text"]
    assert "golpe franco" in event["text"]


def test_goal_disallowed_for_back_stick_via_shot():
    engine = _engine(2)
    engine.rng = _FixedRng(0.0)
    engine.zone = "circle"
    engine._shot(0, "open", offence="back_stick")
    assert engine.score == [0, 0]
    assert engine.stats[0]["goals_disallowed"] == 1
    assert engine.stats[0]["back_stick_goals_disallowed"] == 1
    assert engine.last_decision["disallowed_reason"] == "back_stick"
    event = next(event for event in engine.events if event["type"] == "goal_disallowed")
    assert "revés del stick" in event["text"]


def test_disallowed_goal_only_reviewable_by_attacking_team():
    engine = _engine(3)
    scorer = engine._lineup(0)[0]
    engine._disallowed_goal(0, scorer, None, "open", "foot")
    denied = engine.review_decision(1, "goal_disallowed")
    assert denied["ok"] is False
    assert "anuló" in denied["message"]
    engine.rng = _FixedRng(0.0)
    allowed = engine.review_decision(0, "goal_disallowed")
    assert allowed["ok"] is True


def test_review_overturns_disallowed_goal_and_awards_it():
    engine = _engine(4)
    scorer = engine._lineup(0)[0]
    engine._disallowed_goal(0, scorer, None, "open", "foot")
    engine.rng = _FixedRng(0.0)
    result = engine.review_decision(0, "goal_disallowed")
    assert result["ok"] is True
    assert result["review"]["overturned"] is True
    assert result["score"] == [1, 0]
    assert engine.score == [1, 0]
    assert engine.stats[0]["goals"] == 1
    assert engine.stats[0]["goals_disallowed"] == 1
    assert engine.player_stats[scorer.id]["goals"] == 1
    assert engine.referrals[0] == 1
    assert any(event["type"] == "goal" for event in engine.events)


def test_review_upheld_disallowed_goal_consumes_referral():
    engine = _engine(5)
    scorer = engine._lineup(0)[0]
    engine._disallowed_goal(0, scorer, None, "open", "back_stick")
    engine.rng = _FixedRng(0.99)
    result = engine.review_decision(0, "goal_disallowed")
    assert result["ok"] is True
    assert result["review"]["overturned"] is False
    assert result["score"] == [0, 0]
    assert engine.score == [0, 0]
    assert engine.referrals[0] == 0
    again = engine.review_decision(0, "goal_disallowed")
    assert again["ok"] is False


def test_disallowed_goal_stats_and_event_reach_match_result():
    engine = _engine(6)
    scorer = engine._lineup(0)[0]
    engine._disallowed_goal(0, scorer, None, "open", "foot")
    result = engine.simulate()
    assert result.home_stats["goals_disallowed"] >= 1
    assert result.home_stats["foot_goals_disallowed"] >= 1
    assert any(event["type"] == "goal_disallowed" for event in result.events)
