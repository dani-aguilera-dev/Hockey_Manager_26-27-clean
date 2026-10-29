from src.scouting import recommendations, scout_context, scout_summary
from src.season import new_game


def test_scout_recommendations_respect_budget_quality_and_needs():
    state = new_game("cd-terrassa", "Test", seed=951)
    context = scout_context(state)
    assert context["scout"]["rating"] >= 50
    assert context["team_quality"] > 0
    assert len(context["needs"]) == 4
    rows = recommendations(state, focus="equilibrado", limit=20)
    assert rows
    budget = state.user_team.transfer_budget
    for row in rows:
        assert row["asking"] <= budget * 1.12
        assert row["score"] >= 0
        assert row["reasons"]


def test_scout_focus_filters_are_applied():
    state = new_game("cd-terrassa", "Test", seed=952)
    young = recommendations(state, focus="joven", max_age=23, position="Medio", limit=20)
    assert young
    assert all(row["age"] <= 23 for row in young)
    assert all(row["need_group"] == "Medio" for row in young)
    summary = scout_summary(state, focus="necesidad")
    assert summary["focus"] == "necesidad"
    assert summary["recommendations"]
