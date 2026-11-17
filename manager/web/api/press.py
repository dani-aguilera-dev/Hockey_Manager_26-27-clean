"""API de press."""

from __future__ import annotations

import random
from datetime import date

from flask import Blueprint, request
from src.conversations import apply_conversation_choice, create_conversation, random_conversation, topics_for_target
from src.events import event_history as game_event_history
from src.events import pending_events as pending_game_events
from src.events import resolve_event as resolve_game_event
from src.news import awards_for_last_match, news_feed
from src.press import (
    answer_post_press,
    answer_press,
    mark_press_done,
    post_press_available,
    post_press_context,
    post_press_questions,
    press_context,
    press_questions,
)
from web.api.common import (
    _awards_payload,
    _chat_payload,
    _error,
    _news_item,
    _ok,
    _save,
    _state,
    _state_payload,
)

api = Blueprint("api_press", __name__, url_prefix="/api")

@api.get("/events")
def events_list():
    state, err = _state()
    if err:
        return err
    return _ok({"pending": pending_game_events(state), "history": game_event_history(state, 30)})


@api.post("/events/<instance_id>")
def events_resolve(instance_id: str):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    choice = payload.get("choice", payload.get("option", ""))
    result = resolve_game_event(state, instance_id, choice)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo resolver la decisión."), 409, "event_resolve_failed")
    _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message"))


@api.get("/news")
def news():
    state, err = _state()
    if err:
        return err
    items = [_news_item(state, item) for item in news_feed(state, 30)]
    return _ok(
        {
            "news": items,
            "awards": _awards_payload(state, awards_for_last_match(state)),
            "daily_events": list(reversed(state.daily_events[-30:])),
        }
    )


@api.get("/chat")
def chat():
    state, err = _state()
    if err:
        return err
    return _ok(_chat_payload(state))


@api.get("/chat/topics")
def chat_topics():
    state, err = _state()
    if err:
        return err
    target_type = request.args.get("target_type", "player")
    target_id = request.args.get("target_id", "")
    try:
        payload = topics_for_target(state, target_type, target_id)
    except KeyError as exc:
        return _error(str(exc), 404, "target_not_found")
    return _ok(payload)


@api.post("/chat/start")
def chat_start():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    target_type = str(payload.get("target_type", "player"))
    target_id = str(payload.get("target_id", ""))
    topic_id = payload.get("topic") or None
    try:
        message = create_conversation(state, date.fromisoformat(state.date), target_type, target_id, topic_id)
    except KeyError as exc:
        return _error(str(exc), 404, "target_not_found")
    _save(state)
    return _ok({"message": message, **_chat_payload(state)}, "Conversación abierta.")


@api.post("/chat/new")
def chat_new():
    state, err = _state()
    if err:
        return err
    message = random_conversation(state, date.fromisoformat(state.date), random.Random(state.seed + len(state.chat_messages) * 31))
    if message is None:
        return _error("No hay objetivos disponibles.", 409, "no_chat_targets")
    _save(state)
    return _ok(_chat_payload(state), "Has abierto una conversación con el vestuario.")


@api.post("/chat/<message_id>")
def chat_answer(message_id):
    state, err = _state()
    if err:
        return err
    message = next((m for m in state.chat_messages if m.get("id") == message_id), None)
    if not message or message.get("answered"):
        return _error("Esa conversación ya no está disponible.", 409, "chat_unavailable")
    payload = request.get_json(silent=True) or request.form
    try:
        choice = int(payload.get("option", 0))
    except (TypeError, ValueError):
        choice = 0
    result = apply_conversation_choice(state, message, choice)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo responder."), 409, "chat_failed")
    _save(state)
    return _ok({"result": result, **_chat_payload(state)}, result.get("message", "Conversación registrada."))


@api.get("/press")
def press():
    state, err = _state()
    if err:
        return err
    questions = []
    for q in press_questions(state):
        questions.append(
            {
                "id": q["id"],
                "question": q["question"],
                "topic": q.get("topic", ""),
                "player_id": q.get("player_id", ""),
                "options": [
                    {"label": label, "effects": effects, "headline": headline}
                    for label, effects, headline in q["options"]
                ],
            }
        )
    return _ok(
        {
            "questions": questions,
            "context": press_context(state),
            "done": state.press_done_round == state.round,
            "post_available": post_press_available(state),
            "history": state.press_history[-8:],
        }
    )


@api.get("/press/post")
def post_press():
    state, err = _state()
    if err:
        return err
    questions = []
    for q in post_press_questions(state):
        questions.append(
            {
                "id": q["id"],
                "question": q["question"],
                "topic": q.get("topic", ""),
                "options": [
                    {"label": label, "effects": effects, "headline": headline}
                    for label, effects, headline in q["options"]
                ],
            }
        )
    return _ok(
        {
            "questions": questions,
            "context": post_press_context(state),
            "done": not post_press_available(state),
            "available": post_press_available(state),
            "history": [item for item in state.press_history if item.get("kind") == "post"][-8:],
        }
    )


@api.post("/press/post")
def post_press_answer():
    state, err = _state()
    if err:
        return err
    if not post_press_available(state):
        return _error("No hay una rueda de prensa posterior disponible.", 409, "post_press_unavailable")
    payload = request.get_json(silent=True) or request.form
    answers = payload.get("answers", {})
    questions = post_press_questions(state)
    results = []
    for q in questions:
        raw = answers.get(q["id"], 0) if isinstance(answers, dict) else 0
        try:
            idx = int(raw)
        except (TypeError, ValueError):
            idx = 0
        results.append(answer_post_press(state, q["id"], idx))
    _save(state)
    return _ok({"results": results, "state": _state_payload(state)}, "Rueda de prensa posterior completada.")


@api.post("/press")
def press_answer():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    answers = payload.get("answers", {})
    questions = press_questions(state)
    results = []
    for q in questions:
        raw = answers.get(q["id"], 0) if isinstance(answers, dict) else 0
        try:
            idx = int(raw)
        except (TypeError, ValueError):
            idx = 0
        results.append(answer_press(state, q["id"], idx))
    mark_press_done(state)
    _save(state)
    return _ok({"results": results, "state": _state_payload(state)}, "Rueda de prensa completada.")
