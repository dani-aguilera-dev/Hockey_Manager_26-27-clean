from datetime import date, timedelta

from src.events import (
    definitions,
    event_history,
    pending_events,
    resolve_event,
    tick_events,
    trigger_event,
)
from src.persistence import load_game, save_game
from src.season import new_game


def _state(seed: int = 501):
    state = new_game("cd-terrassa", "EventTest", seed=seed)
    for player in state.user_team.players:
        player.fatigue = 80
    return state


def test_event_definitions_are_loaded():
    events = definitions()
    assert len(events) >= 10
    ids = {event["id"] for event in events}
    assert "medical_hamstring_warning" in ids
    assert "medical_hamstring_tear" in ids
    assert all(event.get("choices") for event in events)


def test_trigger_and_resolve_medical_event():
    state = _state()
    day = date.fromisoformat(state.date)
    event = trigger_event(state, day, event_id="medical_hamstring_warning")
    assert event is not None
    assert len(pending_events(state)) == 1
    player = next(p for p in state.user_team.players if p.id == event["context"]["player_id"])
    before = player.fatigue

    result = resolve_event(state, event["id"], "rest", day)
    assert result["ok"]
    assert player.fatigue < before
    assert not pending_events(state)
    assert state.event_history[-1]["status"] == "resolved"
    assert state.event_history[-1]["choice_label"] == "Darle descanso y recuperación"


def test_event_cooldown_blocks_immediate_repeat():
    state = _state()
    day = date.fromisoformat(state.date)
    first = trigger_event(state, day, event_id="medical_hamstring_warning")
    assert first is not None
    resolve_event(state, first["id"], "rest", day)
    second = trigger_event(state, day, event_id="medical_hamstring_warning")
    assert second is None


def test_event_injury_effect_sets_medical_metadata():
    state = _state()
    day = date.fromisoformat(state.date)
    event = trigger_event(state, day, event_id="medical_hamstring_tear")
    assert event is not None
    player = next(p for p in state.user_team.players if p.id == event["context"]["player_id"])
    result = resolve_event(state, event["id"], "accept", day)
    assert result["ok"]
    assert player.injury == 4
    assert player.injury_type == "muscular"
    assert player.injury_severity == "grave"
    assert player.injury_expected == 4
    assert player.injury_history


def test_scheduled_event_is_activated():
    state = _state()
    day = date.fromisoformat(state.date)
    player = state.user_team.players[0]
    state.event_queue.append(
        {
            "event_id": "medical_hamstring_tear",
            "due_date": day.isoformat(),
            "context": {"player": player.name, "player_id": player.id, "team": state.user_team.name, "team_id": state.user_team.id},
            "parent_id": "parent",
            "created_at": day.isoformat(),
        }
    )
    activated = tick_events(state, day)
    assert activated
    assert any(event["event_id"] == "medical_hamstring_tear" for event in pending_events(state))


def test_expired_event_is_resolved_with_default_choice():
    state = _state()
    day = date.fromisoformat(state.date)
    event = trigger_event(state, day, event_id="medical_hamstring_warning")
    assert event is not None
    event["expires_at"] = (day - timedelta(days=1)).isoformat()
    tick_events(state, day)
    assert not pending_events(state)
    assert state.event_history[-1]["status"] == "expired"


def test_events_roundtrip_through_save():
    state = _state()
    day = date.fromisoformat(state.date)
    trigger_event(state, day, event_id="medical_hamstring_warning")
    with __import__("tempfile").TemporaryDirectory() as td:
        from pathlib import Path

        db = Path(td) / "events.db"
        save_game(state, "events", db)
        loaded = load_game("events", db)
        assert loaded.pending_events
        assert loaded.event_history
        assert pending_events(loaded)[0]["event_id"] == "medical_hamstring_warning"
