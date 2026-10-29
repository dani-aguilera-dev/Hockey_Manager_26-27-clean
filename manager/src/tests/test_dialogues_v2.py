from datetime import date, timedelta

from src.conversations import (
    apply_conversation_choice,
    check_promises,
    create_conversation,
    player_context,
    topics_for_target,
)
from src.season import new_game


def test_conversation_has_contextual_opening_and_two_turns():
    state = new_game("cd-terrassa", "Dialogue", seed=801)
    player = next(p for p in state.user_team.players if p.apps == 0)
    player.apps = 4
    player.form = 7.3
    message = create_conversation(state, date.fromisoformat(state.date), "player", player.id, "role")
    assert "Llevo 4 partidos" in message["text"]
    assert message["stage"] == 0
    assert len(message["turns"]) == 1
    first = apply_conversation_choice(state, message, 0)
    assert first["continued"]
    assert message["stage"] == 1
    assert len(message["turns"]) >= 3
    assert not message["answered"]
    final = apply_conversation_choice(state, message, 0)
    assert final["ok"]
    assert message["answered"]
    assert message["status"] == "closed"


def test_recent_topic_is_marked_after_conversation():
    state = new_game("cd-terrassa", "Dialogue", seed=802)
    player = state.user_team.players[0]
    message = create_conversation(state, date.fromisoformat(state.date), "player", player.id, "role")
    apply_conversation_choice(state, message, 0)
    apply_conversation_choice(state, message, 0)
    topics = topics_for_target(state, "player", player.id)["topics"]
    role = next(topic for topic in topics if topic["id"] == "role")
    assert role["recent"] is True


def test_promise_is_created_and_checked():
    state = new_game("cd-terrassa", "Dialogue", seed=803)
    player = next(p for p in state.user_team.players if p.age <= 21)
    message = create_conversation(state, date.fromisoformat(state.date), "player", player.id, "development")
    # La segunda opción de desarrollo promete minutos.
    first = apply_conversation_choice(state, message, 1)
    assert first["continued"]
    assert player.promises
    promise = player.promises[-1]
    assert promise["type"] == "minutes"
    assert promise["status"] == "open"
    final = apply_conversation_choice(state, message, 0)
    assert final["ok"]
    # No ha jugado los partidos prometidos: la promesa se rompe.
    later = date.fromisoformat(promise["due"]) + timedelta(days=1)
    checked = check_promises(state, later)
    assert checked
    assert promise["status"] == "broken"
    assert any("promesa" in event["body"].lower() for event in state.daily_events)


def test_promise_can_be_kept():
    state = new_game("cd-terrassa", "Dialogue", seed=804)
    player = next(p for p in state.user_team.players if p.age <= 21)
    message = create_conversation(state, date.fromisoformat(state.date), "player", player.id, "development")
    apply_conversation_choice(state, message, 1)
    promise = player.promises[-1]
    player.apps = int(promise["target_apps"])
    apply_conversation_choice(state, message, 0)
    later = date.fromisoformat(promise["due"]) + timedelta(days=1)
    check_promises(state, later)
    assert promise["status"] == "kept"
