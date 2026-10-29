"""Motor de eventos con decisiones.

Los eventos del diario dejan de ser solo noticias: cada evento puede abrir una
decisión, aplicar consecuencias y programar una cadena posterior.

El contenido vive en ``manager/data/events_v2.json``. Este módulo solo conoce
el contrato de datos y las reglas de elegibilidad, efectos y seguimiento.
"""

from __future__ import annotations

import json
import random
import zlib
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

from .models import GameState, PlayerState, TeamState
from .runtime import project_root

EVENTS_FILE = project_root() / "manager" / "data" / "events_v2.json"
MAX_PENDING_EVENTS = 3
MAX_HISTORY = 200
MAX_QUEUE = 50

BIG_CLUBS = {
    "fc-barcelona",
    "rc-polo",
    "atletic-terrassa",
    "club-egara",
    "junior-fc",
    "rc-de-campo",
    "real-club-de-campo",
}


# ---------------------------------------------------------------------------
# carga de definiciones
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def definitions() -> list[dict[str, Any]]:
    path = Path(EVENTS_FILE)
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    events = payload.get("events", [])
    return [event for event in events if event.get("id")]


@lru_cache(maxsize=1)
def definitions_by_id() -> dict[str, dict[str, Any]]:
    return {event["id"]: event for event in definitions()}


def event_definition(event_id: str) -> dict[str, Any] | None:
    return definitions_by_id().get(event_id)


# ---------------------------------------------------------------------------
# utilidades de contexto
# ---------------------------------------------------------------------------


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _as_date(value: str | date | None, fallback: date | None = None) -> date:
    if isinstance(value, date):
        return value
    if value:
        try:
            return date.fromisoformat(str(value))
        except ValueError:
            pass
    return fallback or date.today()


def _rng_for(state: GameState, day: date, salt: str = "") -> random.Random:
    extra = zlib.crc32(salt.encode("utf-8")) % 100000
    return random.Random(state.seed * 10000 + day.toordinal() * 37 + extra)


def _last_results(state: GameState, limit: int = 5) -> list[str]:
    played = [
        fixture
        for fixture in state.fixtures
        if fixture.phase == "regular" and fixture.played and state.club_id in (fixture.home_id, fixture.away_id)
    ]
    played.sort(key=lambda fixture: fixture.round)
    results = []
    for fixture in played[-limit:]:
        gf = fixture.home_goals if fixture.home_id == state.club_id else fixture.away_goals
        ga = fixture.away_goals if fixture.home_id == state.club_id else fixture.home_goals
        results.append("V" if gf > ga else ("E" if gf == ga else "D"))
    return results


def _next_fixture(state: GameState):
    return state.next_user_fixture()


def _rival(state: GameState) -> TeamState | None:
    fixture = _next_fixture(state)
    if not fixture:
        return None
    rival_id = fixture.away_id if fixture.home_id == state.club_id else fixture.home_id
    return state.teams.get(rival_id)


def _days_to_match(state: GameState, day: date) -> int | None:
    fixture = _next_fixture(state)
    if not fixture:
        return None
    return (date.fromisoformat(fixture.date) - day).days


def _team_position(state: GameState) -> int:
    return next((index for index, team in enumerate(state.table(), 1) if team.id == state.club_id), 0)


def _player_matches(player: PlayerState, conditions: dict[str, Any]) -> bool:
    if conditions.get("available", True) and not player.available:
        return False
    if "min_age" in conditions and player.age < int(conditions["min_age"]):
        return False
    if "max_age" in conditions and player.age > int(conditions["max_age"]):
        return False
    if "min_fatigue" in conditions and player.fatigue < float(conditions["min_fatigue"]):
        return False
    if "max_fatigue" in conditions and player.fatigue > float(conditions["max_fatigue"]):
        return False
    if "min_overall" in conditions and player.overall < float(conditions["min_overall"]):
        return False
    if "max_overall" in conditions and player.overall > float(conditions["max_overall"]):
        return False
    if "min_relationship" in conditions and player.relationship < int(conditions["min_relationship"]):
        return False
    if "max_relationship" in conditions and player.relationship > int(conditions["max_relationship"]):
        return False
    if "min_apps" in conditions and player.apps < int(conditions["min_apps"]):
        return False
    if "max_apps" in conditions and player.apps > int(conditions["max_apps"]):
        return False
    traits = set(player.traits)
    wanted = set(conditions.get("traits_any") or [])
    if wanted and not traits.intersection(wanted):
        return False
    return True


