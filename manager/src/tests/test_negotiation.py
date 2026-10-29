import random

from src.market import (
    accept_incoming_offer,
    asking_price,
    generate_incoming_offers,
    list_player_for_transfer,
    market_players,
)
from src.negotiation import (
    counter_incoming_offer,
    respond_negotiation,
    start_renewal_negotiation,
    start_transfer_negotiation,
)
from src.persistence import load_game, save_game
from src.season import new_game


def _buy_target(state):
    state.user_team.transfer_budget = 3_000_000
    state.user_team.budget = 3_000_000
    player = min(market_players(state, limit=40, max_value=1_500_000), key=lambda item: item.value)
    return player


def test_transfer_negotiation_counter_and_accept():
    state = new_game("cd-terrassa", "Negotiation", seed=701)
    player = _buy_target(state)
    result = start_transfer_negotiation(state, player.id, 50_000, player.salary * 2, 3)
    assert result["ok"]
    negotiation = result["negotiation"]
    assert negotiation["status"] == "open"
    assert negotiation["ask"]["fee"] > 50_000
    assert negotiation["counter"]["fee"] >= 50_000

    accepted = respond_negotiation(state, negotiation["id"], "accept")
    assert accepted["ok"]
    assert accepted["negotiation"]["status"] == "accepted"
    assert any(item.id == player.id for item in state.user_team.players)


def test_transfer_negotiation_walks_away():
    state = new_game("cd-terrassa", "Negotiation", seed=702)
    player = _buy_target(state)
    result = start_transfer_negotiation(state, player.id, 10_000, player.salary * 2, 3)
    assert result["ok"]
    walked = respond_negotiation(state, result["negotiation"]["id"], "walk")
    assert walked["ok"]
    assert walked["negotiation"]["status"] == "walked"


def test_renewal_negotiation_can_close():
    state = new_game("cd-terrassa", "Negotiation", seed=703)
    player = state.user_team.players[0]
    result = start_renewal_negotiation(state, player.id, max(5000, player.salary // 2), 3)
    assert result["ok"]
    negotiation = result["negotiation"]
    assert negotiation["kind"] == "renew"
    if negotiation["status"] == "open":
        accepted = respond_negotiation(state, negotiation["id"], "accept")
        assert accepted["ok"]
        assert accepted["negotiation"]["status"] == "accepted"
    assert player.contract_until.endswith("-06-30")


def test_incoming_offer_can_be_countered():
    state = new_game("cd-terrassa", "Negotiation", seed=704)
    player = state.user_team.players[0]
    list_player_for_transfer(state, player.id, True, 100_000)
    offers = []
    for attempt in range(20):
        state.transfer_offers = []
        state.market_offers_date = None
        offers = generate_incoming_offers(state, random.Random(704 + attempt))
        if offers:
            break
    assert offers
    offer = offers[0]
    result = counter_incoming_offer(state, offer["id"], offer["fee"] + 5_000)
    assert result["ok"]
    if result.get("accepted"):
        assert not any(item.id == player.id for item in state.user_team.players) or state.pending_transfers
    else:
        assert result["counter"]["fee"] > 0


def test_negotiation_state_roundtrip():
    state = new_game("cd-terrassa", "Negotiation", seed=705)
    player = _buy_target(state)
    result = start_transfer_negotiation(state, player.id, 25_000, player.salary * 2, 3)
    assert result["ok"]
    with __import__("tempfile").TemporaryDirectory() as td:
        from pathlib import Path

        db = Path(td) / "negotiation.db"
        save_game(state, "negotiation", db)
        loaded = load_game("negotiation", db)
        assert loaded.negotiations
        assert loaded.negotiations[-1]["player_id"] == player.id
