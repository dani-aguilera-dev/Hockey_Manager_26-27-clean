import random

from src.data_loader import load_teams
from src.match_engine import MatchEngine


def _engine(seed: int = 1) -> MatchEngine:
    teams, _, _ = load_teams()
    return MatchEngine(teams["cd-terrassa"], teams["sardinero"], random.Random(seed), detailed=True)


def test_live_protest_respectful_is_one_per_team():
    engine = _engine()
    engine.prepare()
    result = engine.protest_decision(0, "respetuosa")
    assert result["ok"] is True
    assert result["card"] is False
    assert engine.protest_used[0] is True
    assert engine.stats[0]["dissent"] == 1
    again = engine.protest_decision(0, "respetuosa")
    assert again["ok"] is False


def test_live_protest_vehement_can_draw_card():
    engine = _engine(2)
    engine.prepare()
    result = engine.protest_decision(1, "vehemente")
    assert result["ok"] is True
    assert result["card"] is True
    assert engine.cards
    assert engine.stats[1]["dissent"] == 1
