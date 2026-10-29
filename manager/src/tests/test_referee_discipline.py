import random

from src.data_loader import load_teams
from src.match_engine import MatchEngine


def _engine(seed: int = 1) -> MatchEngine:
    teams, _, _ = load_teams()
    return MatchEngine(teams["cd-terrassa"], teams["sardinero"], random.Random(seed), detailed=True)


def test_protest_warning_records_dissent_without_card():
    engine = _engine()
    engine.prepare()
    player = engine._lineup(0)[0]
    before_cards = len(engine.cards)
    result = engine._protest(0, player, "card", "warning")
    assert result["ok"] is True
    assert engine.stats[0]["dissent"] == 1
    assert len(engine.cards) == before_cards
    assert any(event["type"] == "protest" for event in engine.events)


def test_protest_can_draw_card():
    engine = _engine(2)
    engine.prepare()
    player = engine._lineup(0)[0]
    result = engine._protest(0, player, "card", "card")
    assert result["ok"] is True
    assert engine.cards
    assert any(event["type"] == "protest" for event in engine.events)


def test_unsportsmanlike_delay_and_simulation():
    engine = _engine(3)
    engine.prepare()
    player = engine._lineup(0)[0]
    engine._unsportsmanlike(0, "delay", player, card=False)
    assert engine.stats[0]["unsportsmanlike"] == 1
    before_cards = len(engine.cards)
    engine._unsportsmanlike(0, "simulation", player, card=True)
    assert len(engine.cards) > before_cards
    assert any(event["type"] == "unsportsmanlike" for event in engine.events)


def test_added_time_is_computed_and_in_result():
    engine = _engine(4)
    engine.events.extend(
        [
            {"type": "injury", "quarter": 1, "minute": 5, "text": "lesión"},
            {"type": "card", "quarter": 1, "minute": 6, "text": "tarjeta"},
            {"type": "review", "quarter": 1, "minute": 7, "text": "revisión"},
        ]
    )
    assert engine.compute_added_time(1) > 0
    result = engine.simulate()
    assert result.added_time
    assert any(event["type"] == "added_time" for event in result.events)
