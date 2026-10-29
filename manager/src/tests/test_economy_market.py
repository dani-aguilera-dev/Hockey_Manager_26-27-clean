from datetime import date, timedelta
import random

from src.commercial import (
    accept_sponsor_offer,
    brand_score,
    commercial_summary,
    generate_sponsor_offers,
    run_campaign,
    set_ticket_price,
)
from src.finance import sponsor_income
from src.market import (
    accept_incoming_offer,
    daily_transfer_activity,
    hire_market_staff,
    list_player_for_transfer,
    market_players,
    process_pending_transfers,
    staff_market,
)
from src.season import new_game, play_round


def test_commercial_brand_sponsors_and_campaigns():
    state = new_game("cd-terrassa", "Test", seed=941)
    assert brand_score(state) > 0
    offers = generate_sponsor_offers(state, force=True)
    assert offers
    offer = offers[0]
    result = accept_sponsor_offer(state, offer["id"])
    assert result["ok"]
    assert state.user_team.sponsor_deals
    assert sponsor_income(state.user_team) > 0
    assert commercial_summary(state)["brand_score"] > 0
    assert set_ticket_price(state, 22)["ok"]
    assert run_campaign(state, "social")["ok"]
    assert state.user_team.commercial_history


def test_market_is_global_and_has_advanced_filters():
    state = new_game("cd-terrassa", "Test", seed=942)
    pool = market_players(state, limit=2000)
    leagues = {p.league for p in pool}
    assert "DHA" in leagues
    assert "NED" in leagues
    assert "BEL" in leagues
    assert "GER" in leagues
    assert "ENG" in leagues
    assert "ARG" in leagues
    assert "IND" in leagues
    filtered = market_players(
        state,
        limit=100,
        league="NED",
        min_age=22,
        max_age=28,
        min_overall=70,
        attribute="pase",
        min_attribute=70,
    )
    assert filtered
    assert all(p.league == "NED" and 22 <= p.age <= 28 and p.overall >= 70 for p in filtered)
    assert all(p.attributes.get("pase", 0) >= 70 for p in filtered)


def test_transfer_listing_and_simulation_offers():
    state = new_game("cd-terrassa", "Test", seed=943)
    player = state.user_team.players[0]
    assert list_player_for_transfer(state, player.id, True, 100000)["ok"]
    assert player.transfer_listed
    offers = []
    for day in range(1, 8):
        offers += daily_transfer_activity(
            state,
            date(2026, 8, 1) + timedelta(days=day),
            random.Random(2 + day),
        )
        if offers:
            break
    assert offers
    assert offers[0]["from_club_id"] != state.club_id
    assert offers[0]["from_league"]
    assert offers[0]["player_id"] == player.id


def test_closed_market_queues_offer_until_window_opens():
    state = new_game("cd-terrassa", "Test", seed=946)
    state.date = "2026-10-01"
    player = state.user_team.players[0]
    list_player_for_transfer(state, player.id, True, 100000)
    offers = []
    for day in range(1, 8):
        offers = daily_transfer_activity(
            state,
            date(2026, 10, 1) + timedelta(days=day),
            random.Random(30 + day),
        )
        if offers:
            break
    assert offers
    offer = offers[0]
    result = accept_incoming_offer(state, offer["id"])
    assert result["ok"]
    assert result.get("pending")
    assert state.pending_transfers
    assert any(p.id == player.id for p in state.user_team.players)
    state.date = "2027-01-01"
    processed = process_pending_transfers(state)
    assert processed
    assert not any(p.id == player.id for p in state.user_team.players)
    assert not state.pending_transfers


def test_offer_generation_respects_buyer_budget():
    state = new_game("cd-terrassa", "Test", seed=947)
    player = state.user_team.players[0]
    list_player_for_transfer(state, player.id, True, 100000)
    offers = []
    for day in range(1, 12):
        offers = daily_transfer_activity(
            state,
            date(2026, 8, 1) + timedelta(days=day),
            random.Random(70 + day),
        )
        if offers:
            break
    assert offers
    for offer in offers:
        buyer = state.teams[offer["from_club_id"]]
        assert offer["buyer_budget"] >= offer["fee"]
        assert buyer.transfer_budget >= offer["fee"]
    buyer = state.teams[offers[0]["from_club_id"]]
    buyer.transfer_budget = max(0, offers[0]["fee"] - 1)
    result = accept_incoming_offer(state, offers[0]["id"])
    assert not result["ok"]


def test_staff_market_is_fictitious_and_hireable():
    state = new_game("cd-terrassa", "Test", seed=944)
    candidates = staff_market(state, limit=20)
    assert candidates
    assert all(item["source"] == "ficticio" for item in candidates)
    result = hire_market_staff(state, candidates[0]["id"])
    assert "message" in result
    if result["ok"]:
        assert any(member.name == candidates[0]["name"] for member in state.user_team.staff)


def test_commercial_income_flows_through_round_finance():  # noqa: E302
    state = new_game("cd-terrassa", "Test", seed=945)
    offers = generate_sponsor_offers(state, force=True)
    assert accept_sponsor_offer(state, offers[0]["id"])["ok"]
    before = state.user_team.budget
    play_round(state, None, "equilibrado")
    entry = state.user_team.finance_log[-1]
    assert entry["sponsor"] > 0
    assert state.user_team.budget == before + entry["gate"] + entry["sponsor"] - entry["wages"] - entry["travel"]