def _team_matches(state: GameState, conditions: dict[str, Any], day: date) -> bool:
    team = state.user_team
    available = len(team.available_players)
    injured = sum(1 for player in team.players if player.injury > 0)
    avg_fatigue = sum(player.fatigue for player in team.players) / max(1, len(team.players))
    rival = _rival(state)
    fixture = _next_fixture(state)
    results = _last_results(state)
    values = {
        "available": available,
        "injury_count": injured,
        "avg_fatigue": avg_fatigue,
        "morale": team.morale,
        "cohesion": team.cohesion,
        "budget": team.budget,
        "transfer_budget": team.transfer_budget,
        "board_confidence": team.board_confidence,
        "fan_confidence": team.fan_confidence,
        "losses_last": results.count("D"),
        "days_to_match": _days_to_match(state, day),
        "next_fixture_away": bool(fixture and fixture.away_id == state.club_id),
        "rival_big": bool(rival and rival.id in BIG_CLUBS),
        "has_transfer_offer": bool(state.transfer_offers),
    }
    for key, expected in conditions.items():
        if key == "available_min" and available < int(expected):
            return False
        if key == "available_max" and available > int(expected):
            return False
        if key == "injury_count_min" and injured < int(expected):
            return False
        if key == "injury_count_max" and injured > int(expected):
            return False
        if key == "avg_fatigue_min" and avg_fatigue < float(expected):
            return False
        if key == "avg_fatigue_max" and avg_fatigue > float(expected):
            return False
        if key == "morale_min" and team.morale < int(expected):
            return False
        if key == "morale_max" and team.morale > int(expected):
            return False
        if key == "cohesion_min" and team.cohesion < int(expected):
            return False
        if key == "cohesion_max" and team.cohesion > int(expected):
            return False
        if key == "budget_min" and team.budget < int(expected):
            return False
        if key == "budget_max" and team.budget > int(expected):
            return False
        if key == "transfer_budget_min" and team.transfer_budget < int(expected):
            return False
        if key == "transfer_budget_max" and team.transfer_budget > int(expected):
            return False
        if key == "board_confidence_min" and team.board_confidence < int(expected):
            return False
        if key == "board_confidence_max" and team.board_confidence > int(expected):
            return False
        if key == "losses_last_min" and results.count("D") < int(expected):
            return False
        if key == "days_to_match_max" and (values["days_to_match"] is None or values["days_to_match"] > int(expected)):
            return False
        if key == "next_fixture_away" and values["next_fixture_away"] != bool(expected):
            return False
        if key == "rival_big" and values["rival_big"] != bool(expected):
            return False
        if key == "has_transfer_offer" and values["has_transfer_offer"] != bool(expected):
            return False
    return True


