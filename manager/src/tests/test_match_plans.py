import random

from src.data_loader import load_teams
from src.match_engine import MatchEngine
from src.match_plans import (
    create_match_plan,
    delete_match_plan,
    match_plans_overview,
    update_match_plan,
)
from src.models import GameState
from src.season import new_game

PLAN = {
    "id": "MP-TEST",
    "name": "Cerrar el partido",
    "situation": "leading",
    "from_minute": 45,
    "enabled": True,
    "instructions": {"mentality": "defensiva", "press": "baja", "block": "bajo"},
}


def test_match_plans_overview_has_options_and_empty_state():
    state = new_game("cd-terrassa", "Plans Test", seed=211)
    data = match_plans_overview(state)
    assert data["plans"] == []
    assert data["summary"]["total"] == 0
    assert data["situations"]
    assert data["fields"]
    assert data["max_plans"] > 0


def test_create_update_delete_match_plan_and_persist():
    state = new_game("cd-terrassa", "Plans Test", seed=212)
    created = create_match_plan(
        state,
        "Cerrar el partido",
        "leading",
        45,
        {"mentality": "defensiva", "press": "baja"},
    )
    assert created["ok"] is True
    plan_id = created["plan"]["id"]
    assert state.match_plans[0]["instructions"]["mentality"] == "defensiva"
    updated = update_match_plan(
        state,
        plan_id,
        "Cerrar el partido",
        "leading",
        50,
        {"mentality": "muy_defensiva"},
        False,
    )
    assert updated["ok"] is True
    assert updated["plan"]["from_minute"] == 50
    assert updated["plan"]["enabled"] is False
    restored = GameState.from_dict(state.to_dict())
    assert restored.match_plans[0]["from_minute"] == 50
    assert restored.match_plans[0]["enabled"] is False
    assert delete_match_plan(state, plan_id)["ok"] is True
    assert state.match_plans == []


def test_match_plan_validation_and_limit():
    state = new_game("cd-terrassa", "Plans Test", seed=213)
    assert create_match_plan(state, "", "leading", 45, {"mentality": "defensiva"})["ok"] is False
    assert create_match_plan(state, "Plan", "no-existe", 45, {"mentality": "defensiva"})["ok"] is False
    assert create_match_plan(state, "Plan", "leading", 99, {"mentality": "defensiva"})["ok"] is False
    assert create_match_plan(state, "Plan", "leading", 45, {})["ok"] is False
    for index in range(12):
        assert create_match_plan(state, f"Plan {index}", "drawing", 10, {"tempo": "rapido"})["ok"] is True
    assert create_match_plan(state, "Plan extra", "drawing", 10, {"tempo": "rapido"})["ok"] is False


def _engine(plan_side=0, plans=None, seed=1):
    teams, _, _ = load_teams()
    return MatchEngine(
        teams["cd-terrassa"],
        teams["sardinero"],
        random.Random(seed),
        detailed=True,
        match_plans=plans or [],
        plan_side=plan_side,
    )


def test_engine_applies_plan_only_when_situation_and_minute_match():
    base = _engine(plans=[])
    base.score = [1, 0]
    base.minute = 50
    base_attack, base_defense = base._attack_defense()[0], base._attack_defense()[1]

    engine = _engine(plans=[PLAN])
    engine.score = [1, 0]
    engine.minute = 50
    attack, defense = engine._attack_defense()[0], engine._attack_defense()[1]
    assert attack < base_attack
    assert defense > base_defense
    assert engine.plan_effect_cache["plans"] == ["MP-TEST"]
    assert sum(1 for event in engine.events if event["type"] == "match_plan") == 1
    engine._attack_defense()
    assert sum(1 for event in engine.events if event["type"] == "match_plan") == 1

    engine.score = [0, 1]
    engine._attack_defense()
    assert engine.plan_effect_cache["plans"] == []

    engine.score = [1, 0]
    engine.minute = 20
    engine._attack_defense()
    assert engine.plan_effect_cache["plans"] == []


def test_engine_ignores_disabled_plan_and_other_side():
    disabled = {**PLAN, "enabled": False}
    engine = _engine(plans=[disabled])
    engine.score = [1, 0]
    engine.minute = 50
    engine._attack_defense()
    assert engine.plan_effect_cache["plans"] == []

    other = _engine(plan_side=1, plans=[PLAN])
    other.score = [1, 0]
    other.minute = 50
    other._attack_defense()
    assert other.plan_effect_cache["plans"] == []
