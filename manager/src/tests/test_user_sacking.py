from src.jobs import accept_job_offer, generate_job_offers
from src.managers import process_user_sacking, resign_user
from src.models import GameState
from src.season import new_game


def _crisis(state, pressure=2):
    team = state.user_team
    team.played = 10
    team.points = 0
    team.goals_for = 1
    team.goals_against = 20
    team.board_confidence = 8
    state.user_pressure = pressure
    state.round = 12


def test_user_sacking_after_pressure():
    state = new_game("cd-terrassa", "Sack Test", seed=501)
    _crisis(state)
    result = process_user_sacking(state)
    assert result is not None
    assert result["ok"] is True
    assert state.user_sacked is True
    assert state.user_sacking["kind"] == "sacked"
    assert state.user_sacking["club_id"] == state.club_id
    assert state.user_team.manager_name != "Sack Test"
    assert state.manager_changes[-1]["type"] == "user_sacked"


def test_user_sacking_requires_repeated_pressure():
    state = new_game("cd-terrassa", "Sack Test", seed=502)
    _crisis(state, pressure=0)
    result = process_user_sacking(state)
    assert result is None
    assert state.user_sacked is False
    assert state.user_pressure == 1


def test_user_sacking_persists():
    state = new_game("cd-terrassa", "Sack Test", seed=503)
    _crisis(state)
    process_user_sacking(state)
    restored = GameState.from_dict(state.to_dict())
    assert restored.user_sacked is True
    assert restored.user_sacking["reason"]
    assert restored.user_pressure == 0
    assert restored.manager_changes[-1]["type"] == "user_sacked"


def test_resign_user_sets_sacked():
    state = new_game("cd-terrassa", "Sack Test", seed=504)
    result = resign_user(state)
    assert result["ok"] is True
    assert state.user_sacked is True
    assert state.user_sacking["kind"] == "resigned"
    assert state.manager_changes[-1]["type"] == "resigned"


def test_accept_job_after_sacking_clears_flag():
    state = new_game("cd-terrassa", "Sack Test", seed=505)
    resign_user(state)
    offers = generate_job_offers(state, force=True, include_cross_league=False)
    target = next(offer for offer in offers if not offer["cross_league"])
    result = accept_job_offer(state, target["id"])
    assert result["ok"] is True
    assert state.user_sacked is False
    assert state.user_sacking == {}
    assert state.user_team.manager_name == "Sack Test"
    assert state.user_team.id == target["club_id"]


def test_cross_league_offer_blocked_while_sacked():
    state = new_game("cd-terrassa", "Sack Test", seed=506)
    resign_user(state)
    offers = generate_job_offers(state, force=True, include_cross_league=True)
    cross = next((offer for offer in offers if offer["cross_league"]), None)
    assert cross is not None
    result = accept_job_offer(state, cross["id"])
    assert result["ok"] is False
    assert "Sin club" in result["message"]
    assert state.user_sacked is True
