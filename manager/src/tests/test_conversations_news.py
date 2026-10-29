from datetime import date

from src.conversations import (
    apply_conversation_choice,
    conversation_targets,
    create_conversation,
    player_context,
    topics_for_target,
)
from src.news import awards_for_last_match, news_feed
from src.season import new_game, play_round


def _young_and_veteran(state):
    young = next((p for p in state.user_team.players if p.age <= 21), None)
    veteran = next((p for p in state.user_team.players if p.age >= 29), None)
    return young, veteran


def test_player_topics_are_contextual_by_age():
    state = new_game("cd-terrassa", "Test", seed=921)
    young, veteran = _young_and_veteran(state)
    assert young is not None
    assert veteran is not None
    young_topics = {t["id"] for t in topics_for_target(state, "player", young.id)["topics"]}
    veteran_topics = {t["id"] for t in topics_for_target(state, "player", veteran.id)["topics"]}
    assert "development" in young_topics
    assert "legacy" in veteran_topics
    assert "role" in young_topics and "performance" in young_topics
    young_ctx = player_context(state, young)
    assert young_ctx["age_band"] == "joven"
    assert young_ctx["performance"]


def test_start_and_answer_individual_conversation():
    state = new_game("cd-terrassa", "Test", seed=922)
    young, _ = _young_and_veteran(state)
    assert young is not None
    before = young.relationship
    message = create_conversation(state, date.fromisoformat(state.date), "player", young.id, "development")
    assert message["topic"] == "development"
    assert message["context"]["age_band"] == "joven"
    assert len(message["options"]) >= 4
    result = apply_conversation_choice(state, message, 0)
    assert result["ok"]
    assert result["continued"]
    assert not message["answered"]
    assert len(message["turns"]) >= 3
    final = apply_conversation_choice(state, message, 0)
    assert final["ok"]
    assert message["answered"]
    assert young.relationship > before
    assert any(event.get("type") == "chat" for event in state.daily_events)


def test_staff_conversation_changes_staff_relationship():
    state = new_game("cd-terrassa", "Test", seed=923)
    member = next(m for m in state.user_team.staff if m.role != "head_coach")
    targets = conversation_targets(state)
    assert any(item["target_id"] == member.role for item in targets["staff"])
    before = member.relationship
    message = create_conversation(state, date.fromisoformat(state.date), "staff", member.role, "staff_training")
    assert message["target_type"] == "staff"
    result = apply_conversation_choice(state, message, 0)
    assert result["ok"]
    final = apply_conversation_choice(state, message, 0)
    assert final["ok"]
    assert member.relationship >= before


def test_news_after_match_has_awards_and_related_entities():
    state = new_game("cd-terrassa", "Test", seed=924)
    play_round(state, None, "equilibrado")
    awards = awards_for_last_match(state)
    assert awards
    assert all(award["player_id"] for award in awards)
    items = news_feed(state, 20)
    match_item = next(item for item in items if item["category"] == "Partido")
    assert match_item["awards"]
    assert match_item["player_ids"]
    assert match_item["team_ids"]
    assert match_item["crest_id"]
    assert any(item["category"] == "Rendimiento" for item in items)
    assert any(item["category"] == "Rumor" for item in items)
