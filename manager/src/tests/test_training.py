import random

from src.data_loader import load_teams
from src.season import ensure_ai_training, ensure_week_training, new_game, play_round
from src.training import PLAN_PRESETS, SESSION_TYPES, apply_training_plan, auto_plan


def test_auto_plan_and_apply():
    teams, _, _ = load_teams()
    team = teams["cd-terrassa"]
    opponent = teams["club-egara"]
    plan = auto_plan(team, opponent, random.Random(1))
    assert len(plan) == 5
    assert all(s in SESSION_TYPES for s in plan)
    report = apply_training_plan(team, plan, opponent, random.Random(2))
    assert report["plan"] == plan
    assert report["fatigue_after"] >= 0
    assert report["cohesion"] >= 1
    assert "gains" in report and "injuries" in report
    assert team.prep_bonus >= 0


def test_tired_team_gets_recovery_plan():
    teams, _, _ = load_teams()
    team = teams["cd-terrassa"]
    for p in team.players:
        p.fatigue = 85
    plan = auto_plan(team, teams["club-egara"], random.Random(3))
    assert plan == PLAN_PRESETS["recuperacion"]
    report = apply_training_plan(team, plan, None, random.Random(4))
    assert report["fatigue_after"] < report["fatigue_before"]


def test_ensure_week_training_and_reset():
    state = new_game("cd-terrassa", "Test", seed=101)
    report = ensure_week_training(state)
    assert report is not None
    assert state.week_trained
    assert len(state.weekly_plan) == 5
    assert state.user_team.prep_bonus > 0
    assert ensure_week_training(state) is None
    play_round(state, None, "equilibrado")
    assert state.round == 2
    assert not state.week_trained
    assert state.weekly_plan == []
    assert state.user_team.prep_bonus == 0


def test_ai_training_is_applied_once_per_round():
    state = new_game("cd-terrassa", "Test", seed=102)
    ensure_ai_training(state)
    assert state.ai_training_round == 1
    prepared = [t for t in state.teams.values() if t.league == "DHA" and t.id != state.club_id]
    assert any(t.prep_bonus > 0 for t in prepared)
    before = {t.id: t.prep_bonus for t in prepared}
    ensure_ai_training(state)
    assert {t.id: t.prep_bonus for t in prepared} == before
