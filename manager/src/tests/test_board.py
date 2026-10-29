import random

from src.board import board_overview, request_board
from src.models import TeamState
from src.season import new_game


def test_board_overview_has_vision_facilities_and_requests():
    state = new_game("cd-terrassa", "Board Test", seed=51)
    data = board_overview(state)
    assert data["confidence"] == state.user_team.board_confidence
    assert data["competition"]["position"] >= 1
    assert len(data["vision"]) == 3
    assert len(data["facilities"]) == 6
    assert {item["id"] for item in data["facilities"]} >= {"training", "youth", "medical", "stadium"}
    assert len(data["requests"]) == 7
    assert all("approval_chance" in request for request in data["requests"])
    assert data["board_members"]


def test_board_request_approved_updates_facility_and_budget():
    state = new_game("cd-terrassa", "Board Test", seed=52)
    team = state.user_team
    team.board_confidence = 100
    team.fan_confidence = 100
    team.budget = 10_000_000
    before_budget = team.budget
    before_training = team.facilities["training"]
    result = request_board(state, "training", rng=random.Random(1))
    assert result["ok"] is True
    assert result["approved"] is True
    assert team.budget < before_budget
    assert team.facilities["training"] == before_training + 6
    assert team.board_confidence == 100
    assert team.board_requests[-1]["approved"] is True
    assert team.board_requests[-1]["cost"] == before_budget - team.budget


def test_board_request_rejected_keeps_facility_and_records_history():
    state = new_game("cd-terrassa", "Board Test", seed=53)
    team = state.user_team
    team.board_confidence = 0
    team.fan_confidence = 0
    team.budget = 10_000_000
    before_training = team.facilities["training"]
    result = request_board(state, "training", rng=random.Random(1))
    assert result["ok"] is True
    assert result["approved"] is False
    assert team.facilities["training"] == before_training
    assert team.board_requests[-1]["approved"] is False
    assert team.board_requests[-1]["message"].startswith("La junta rechaza")


def test_board_request_requires_funds_and_valid_id():
    state = new_game("cd-terrassa", "Board Test", seed=54)
    state.user_team.budget = 0
    no_funds = request_board(state, "training", rng=random.Random(1))
    assert no_funds["ok"] is False
    assert "caja" in no_funds["message"].lower()
    unknown = request_board(state, "no-existe", rng=random.Random(1))
    assert unknown["ok"] is False


def test_board_facilities_and_requests_persist_in_team_state():
    state = new_game("cd-terrassa", "Board Test", seed=55)
    team = state.user_team
    team.facilities["training"] = 88
    team.board_requests = [{"date": "2026-08-01", "request_id": "training", "approved": True}]
    restored = TeamState.from_dict(team.to_dict())
    assert restored.facilities["training"] == 88
    assert restored.facilities["youth"] == team.facilities["youth"]
    assert restored.board_requests[-1]["request_id"] == "training"
