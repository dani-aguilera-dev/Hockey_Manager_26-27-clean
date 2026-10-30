from src.models import GameState
from src.season import new_game
from src.trials import advance_trials, end_trial, invite_trial, trial_overview


def test_trial_overview_has_candidates_and_empty_state():
    state = new_game("cd-terrassa", "Trials Test", seed=251)
    data = trial_overview(state)
    assert data["candidates"]
    assert data["active"] == []
    assert data["history"] == []
    assert data["summary"]["max_active"] == 3


def test_invite_and_end_trial_generates_report():
    state = new_game("cd-terrassa", "Trials Test", seed=252)
    candidate = trial_overview(state)["candidates"][0]
    invited = invite_trial(state, candidate["id"])
    assert invited["ok"] is True
    active = trial_overview(state)["active"]
    assert len(active) == 1
    trial_id = active[0]["trial_id"]
    ended = end_trial(state, trial_id)
    assert ended["ok"] is True
    assert ended["trial"]["report"]["score"] >= 0
    assert ended["trial"]["report"]["recommendation"] in ("fichar", "seguir", "descartar")
    assert state.trial_history
    assert trial_overview(state)["active"] == []
    restored = GameState.from_dict(state.to_dict())
    assert restored.trial_history[-1]["player_name"] == candidate["name"]
    assert restored.trial_history[-1]["report"]["summary"]


def test_trial_limits_and_validation():
    state = new_game("cd-terrassa", "Trials Test", seed=253)
    candidates = trial_overview(state)["candidates"][:4]
    for candidate in candidates[:3]:
        assert invite_trial(state, candidate["id"])["ok"] is True
    assert invite_trial(state, candidates[3]["id"])["ok"] is False
    assert invite_trial(state, candidates[0]["id"])["ok"] is False
    assert invite_trial(state, "no-existe")["ok"] is False
    own_player = state.user_team.players[0]
    assert invite_trial(state, own_player.id)["ok"] is False
    trial_id = trial_overview(state)["active"][0]["trial_id"]
    assert end_trial(state, trial_id)["ok"] is True
    assert end_trial(state, trial_id)["ok"] is False


def test_advance_trials_completes_when_end_date_arrives():
    state = new_game("cd-terrassa", "Trials Test", seed=254)
    candidate = trial_overview(state)["candidates"][0]
    invite_trial(state, candidate["id"])
    trial = trial_overview(state)["active"][0]
    state.date = trial["end"]
    report = advance_trials(state)
    assert report["completed"] == 1
    assert state.trial_history[-1]["status"] == "completed"
    assert state.trial_history[-1]["report"]["score"] >= 0
