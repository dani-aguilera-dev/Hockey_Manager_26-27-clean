"""Planes de partido condicionales.

Un plan asocia una situación de marcador y un minuto de activación a un cambio
de instrucciones. El motor calcula el delta táctico respecto a la táctica base
y lo aplica solo mientras el plan está activo. Los planes no modifican la
táctica persistente del equipo.
"""

from __future__ import annotations

import zlib
from typing import Any

from .models import TACTIC_MODS, GameState

SITUATIONS: dict[str, dict[str, Any]] = {
    "leading": {"label": "Si vamos por delante", "description": "Proteger la ventaja o sentenciar."},
    "drawing": {"label": "Si vamos empatados", "description": "Buscar el gol o mantener el control."},
    "trailing": {"label": "Si vamos por detrás", "description": "Arriesgar para remontar."},
}

INSTRUCTION_LABELS: dict[str, dict[str, str]] = {
    "mentality": {
        "muy_defensiva": "Muy defensiva",
        "defensiva": "Defensiva",
        "equilibrada": "Equilibrada",
        "ofensiva": "Ofensiva",
        "muy_ofensiva": "Muy ofensiva",
    },
    "press": {"baja": "Baja", "media": "Media", "alta": "Alta", "muy_alta": "Muy alta"},
    "block": {"bajo": "Bajo", "medio": "Medio", "alto": "Alto"},
    "tempo": {"lento": "Lento", "normal": "Normal", "rapido": "Rápido"},
    "width": {"estrecha": "Estrecha", "normal": "Normal", "ancha": "Ancha"},
    "passing": {"corto": "Corto", "mixto": "Mixto", "directo": "Directo"},
}

FIELD_LABELS: dict[str, str] = {
    "mentality": "Mentalidad",
    "press": "Presión",
    "block": "Bloque",
    "tempo": "Tempo",
    "width": "Anchura",
    "passing": "Pase",
}

FIELDS = tuple(INSTRUCTION_LABELS)
MAX_PLANS = 12


def _options() -> list[dict[str, Any]]:
    rows = []
    for field, labels in INSTRUCTION_LABELS.items():
        rows.append(
            {
                "field": field,
                "label": FIELD_LABELS[field],
                "options": [
                    {"value": value, "label": label, "attack": TACTIC_MODS[field][value][0], "defense": TACTIC_MODS[field][value][1]}
                    for value, label in labels.items()
                ],
            }
        )
    return rows


def _clean_instructions(instructions: dict[str, Any] | None) -> dict[str, str]:
    clean: dict[str, str] = {}
    for field, value in (instructions or {}).items():
        if field in FIELDS and str(value) in INSTRUCTION_LABELS[field]:
            clean[field] = str(value)
    return clean


def _plan_payload(plan: dict[str, Any]) -> dict[str, Any]:
    situation = str(plan.get("situation", "leading"))
    if situation not in SITUATIONS:
        situation = "leading"
    instructions = _clean_instructions(plan.get("instructions") or {})
    return {
        "id": plan.get("id", ""),
        "name": plan.get("name", ""),
        "situation": situation,
        "situation_label": SITUATIONS[situation]["label"],
        "from_minute": int(plan.get("from_minute", 45) or 0),
        "enabled": bool(plan.get("enabled", True)),
        "instructions": instructions,
        "instruction_labels": [
            f"{FIELD_LABELS[field]}: {INSTRUCTION_LABELS[field][value]}" for field, value in instructions.items()
        ],
        "created": plan.get("created", ""),
    }


def match_plans_overview(state: GameState) -> dict[str, Any]:
    plans = [_plan_payload(plan) for plan in state.match_plans]
    plans.sort(key=lambda plan: (not plan["enabled"], plan["from_minute"], plan["name"]))
    return {
        "plans": plans,
        "summary": {
            "total": len(plans),
            "enabled": sum(1 for plan in plans if plan["enabled"]),
            "leading": sum(1 for plan in plans if plan["situation"] == "leading"),
            "drawing": sum(1 for plan in plans if plan["situation"] == "drawing"),
            "trailing": sum(1 for plan in plans if plan["situation"] == "trailing"),
        },
        "situations": [{"id": key, **value} for key, value in SITUATIONS.items()],
        "fields": _options(),
        "max_plans": MAX_PLANS,
    }


def _validate(
    state: GameState,
    name: str,
    situation: str,
    from_minute: int,
    instructions: dict[str, Any],
) -> tuple[dict[str, str] | None, str]:
    if not name.strip():
        return None, "El plan necesita un nombre."
    if len(name.strip()) > 60:
        return None, "El nombre del plan es demasiado largo."
    if situation not in SITUATIONS:
        return None, "La situación del plan no es válida."
    if not 0 <= int(from_minute) <= 60:
        return None, "El minuto de activación debe estar entre 0 y 60."
    clean = _clean_instructions(instructions)
    if not clean:
        return None, "Selecciona al menos una instrucción."
    return clean, ""


def create_match_plan(
    state: GameState,
    name: str,
    situation: str,
    from_minute: int,
    instructions: dict[str, Any],
    enabled: bool = True,
) -> dict[str, Any]:
    if len(state.match_plans) >= MAX_PLANS:
        return {"ok": False, "message": f"Solo puedes guardar {MAX_PLANS} planes."}
    clean, error = _validate(state, name, situation, from_minute, instructions)
    if clean is None:
        return {"ok": False, "message": error}
    plan = {
        "id": f"MP-{state.season}-{state.round}-{zlib.crc32((name + situation).encode('utf-8')) % 10000}",
        "name": name.strip(),
        "situation": situation,
        "from_minute": int(from_minute),
        "enabled": bool(enabled),
        "instructions": clean,
        "created": state.date,
    }
    state.match_plans.append(plan)
    return {"ok": True, "message": f"Plan «{plan['name']}» creado.", "plan": _plan_payload(plan)}


def update_match_plan(
    state: GameState,
    plan_id: str,
    name: str,
    situation: str,
    from_minute: int,
    instructions: dict[str, Any],
    enabled: bool = True,
) -> dict[str, Any]:
    plan = next((item for item in state.match_plans if item.get("id") == plan_id), None)
    if plan is None:
        return {"ok": False, "message": "El plan no existe."}
    clean, error = _validate(state, name, situation, from_minute, instructions)
    if clean is None:
        return {"ok": False, "message": error}
    plan.update(
        {
            "name": name.strip(),
            "situation": situation,
            "from_minute": int(from_minute),
            "enabled": bool(enabled),
            "instructions": clean,
        }
    )
    return {"ok": True, "message": f"Plan «{plan['name']}» actualizado.", "plan": _plan_payload(plan)}


def delete_match_plan(state: GameState, plan_id: str) -> dict[str, Any]:
    plan = next((item for item in state.match_plans if item.get("id") == plan_id), None)
    if plan is None:
        return {"ok": False, "message": "El plan no existe."}
    state.match_plans = [item for item in state.match_plans if item.get("id") != plan_id]
    return {"ok": True, "message": f"Plan «{plan['name']}» eliminado."}
