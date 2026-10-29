import random

from src.affiliates import (
    advance_mentoring,
    affiliate_overview,
    assign_mentor,
    end_affiliate,
    end_mentoring,
    mentoring_overview,
    request_affiliate,
)
from src.models import GameState
from src.season import new_game


def test_affiliate_overview_has_candidates_and_benefits():
    state = new_game("cd-terrassa", "Affiliate Test", seed=81)
    data = affiliate_overview(state)
    assert data["candidates"]
    assert data["benefits"]
    assert data["scouting"] >= 55
    candidate = data["candidates"][0]
    assert candidate["annual_fee"] > 0
    assert 0 <= candidate["approval_chance"] <= 1


def test_affiliate_request_accepts_and_applies_benefits():
    state = new_game("cd-terrassa", "Affiliate Test", seed=81)
    team = state.user_team
    team.brand_rating = 90
    team.board_confidence = 90
    team.budget = 5_000_000
    candidate = affiliate_overview(state)["candidates"][0]
    before_scouting = team.facilities["scouting"]
    before_youth = team.facilities["youth"]
    result = request_affiliate(state, candidate["id"], rng=random.Random(1))
    assert result["ok"] is True
    assert result["accepted"] is True
    assert state.affiliates
    assert team.facilities["scouting"] == before_scouting + 2
    assert team.facilities["youth"] == before_youth + 1
    assert state.affiliate_history[-1]["accepted"] is True
    affiliate_id = state.affiliates[0]["id"]
    ended = end_affiliate(state, affiliate_id)
    assert ended["ok"] is True
    assert state.affiliates == []
    assert state.affiliate_history[-1]["ended_on"]


def test_affiliate_request_can_be_rejected():
    state = new_game("cd-terrassa", "Affiliate Test", seed=82)
    candidate = affiliate_overview(state)["candidates"][0]
    result = request_affiliate(state, candidate["id"], rng=random.Random(999))
    assert result["ok"] is True
    assert result["accepted"] is False
    assert state.affiliates == []
    assert state.affiliate_history[-1]["accepted"] is False


def test_mentoring_assigns_and_develops_young_player():
    state = new_game("cd-terrassa", "Affiliate Test", seed=83)
    data = mentoring_overview(state)
    assert data["mentors"] and data["mentees"]
    mentor = data["mentors"][0]
    mentee = data["mentees"][0]
    before_relationship = next(
        player.relationship
        for player in list(state.user_team.players) + list(state.user_team.youth)
        if player.id == mentee["id"]
    )
    result = assign_mentor(state, mentor["id"], mentee["id"], "tecnica")
    assert result["ok"] is True
    assert state.user_team.mentoring
    pair = state.user_team.mentoring[0]
    assert pair["mentor_id"] == mentor["id"]
    assert pair["mentee_id"] == mentee["id"]
    player = next(p for p in list(state.user_team.players) + list(state.user_team.youth) if p.id == mentee["id"])
    assert player.relationship >= before_relationship + 3
    for _ in range(4):
        report = advance_mentoring(state)
    assert report["active"] == 1
    assert pair["sessions"] == 4
    assert pair["progress"] > 0
    ended = end_mentoring(state, pair["id"])
    assert ended["ok"] is True
    assert state.user_team.mentoring == []
    assert state.user_team.mentoring_history


def test_mentoring_validation_and_persistence():
    state = new_game("cd-terrassa", "Affiliate Test", seed=84)
    data = mentoring_overview(state)
    mentor = data["mentors"][0]
    mentee = data["mentees"][0]
    assert assign_mentor(state, mentor["id"], mentor["id"], "tecnica")["ok"] is False
    assert assign_mentor(state, mentor["id"], mentee["id"], "no-existe")["ok"] is False
    assert assign_mentor(state, mentor["id"], mentee["id"], "tecnica")["ok"] is True
    state.affiliates = [{"id": "AF-1", "club_id": "x", "club_name": "Filial"}]
    state.affiliate_history = [{"date": state.date, "club_id": "x", "accepted": True}]
    restored = GameState.from_dict(state.to_dict())
    assert restored.affiliates[0]["club_name"] == "Filial"
    assert restored.affiliate_history[0]["accepted"] is True
    assert restored.user_team.mentoring
    assert restored.user_team.mentoring[0]["mentor_id"] == mentor["id"]
