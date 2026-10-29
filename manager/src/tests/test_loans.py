import random

from src.loans import loan_overview, offer_loan_out, request_loan_in, return_loans
from src.models import GameState, PlayerState
from src.season import new_game


def test_loan_overview_lists_targets_outgoing_and_terms():
    state = new_game("cd-terrassa", "Loan Test", seed=61)
    data = loan_overview(state)
    assert data["targets"]
    assert data["outgoing"]
    assert data["playing_times"]
    assert data["window"] in ("verano", "invierno", "cerrado")
    target = data["targets"][0]
    assert target["team_id"] != state.club_id
    assert target["wage_share_options"] == [0, 25, 50, 75, 100]
    assert target["playing_time_options"]


def test_loan_in_moves_player_and_returns_to_parent():
    state = new_game("cd-terrassa", "Loan Test", seed=61)
    target = loan_overview(state)["targets"][0]
    owner = state.teams[target["team_id"]]
    result = request_loan_in(
        state,
        target["id"],
        wage_share=100,
        playing_time="titular",
        rng=random.Random(1),
    )
    assert result["ok"] is True
    assert result["accepted"] is True
    player = next(p for p in state.user_team.players if p.id == target["id"])
    assert player.loan["parent_club_id"] == owner.id
    assert player.loan["loan_club_id"] == state.club_id
    assert target["id"] not in [p.id for p in owner.players]
    assert state.loans and state.loan_history[-1]["accepted"] is True
    returned = return_loans(state)
    assert returned
    assert player in owner.players
    assert player.loan == {}
    assert state.loans == []
    assert state.loan_history[-1]["returned_on"]


def test_loan_out_moves_player_to_borrower_and_returns():
    state = new_game("cd-terrassa", "Loan Test", seed=62)
    candidate = loan_overview(state)["outgoing"][0]
    club = candidate["interested_clubs"][0]
    result = offer_loan_out(
        state,
        candidate["id"],
        club["id"],
        wage_share=100,
        playing_time="titular",
        rng=random.Random(1),
    )
    assert result["ok"] is True
    assert result["accepted"] is True
    player = next(p for p in state.teams[club["id"]].players if p.id == candidate["id"])
    assert player.loan["parent_club_id"] == state.club_id
    assert candidate["id"] not in [p.id for p in state.user_team.players]
    return_loans(state)
    assert player in state.user_team.players
    assert player.loan == {}


def test_rejected_loan_keeps_player_and_records_history():
    state = new_game("cd-terrassa", "Loan Test", seed=63)
    target = loan_overview(state)["targets"][0]
    owner = state.teams[target["team_id"]]
    result = request_loan_in(state, target["id"], wage_share=0, playing_time="suplente", rng=random.Random(999))
    assert result["ok"] is True
    assert result["accepted"] is False
    assert target["id"] in [p.id for p in owner.players]
    assert state.loans == []
    assert state.loan_history[-1]["accepted"] is False


def test_loan_validation_and_persistence():
    state = new_game("cd-terrassa", "Loan Test", seed=64)
    own_player = state.user_team.players[0]
    assert request_loan_in(state, own_player.id, rng=random.Random(1))["ok"] is False
    assert offer_loan_out(state, own_player.id, "no-existe", rng=random.Random(1))["ok"] is False
    state.loans = [{"id": "LN-1", "player_id": own_player.id}]
    state.loan_history = [{"date": state.date, "player_id": own_player.id, "accepted": True}]
    own_player.loan = {"parent_club_id": "x", "loan_club_id": state.club_id}
    restored = GameState.from_dict(state.to_dict())
    assert restored.loans == state.loans
    assert restored.loan_history == state.loan_history
    restored_player = next(p for p in restored.user_team.players if p.id == own_player.id)
    assert restored_player.loan["parent_club_id"] == "x"
    assert PlayerState.from_dict(own_player.to_dict()).loan["loan_club_id"] == state.club_id