def _context(state: GameState, definition: dict[str, Any], day: date, rng: random.Random) -> dict[str, Any] | None:
    team = state.user_team
    rival = _rival(state)
    context: dict[str, Any] = {
        "team": team.name,
        "team_id": team.id,
        "date": day.isoformat(),
        "rival": rival.name if rival else "el próximo rival",
        "rival_id": rival.id if rival else "",
        "position": _team_position(state),
    }
    context_type = definition.get("context", "team")
    conditions = definition.get("conditions", {})
    if context_type == "player":
        player_conditions = conditions.get("player", {})
        pool = [player for player in team.players if _player_matches(player, player_conditions)]
        if not pool:
            return None
        player = rng.choice(pool)
        context.update(
            {
                "player": player.name,
                "player_id": player.id,
                "player_age": player.age,
                "player_position": player.subposition,
            }
        )
    elif context_type == "transfer_offer":
        if not state.transfer_offers:
            return None
        offer = state.transfer_offers[0]
        player = next((item for item in team.players if item.id == offer.get("player_id")), None)
        if player is None:
            return None
        buyer = state.teams.get(offer.get("from_club_id"))
        context.update(
            {
                "player": player.name,
                "player_id": player.id,
                "buyer": buyer.name if buyer else offer.get("from_club_name", "un club"),
                "buyer_id": buyer.id if buyer else offer.get("from_club_id", ""),
            }
        )
    elif context_type == "next_fixture":
        if not rival:
            return None
    return context


def _format(text: str, context: dict[str, Any]) -> str:
    values = {key: str(value) for key, value in context.items()}
    values.setdefault("player", "el jugador")
    values.setdefault("buyer", "un club")
    values.setdefault("rival", "el próximo rival")
    for key, value in values.items():
        text = text.replace("{" + key + "}", value)
    return text


# ---------------------------------------------------------------------------
# elegibilidad y creación
# ---------------------------------------------------------------------------


def _history_last_date(state: GameState, event_id: str) -> date | None:
    for item in reversed(state.event_history):
        if item.get("event_id") == event_id:
            return _as_date(item.get("date"), None)
    return None


