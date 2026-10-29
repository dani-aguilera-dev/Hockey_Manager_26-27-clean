import random

from src import rules
from src.data_loader import load_teams
from src.match_engine import MOMENT_MINUTES, QUARTER_MINUTES, MatchEngine


class FixedRng:
    """RNG mínimo para forzar una tarjeta concreta en los tests."""

    def __init__(self, value: float):
        self.value = value

    def choice(self, items):
        return items[0]

    def choices(self, items, weights=None, k=1):
        return [items[0]]

    def random(self):
        return self.value


def _engine(seed: int = 1) -> MatchEngine:
    teams, _, _ = load_teams()
    return MatchEngine(teams["cd-terrassa"], teams["ud-taburiente"], random.Random(seed), detailed=True)


def test_fih_match_duration_and_card_values():
    assert QUARTER_MINUTES == 15.0
    assert rules.GREEN_CARD_MINUTES == 2
    assert rules.YELLOW_CARD_MINUTES == (5, 10)
    assert rules.suspension_minutes("green") == 2
    assert rules.suspension_minutes("yellow") == 5
    assert rules.suspension_minutes("yellow", serious=True) == 10
    assert rules.suspension_minutes("red") == 0


def test_card_progression_avoids_two_greens_or_two_yellows():
    assert rules.next_card_for_player([]) == "green"
    assert rules.next_card_for_player(["green"]) == "yellow"
    assert rules.next_card_for_player(["yellow"]) == "red"
    assert rules.next_card_for_player(["green", "yellow"]) == "red"


def test_green_card_is_temporary_and_does_not_ban_next_match():
    engine = _engine()
    engine.rng = FixedRng(0.0)
    player = engine._lineup(0)[0]
    engine._card(0)

    assert engine.cards[-1]["type"] == "green"
    assert engine.cards[-1]["duration_minutes"] == 2
    assert player.id in engine.suspensions[0]
    assert player.suspension == 0
    assert len(engine._lineup(0)) == 10

    for _ in range(3):
        engine._tick_suspensions()
    assert player.id not in engine.suspensions[0]
    assert len(engine._lineup(0)) == 11
    assert any(event["type"] == "card_return" for event in engine.events)


def test_yellow_card_is_temporary_and_does_not_ban_next_match():
    engine = _engine()
    engine.rng = FixedRng(0.8)
    player = engine._lineup(0)[0]
    engine._card(0)

    assert engine.cards[-1]["type"] == "yellow"
    assert engine.cards[-1]["duration_minutes"] == 5
    assert player.id in engine.suspensions[0]
    assert player.suspension == 0
    assert len(engine._lineup(0)) == 10

    # Una amarilla no se puede sustituir mientras dura la suspensión.
    ok, _ = engine.manual_substitute(0, player.id, engine._bench(0)[0].id)
    assert not ok


def test_red_card_is_permanent_for_match_and_creates_next_match_ban():
    engine = _engine()
    engine.rng = FixedRng(0.99)
    player = engine._lineup(0)[0]
    engine._card(0)

    assert engine.cards[-1]["type"] == "red"
    assert engine.cards[-1]["rest_of_match"] is True
    assert player.id in engine.red_cards[0]
    assert player.suspension == rules.RED_CARD_NEXT_MATCHES
    assert len(engine._lineup(0)) == 10

    # La roja no vuelve al campo, aunque pasen minutos.
    for _ in range(20):
        engine._tick_suspensions()
    assert player.id in engine.red_cards[0]
    assert len(engine._lineup(0)) == 10


def test_suspension_time_is_playing_time():
    # 5 minutos / 0.9375 minutos por momento = 5.33 momentos.
    assert MOMENT_MINUTES == QUARTER_MINUTES / 16
    assert 5 / MOMENT_MINUTES == 5.333333333333333


def test_injured_player_stays_on_field_until_substituted():
    engine = _engine()
    injured = engine.home_lineup[0]
    injured.injury = 2
    injured.injury_type = "muscular"
    injured.absence_note = "Muscular (moderada)"

    assert injured.id not in {player.id for player in engine._lineup(0)}
    assert injured.id in {player.id for player in engine._field_lineup(0)}

    replacement = engine._bench(0)[0]
    ok, message = engine.manual_substitute(0, injured.id, replacement.id)
    assert ok, message
    assert replacement.id in {player.id for player in engine._lineup(0)}
