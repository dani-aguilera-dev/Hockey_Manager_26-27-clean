import random
from datetime import date

from src.daily import _legal_event
from src.press import answer_press, press_context, press_questions
from src.season import new_game


def test_off_field_incident_creates_absence_and_conversation():
    state = new_game("cd-terrassa", "Test", seed=910)
    before_chats = len(state.chat_messages)
    _legal_event(state, date.fromisoformat(state.date), random.Random(7))
    assert len(state.chat_messages) > before_chats
    message = state.chat_messages[-1]
    player = next(p for p in state.user_team.players if p.id == message["player_id"])
    assert player.suspension > 0
    assert player.absence_label == "Citación judicial"
    assert len(state.chat_messages) > before_chats
    assert any(event["category"] == "Sucesos" for event in state.daily_events)


def test_press_includes_rival_coach_and_player_relationship():
    state = new_game("cd-terrassa", "Test", seed=911)
    ctx = press_context(state)
    assert ctx["coach"]
    assert ctx["quote"]
    questions = press_questions(state)
    assert len(questions) >= 5
    assert any(q["id"] == "rival_coach" for q in questions)
    player_question = next(q for q in questions if q["id"] == "vestuario")
    player = next((p for p in state.user_team.players if p.id == player_question["player_id"]), None)
    before = player.relationship if player else 0
    result = answer_press(state, "vestuario", 0)
    assert result["ok"]
    if player:
        assert player.relationship >= before
    assert state.press_history[-1]["opponent"]
