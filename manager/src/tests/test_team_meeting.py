import random

from src.models import GameState
from src.season import new_game
from src.team_meeting import perform_team_meeting, team_meeting_context


def test_team_meeting_context_has_dynamics_and_options():
    state = new_game("cd-terrassa", "Meeting Test", seed=111)
    data = team_meeting_context(state)
    assert data["dynamics"]["morale"] == state.user_team.morale
    assert data["meeting_types"]
    assert data["tones"]
    assert data["topics"]
    assert data["promise_types"]
    assert data["players"]
    assert data["recommended_type"] in {item["id"] for item in data["meeting_types"]}


def test_team_meeting_applies_effects_and_history():
    state = new_game("cd-terrassa", "Meeting Test", seed=112)
    team = state.user_team
    before_morale = team.morale
    result = perform_team_meeting(
        state,
        "pre_match",
        "motivadora",
        ["objetivo", "vestuario"],
        rng=random.Random(1),
    )
    assert result["ok"] is True
    assert result["success"] is True
    assert team.morale > before_morale
    assert team.team_meetings
    assert team.team_meetings[-1]["tone"] == "motivadora"
    assert result["effects"]["morale"] > 0


def test_team_meeting_creates_persistent_promise():
    state = new_game("cd-terrassa", "Meeting Test", seed=113)
    data = team_meeting_context(state)
    player = data["players"][0]
    result = perform_team_meeting(
        state,
        "pre_match",
        "honesta",
        ["minutos"],
        player["id"],
        "minutes",
        rng=random.Random(1),
    )
    assert result["ok"] is True
    assert result["promise"]["type"] == "minutes"
    target = next(p for p in state.user_team.squad if p.id == player["id"])
    assert target.promises[-1]["status"] == "open"
    assert target.promises[-1]["target_apps"] == target.apps + 3
    restored = GameState.from_dict(state.to_dict())
    assert restored.user_team.team_meetings
    restored_player = next(p for p in restored.user_team.squad if p.id == player["id"])
    assert restored_player.promises[-1]["type"] == "minutes"


def test_team_meeting_validation_and_failure():
    state = new_game("cd-terrassa", "Meeting Test", seed=114)
    assert perform_team_meeting(state, "no-existe", "serena", [])["ok"] is False
    assert perform_team_meeting(state, "pre_match", "no-existe", [])["ok"] is False
    assert perform_team_meeting(state, "pre_match", "serena", ["objetivo", "vestuario", "minutos", "aficion"])["ok"] is False
    assert perform_team_meeting(state, "pre_match", "serena", [], "no-existe", "minutes")["ok"] is False
    result = perform_team_meeting(state, "pre_match", "exigente", ["disciplina"], rng=random.Random(999))
    assert result["ok"] is True
    assert result["success"] is False
    assert result["effects"]["morale"] < 0
