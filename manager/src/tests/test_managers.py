from src.jobs import accept_job_offer, generate_job_offers
from src.managers import manager_changes_overview, process_manager_changes
from src.models import GameState
from src.season import new_game
from src.vacancies import vacancy_overview


def _bottom_team(state, team_id="atletic-terrassa"):
    team = state.teams[team_id]
    team.played = 10
    team.points = 0
    team.goals_for = 1
    team.goals_against = 20
    team.manager_pressure = 3
    team.manager_since_round = 0
    state.round = 12
    return team


def test_manager_names_initialized_from_staff_or_interim():
    state = new_game("cd-terrassa", "Manager Test", seed=301)
    assert state.user_team.manager_name == "Manager Test"
    assert state.teams["sardinero"].manager_name
    assert state.teams["sardinero"].manager_name != "Manager Test"


def test_bottom_team_pressure_leads_to_sack():
    state = new_game("cd-terrassa", "Manager Test", seed=302)
    team = _bottom_team(state)
    old_name = team.manager_name
    changes = process_manager_changes(state)
    assert changes
    assert team.manager_name != old_name
    assert team.manager_pressure == 0
    assert team.manager_since_round == state.round
    change = next(item for item in changes if item["club_id"] == team.id)
    assert change["type"] == "sack"
    assert change["old_manager"] == old_name
    assert change["new_manager"] == team.manager_name
    assert any("Cambio de entrenador" in item["subject"] for item in state.inbox[-5:])


def test_sacked_team_appears_as_vacancy_and_history():
    state = new_game("cd-terrassa", "Manager Test", seed=303)
    team = _bottom_team(state)
    process_manager_changes(state)
    data = vacancy_overview(state)
    assert any(row["club_id"] == team.id for row in data["pool"])
    assert data["changes"]
    assert data["summary"]["changes"] == len(state.manager_changes)
    assert manager_changes_overview(state)[0]["club_id"] == team.id


def test_manager_changes_persist():
    state = new_game("cd-terrassa", "Manager Test", seed=304)
    team = _bottom_team(state)
    process_manager_changes(state)
    restored = GameState.from_dict(state.to_dict())
    assert restored.teams[team.id].manager_name == team.manager_name
    assert restored.manager_changes[-1]["club_id"] == team.id
    assert restored.teams[team.id].manager_pressure == 0


def test_user_team_is_not_automatically_sacked():
    state = new_game("cd-terrassa", "Manager Test", seed=305)
    user = state.user_team
    user.played = 10
    user.points = 0
    user.goals_for = 1
    user.goals_against = 20
    user.manager_pressure = 5
    state.round = 12
    process_manager_changes(state)
    assert user.manager_name == "Manager Test"
    assert all(change["club_id"] != user.id for change in state.manager_changes)


def test_job_acceptance_updates_manager_names():
    state = new_game("cd-terrassa", "Manager Test", seed=306)
    offers = generate_job_offers(state, force=True, include_cross_league=False)
    target = next(offer for offer in offers if not offer["cross_league"])
    old_team = state.user_team
    old_manager = old_team.manager_name
    result = accept_job_offer(state, target["id"])
    assert result["ok"] is True
    assert state.user_team.manager_name == "Manager Test"
    assert state.teams[old_team.id].manager_name != old_manager
    kinds = {change["type"] for change in state.manager_changes}
    assert {"user_left", "user_hired"} <= kinds