def _eligible(
    state: GameState,
    definition: dict[str, Any],
    day: date,
    rng: random.Random,
    *,
    allow_zero_weight: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    if not allow_zero_weight and float(definition.get("weight", 0)) <= 0:
        return None
    pending_same = [event for event in state.pending_events if event.get("event_id") == definition["id"]]
    if len(pending_same) >= int(definition.get("max_pending", 1)):
        return None
    last = _history_last_date(state, definition["id"])
    cooldown = int(definition.get("cooldown_days", 0))
    if last is not None and cooldown and (day - last).days < cooldown:
        return None
    if definition.get("once_per_season"):
        if any(item.get("event_id") == definition["id"] and item.get("season") == state.season for item in state.event_history):
            return None
    conditions = definition.get("conditions", {})
    if not _team_matches(state, conditions.get("team", {}), day):
        return None
    context = _context(state, definition, day, rng)
    if context is None:
        return None
    return definition, context


def _instance_id(state: GameState, day: date, event_id: str) -> str:
    raw = f"{state.seed}|{state.season}|{day.isoformat()}|{event_id}|{len(state.event_history)}"
    return f"EV-{zlib.crc32(raw.encode('utf-8')) & 0xFFFFFFFF:08x}"


def _build_instance(
    state: GameState,
    definition: dict[str, Any],
    context: dict[str, Any],
    day: date,
    *,
    parent_id: str = "",
) -> dict[str, Any]:
    choices = []
    for choice in definition.get("choices", []):
        choices.append(
            {
                "id": choice["id"],
                "label": _format(choice.get("label", choice["id"]), context),
                "description": _format(choice.get("description", ""), context),
                "tone": choice.get("tone", "neutral"),
            }
        )
    return {
        "id": _instance_id(state, day, definition["id"]),
        "event_id": definition["id"],
        "category": definition.get("category", "Club"),
        "kind": definition.get("kind", "event"),
        "priority": int(definition.get("priority", 5)),
        "title": _format(definition.get("title", definition["id"]), context),
        "body": _format(definition.get("body", ""), context),
        "date": day.isoformat(),
        "expires_at": (day + timedelta(days=int(definition.get("expires_days", 7)))).isoformat(),
        "choices": choices,
        "context": context,
        "status": "pending",
        "parent_id": parent_id,
        "season": state.season,
    }


def _publish(state: GameState, category: str, headline: str, body: str, context: dict[str, Any], *, important: bool = True) -> None:
    event = {
        "date": context.get("date", state.date),
        "category": category,
        "headline": headline,
        "body": body,
        "important": important,
        "team_id": context.get("team_id", state.club_id),
        "player_id": context.get("player_id", ""),
        "league": state.competition,
        "type": "decision",
    }
    state.daily_events = (state.daily_events + [event])[-240:]
    if important:
        state.inbox = (
            state.inbox
            + [
                {
                    "date": event["date"],
                    "from": category,
                    "subject": headline,
                    "body": body,
                }
            ]
        )[-80:]


def trigger_event(
    state: GameState,
    day: date | None = None,
    rng: random.Random | None = None,
    event_id: str | None = None,
) -> dict[str, Any] | None:
    """Crea un evento pendiente si hay alguno elegible."""
    day = _as_date(day, _as_date(state.date))
    rng = rng or _rng_for(state, day)
    if len(state.pending_events) >= MAX_PENDING_EVENTS:
        return None
    if event_id:
        definition = event_definition(event_id)
        candidates = [definition] if definition else []
    else:
        candidates = definitions()
    eligible: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for definition in candidates:
        item = _eligible(state, definition, day, rng, allow_zero_weight=bool(event_id))
        if item:
            eligible.append(item)
    if not eligible:
        return None
    weights = [max(0.1, float(definition.get("weight", 1))) for definition, _ in eligible]
    definition, context = rng.choices(eligible, weights=weights, k=1)[0]
    instance = _build_instance(state, definition, context, day)
    state.pending_events.append(instance)
    state.event_history = (state.event_history + [instance.copy()])[-MAX_HISTORY:]
    _publish(state, instance["category"], instance["title"], instance["body"], context)
    return instance


def maybe_trigger_event(state: GameState, day: date, rng: random.Random | None = None) -> dict[str, Any] | None:
    """Dispara como máximo un evento importante por día."""
    if any(int(event.get("priority", 0)) >= 8 for event in state.pending_events):
        return None
    if len(state.pending_events) >= 2:
        return None
    return trigger_event(state, day, rng)


# ---------------------------------------------------------------------------
# resolución y efectos
# ---------------------------------------------------------------------------


def _player_effects(player: PlayerState, effects: dict[str, Any], day: date) -> None:
    if "morale" in effects:
        player.morale = int(_clamp(player.morale + int(effects["morale"]), 1, 20))
    if "relationship" in effects:
        player.relationship = int(_clamp(player.relationship + int(effects["relationship"]), 0, 100))
    if "form" in effects:
        player.form = _clamp(player.form + float(effects["form"]), 1.0, 10.0)
    if "fatigue" in effects:
        player.fatigue = _clamp(player.fatigue + float(effects["fatigue"]), 0.0, 100.0)
    if "injury" in effects:
        matches = int(effects["injury"])
        if matches > 0:
            player.injury = max(player.injury, matches)
            player.injury_type = str(effects.get("injury_type", player.injury_type or "molestia"))
            player.injury_severity = str(effects.get("injury_severity", player.injury_severity or "leve"))
            player.injury_started = day.isoformat()
            player.injury_expected = matches
            player.absence_note = str(effects.get("absence_note", player.injury_type.capitalize()))
            player.injury_history.append(
                {
                    "date": day.isoformat(),
                    "type": player.injury_type,
                    "severity": player.injury_severity,
                    "matches": matches,
                    "source": "event",
                }
            )
            player.injury_history = player.injury_history[-20:]
    if "suspension" in effects:
        matches = int(effects["suspension"])
        if matches > 0:
            player.suspension = max(player.suspension, matches)
            player.suspension_reason = str(effects.get("suspension_reason", "Decisión disciplinaria"))
            player.suspension_started = day.isoformat()
            player.absence_note = str(effects.get("absence_note", player.suspension_reason))
    if "absence_note" in effects and "injury" not in effects and "suspension" not in effects:
        player.absence_note = str(effects["absence_note"])
    if "transfer_listed" in effects:
        player.transfer_listed = bool(effects["transfer_listed"])


def _team_effects(team: TeamState, effects: dict[str, Any]) -> None:
    if "morale" in effects:
        team.morale = int(_clamp(team.morale + int(effects["morale"]), 1, 20))
    if "cohesion" in effects:
        team.cohesion = int(_clamp(team.cohesion + int(effects["cohesion"]), 1, 20))
    if "board" in effects:
        team.board_confidence = int(_clamp(team.board_confidence + int(effects["board"]), 0, 100))
    if "fan" in effects:
        team.fan_confidence = int(_clamp(team.fan_confidence + int(effects["fan"]), 0, 100))
    if "manager_rating" in effects:
        team.manager_rating = int(_clamp(team.manager_rating + int(effects["manager_rating"]), 0, 100))
    if "academy" in effects:
        team.academy_rating = int(_clamp(team.academy_rating + int(effects["academy"]), 0, 100))
    if "budget" in effects:
        team.budget += int(effects["budget"])
    if "transfer_budget" in effects:
        team.transfer_budget = max(0, team.transfer_budget + int(effects["transfer_budget"]))
    if "prep_bonus" in effects:
        team.prep_bonus = _clamp(team.prep_bonus + float(effects["prep_bonus"]), -5.0, 5.0)
    if "ticket_price" in effects:
        team.ticket_price = int(_clamp(int(effects["ticket_price"]), 8, 40))


def _apply_effects(state: GameState, instance: dict[str, Any], choice: dict[str, Any], day: date) -> None:
    effects = choice.get("effects", {})
    context = instance.get("context", {})
    player = next((item for item in state.user_team.players if item.id == context.get("player_id")), None)
    if player is not None and effects.get("player"):
        _player_effects(player, effects["player"], day)
    if effects.get("all_players"):
        for item in state.user_team.players:
            _player_effects(item, effects["all_players"], day)
    if effects.get("team"):
        _team_effects(state.user_team, effects["team"])
    if effects.get("flags"):
        for key, value in effects["flags"].items():
            state.event_flags[key] = str(value).replace("{player_id}", str(context.get("player_id", "")))
    if effects.get("news"):
        news = effects["news"]
        _publish(
            state,
            instance["category"],
            _format(str(news.get("headline", instance["title"])), context),
            _format(str(news.get("body", "")), context),
            context,
            important=bool(news.get("important", False)),
        )


def _schedule_follow_up(
    state: GameState,
    instance: dict[str, Any],
    choice: dict[str, Any],
    day: date,
    rng: random.Random,
) -> dict[str, Any] | None:
    follow_up = choice.get("follow_up")
    if not follow_up:
        return None
    if rng.random() >= float(follow_up.get("chance", 0)):
        return None
    definition = event_definition(str(follow_up.get("event_id", "")))
    if definition is None:
        return None
    due = day + timedelta(days=max(0, int(follow_up.get("delay_days", 1))))
    queued = {
        "event_id": definition["id"],
        "due_date": due.isoformat(),
        "context": instance.get("context", {}),
        "parent_id": instance.get("id", ""),
        "created_at": day.isoformat(),
    }
    state.event_queue = (state.event_queue + [queued])[-MAX_QUEUE:]
    return queued


def resolve_event(
    state: GameState,
    instance_id: str,
    choice_id: str | int,
    day: date | None = None,
    *,
    auto: bool = False,
) -> dict[str, Any]:
    """Resuelve un evento pendiente y aplica sus consecuencias."""
    day = _as_date(day, _as_date(state.date))
    instance = next(
        (event for event in state.pending_events if event.get("id") == instance_id or event.get("event_id") == instance_id),
        None,
    )
    if instance is None:
        return {"ok": False, "message": "La decisión ya no está pendiente."}
    choices = instance.get("choices", [])
    choice = None
    if isinstance(choice_id, int) or str(choice_id).isdigit():
        index = int(choice_id)
        if 0 <= index < len(choices):
            choice = choices[index]
    if choice is None:
        choice = next((item for item in choices if item.get("id") == str(choice_id)), None)
    if choice is None:
        return {"ok": False, "message": "Opción no válida."}
    definition = event_definition(instance.get("event_id", "")) or {}
    raw_choice = next((item for item in definition.get("choices", []) if item.get("id") == choice.get("id")), choice)
    _apply_effects(state, instance, raw_choice, day)
    instance["status"] = "resolved" if not auto else "expired"
    instance["choice_id"] = choice.get("id", "")
    instance["choice_label"] = choice.get("label", "")
    instance["response"] = _format(str(raw_choice.get("response", "")), instance.get("context", {}))
    instance["resolved_at"] = day.isoformat()
    state.pending_events = [event for event in state.pending_events if event.get("id") != instance.get("id")]
    for history_item in reversed(state.event_history):
        if history_item.get("id") == instance.get("id"):
            history_item.update(instance)
            break
    else:
        state.event_history = (state.event_history + [instance.copy()])[-MAX_HISTORY:]
    _publish(state, instance["category"], instance.get("choice_label") or instance["title"], instance["response"], instance.get("context", {}), important=True)
    rng = _rng_for(state, day, instance.get("event_id", ""))
    follow_up = _schedule_follow_up(state, instance, raw_choice, day, rng)
    return {
        "ok": True,
        "message": instance.get("choice_label", "Decisión tomada."),
        "event": instance,
        "response": instance["response"],
        "follow_up": follow_up,
        "effects": raw_choice.get("effects", {}),
    }


def tick_events(state: GameState, day: date | None = None, rng: random.Random | None = None) -> list[dict[str, Any]]:
    """Activa eventos programados y caduca los que llevan demasiado tiempo."""
    day = _as_date(day, _as_date(state.date))
    activated: list[dict[str, Any]] = []
    for item in list(state.event_queue):
        if _as_date(item.get("due_date"), day) <= day:
            definition = event_definition(str(item.get("event_id", "")))
            state.event_queue.remove(item)
            if definition is None:
                continue
            instance = _build_instance(state, definition, item.get("context", {}), day, parent_id=item.get("parent_id", ""))
            state.pending_events.append(instance)
            state.event_history = (state.event_history + [instance.copy()])[-MAX_HISTORY:]
            _publish(state, instance["category"], instance["title"], instance["body"], instance.get("context", {}))
            activated.append(instance)
    for instance in list(state.pending_events):
        expires = _as_date(instance.get("expires_at"), day)
        if expires <= day:
            choices = instance.get("choices", [])
            if choices:
                resolve_event(state, instance["id"], choices[0]["id"], day, auto=True)
    return activated


# ---------------------------------------------------------------------------
# payloads para la API
# ---------------------------------------------------------------------------


def pending_events(state: GameState) -> list[dict[str, Any]]:
    return [
        {
            "id": event.get("id"),
            "event_id": event.get("event_id"),
            "category": event.get("category"),
            "kind": event.get("kind"),
            "priority": event.get("priority", 5),
            "title": event.get("title"),
            "body": event.get("body"),
            "date": event.get("date"),
            "expires_at": event.get("expires_at"),
            "choices": event.get("choices", []),
        }
        for event in state.pending_events
    ]


def event_history(state: GameState, limit: int = 30) -> list[dict[str, Any]]:
    return [
        {
            "id": event.get("id"),
            "event_id": event.get("event_id"),
            "category": event.get("category"),
            "title": event.get("title"),
            "date": event.get("date"),
            "status": event.get("status"),
            "choice_label": event.get("choice_label", ""),
            "response": event.get("response", ""),
            "resolved_at": event.get("resolved_at", ""),
        }
        for event in reversed(state.event_history[-limit:])
        if event.get("status") != "pending"
    ]
