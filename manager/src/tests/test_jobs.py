from src.jobs import (
    accept_job_offer,
    generate_job_offers,
    job_security_overview,
    reject_job_offer,
)
from src.models import GameState
from src.season import new_game


def test_job_security_overview_has_status_and_contract():
    state = new_game("cd-terrassa", "Jobs Test", seed=241)
    data = job_security_overview(state)
    assert data["club"]["name"] == state.user_team.name
    assert data["security"]["status"] in ("estable", "observacion", "peligro", "ultimatum")
    assert data["contract"]["club_id"] == state.club_id
    assert data["contract"]["salary"] > 0
    assert data["offers"] == []


def test_generate_job_offers_same_league_and_excludes_user():
    state = new_game("cd-terrassa", "Jobs Test", seed=242)
    offers = generate_job_offers(state)
    assert offers
    assert all(offer["club_id"] != state.club_id for offer in offers)
    assert all(offer["league"] == state.competition for offer in offers)
    assert all(offer["salary"] > 0 and offer["years"] >= 2 for offer in offers)
    again = generate_job_offers(state)
    assert len(again) == len(offers)


def test_accept_job_offer_switches_club_and_persists():
    state = new_game("cd-terrassa", "Jobs Test", seed=243)
    offers = generate_job_offers(state)
    target = offers[0]
    old_club = state.user_team.name
    result = accept_job_offer(state, target["id"])
    assert result["ok"] is True
    assert state.club_id == target["club_id"]
    assert state.user_team.name == target["club_name"]
    assert state.manager_contract["club_id"] == target["club_id"]
    assert state.job_offer_history[-1]["type"] == "accepted"
    assert state.job_offer_history[-1]["from_club"] == old_club
    assert state.manual_lineup == []
    restored = GameState.from_dict(state.to_dict())
    assert restored.club_id == target["club_id"]
    assert restored.manager_contract["club_id"] == target["club_id"]
    assert restored.job_offer_history[-1]["to_club"] == target["club_name"]


def test_reject_job_offer_records_history():
    state = new_game("cd-terrassa", "Jobs Test", seed=244)
    offers = generate_job_offers(state)
    target = offers[0]
    result = reject_job_offer(state, target["id"])
    assert result["ok"] is True
    assert state.job_offer_history[-1]["type"] == "rejected"
    assert state.job_offer_history[-1]["to_club"] == target["club_name"]
    open_offers = job_security_overview(state)["offers"]
    assert target["id"] not in {offer["id"] for offer in open_offers}


def test_job_offer_validation_and_same_league_guard():
    state = new_game("cd-terrassa", "Jobs Test", seed=245)
    assert accept_job_offer(state, "no-existe")["ok"] is False
    assert reject_job_offer(state, "no-existe")["ok"] is False
    offers = generate_job_offers(state)
    target = offers[0]
    assert accept_job_offer(state, target["id"])["ok"] is True
    assert accept_job_offer(state, target["id"])["ok"] is False
    other_league = next(
        team for team in state.teams.values()
        if team.league != state.competition and len(team.squad) >= 14
    )
    state.job_offers.append(
        {
            "id": "JOB-OTHER",
            "club_id": other_league.id,
            "status": "open",
            "salary": 50000,
            "years": 2,
            "created": state.date,
            "expires": state.date,
        }
    )
    assert accept_job_offer(state, "JOB-OTHER")["ok"] is False
