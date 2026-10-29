"""Entrenamiento semanal y planes automáticos (Fase 2A)."""

from __future__ import annotations

import random
from typing import Any

from .models import PlayerState, TeamState

SESSION_TYPES: dict[str, dict[str, Any]] = {
    "recuperacion": {
        "label": "Recuperación",
        "short": "REC",
        "fatigue": -11.0,
        "injury": 0.002,
        "form": 0.08,
        "morale": 0.20,
        "cohesion": 0.0,
        "prep": 0.0,
        "attrs": ["resistencia", "coordinacion"],
    },
    "descanso": {
        "label": "Descanso",
        "short": "DES",
        "fatigue": -15.0,
        "injury": 0.0,
        "form": 0.04,
        "morale": 0.30,
        "cohesion": 0.0,
        "prep": 0.0,
        "attrs": [],
    },
    "fisico": {
        "label": "Físico",
        "short": "FIS",
        "fatigue": 10.0,
        "injury": 0.002,
        "form": -0.02,
        "morale": -0.08,
        "cohesion": 0.0,
        "prep": 0.0,
        "attrs": ["resistencia", "fuerza", "velocidad"],
    },
    "tactico": {
        "label": "Táctico",
        "short": "TAC",
        "fatigue": 5.0,
        "injury": 0.0015,
        "form": 0.05,
        "morale": 0.05,
        "cohesion": 0.35,
        "prep": 0.05,
        "attrs": ["posicionamiento", "decisiones", "cobertura", "pressing"],
    },
    "set_pieces": {
        "label": "Set pieces",
        "short": "PC",
        "fatigue": 4.0,
        "injury": 0.0015,
        "form": 0.04,
        "morale": 0.0,
        "cohesion": 0.10,
        "prep": 0.10,
        "attrs": ["pc_injection", "pc_trap", "pc_flick", "pc_deflection", "pc_first_runner", "stroke_shot", "free_hit"],
    },
    "ataque": {
        "label": "Ataque",
        "short": "ATA",
        "fatigue": 6.0,
        "injury": 0.002,
        "form": 0.05,
        "morale": 0.02,
        "cohesion": 0.10,
        "prep": 0.05,
        "attrs": ["definicion", "pc_flick", "regate_3d", "pase", "desmarque"],
    },
    "defensa": {
        "label": "Defensa",
        "short": "DEF",
        "fatigue": 6.0,
        "injury": 0.002,
        "form": 0.03,
        "morale": 0.0,
        "cohesion": 0.15,
        "prep": 0.05,
        "attrs": ["cobertura", "posicionamiento", "pressing", "fuerza", "transicion"],
    },
    "video": {
        "label": "Vídeo / rival",
        "short": "VID",
        "fatigue": 1.0,
        "injury": 0.0,
        "form": 0.03,
        "morale": 0.03,
        "cohesion": 0.20,
        "prep": 0.45,
        "attrs": ["decisiones", "concentracion", "posicionamiento"],
    },
    "activacion": {
        "label": "Activación",
        "short": "ACT",
        "fatigue": -3.0,
        "injury": 0.002,
        "form": 0.10,
        "morale": 0.10,
        "cohesion": 0.05,
        "prep": 0.0,
        "attrs": ["velocidad", "agilidad", "coordinacion"],
    },
}

SESSION_ORDER = [
    "recuperacion",
    "descanso",
    "fisico",
    "tactico",
    "set_pieces",
    "ataque",
    "defensa",
    "video",
    "activacion",
]

PLAN_PRESETS: dict[str, list[str]] = {
    "equilibrado": ["recuperacion", "tactico", "set_pieces", "video", "activacion"],
    "ofensivo": ["recuperacion", "ataque", "set_pieces", "ataque", "activacion"],
    "defensivo": ["recuperacion", "defensa", "tactico", "video", "activacion"],
    "fisico": ["recuperacion", "fisico", "fisico", "tactico", "activacion"],
    "recuperacion": ["recuperacion", "recuperacion", "video", "descanso", "descanso"],
}

PLAN_LABELS = {
    "equilibrado": "Equilibrado",
    "ofensivo": "Ofensivo",
    "defensivo": "Defensivo",
    "fisico": "Físico",
    "recuperacion": "Recuperación",
    "manual": "Manual",
}

DAYS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]


def plan_name(plan: list[str]) -> str:
    for name, preset in PLAN_PRESETS.items():
        if list(plan) == preset:
            return PLAN_LABELS[name]
    return "Manual"


def format_plan(plan: list[str]) -> str:
    return " · ".join(f"{DAYS[i][:3]} {SESSION_TYPES.get(s, {}).get('label', s)}" for i, s in enumerate(plan))


def auto_plan(team: TeamState, opponent: TeamState | None, rng: random.Random | None = None) -> list[str]:
    """Plan automático del segundo entrenador, adaptado al contexto."""
    rng = rng or random.Random(0)
    avg_fatigue = sum(p.fatigue for p in team.players) / max(1, len(team.players))
    injured = sum(1 for p in team.players if p.injury > 0)
    quality = team.assistant_rating
    if avg_fatigue >= 45 or injured >= 4:
        name = "recuperacion"
    elif team.morale <= 8:
        name = "recuperacion" if quality >= 65 else "equilibrado"
    elif opponent is not None:
        team_line, _ = team.auto_lineup()
        opp_line, _ = opponent.auto_lineup()
        ts = sum(team.lineup_strength(team_line)) / 2
        os_ = sum(opponent.lineup_strength(opp_line)) / 2
        if os_ > ts + 4:
            name = "defensivo"
        elif ts > os_ + 4:
            name = "ofensivo"
        else:
            name = "equilibrado"
    else:
        name = "equilibrado"
    # Un segundo entrenador flojo tiende a planes genéricos; uno bueno ajusta mejor.
    if quality < 55 and rng.random() < 0.35:
        name = "equilibrado"
    return list(PLAN_PRESETS[name])


def _gain_chance(player: PlayerState, quality: float, intense: bool) -> float:
    age_factor = 1.8 if player.age <= 22 else (1.3 if player.age <= 26 else (0.9 if player.age <= 29 else 0.4))
    gap = max(0.0, player.potential - player.overall)
    gap_factor = 0.5 + min(1.5, gap / 12.0)
    base = 0.0015 + quality * 0.0020 + (0.001 if intense else 0.0)
    return max(0.0, min(0.05, base * age_factor * gap_factor))


def apply_training_plan(
    team: TeamState,
    plan: list[str],
    opponent: TeamState | None = None,
    rng: random.Random | None = None,
    delegated: bool = True,
) -> dict[str, Any]:
    """Aplica un plan de 5 sesiones y devuelve un informe."""
    rng = rng or random.Random(0)
    if len(plan) != 5 or any(s not in SESSION_TYPES for s in plan):
        plan = list(PLAN_PRESETS["equilibrado"])
    coach_rating = team.assistant_rating if delegated else team.manager_rating
    quality = max(0.0, min(1.0, (coach_rating - 45.0) / 50.0))
    fitness_q = max(0.0, min(1.0, (team.staff_rating("fitness_coach") - 45.0) / 50.0))
    physio_q = max(0.0, min(1.0, (team.staff_rating("physio") - 45.0) / 50.0))
    analyst_q = max(0.0, min(1.0, (team.staff_rating("performance_analyst") - 45.0) / 50.0))
    gk_q = max(0.0, min(1.0, (team.staff_rating("gk_coach") - 45.0) / 50.0))
    fatigue_before = sum(p.fatigue for p in team.players) / max(1, len(team.players))
    morale_before = team.morale
    form_before = sum(p.form for p in team.players) / max(1, len(team.players))
    injuries: list[dict[str, Any]] = []
    gains: list[dict[str, Any]] = []
    recoveries: list[str] = []
    cohesion_delta = 0.0
    prep_bonus = 0.0
    for session in plan:
        spec = SESSION_TYPES[session]
        intense = session in ("fisico", "ataque", "defensa")
        if session in ("fisico", "activacion"):
            session_q = (quality + fitness_q) / 2
        elif session in ("recuperacion", "descanso"):
            session_q = (quality + physio_q) / 2
        elif session == "video":
            session_q = (quality + analyst_q) / 2
        elif session == "set_pieces":
            session_q = (quality + gk_q) / 2
        else:
            session_q = quality
        for p in team.players:
            fat = spec["fatigue"] * (1.0 - session_q * 0.12) * rng.uniform(0.85, 1.15)
            p.fatigue = max(0.0, min(100.0, p.fatigue + fat))
            p.form = max(1.0, min(10.0, p.form + spec["form"] * rng.uniform(0.8, 1.2)))
            # moral: cambios pequeños, con azar
            m = spec.get("morale", 0.0)
            if m > 0 and rng.random() < m * 2.0:
                p.morale = min(20, p.morale + 1)
            elif m < 0 and rng.random() < abs(m) * 2.0:
                p.morale = max(1, p.morale - 1)
            # riesgo de lesión
            risk = spec.get("injury", 0.0) * (1.0 + p.fatigue / 120.0) * (1.05 - session_q * 0.25)
            if p.injury > 0:
                risk = 0.0
            if rng.random() < risk:
                matches = rng.choice([1, 1, 2, 3])
                severity = "leve" if matches <= 1 else "moderada"
                injury_type = "muscular" if session in ("fisico", "activacion", "ataque", "defensa") else "golpe"
                p.injury = max(p.injury, matches)
                p.injury_type = injury_type
                p.injury_severity = severity
                p.injury_expected = matches
                p.absence_note = f"{injury_type.capitalize()} ({severity})"
                p.injury_history = (
                    p.injury_history
                    + [
                        {
                            "type": injury_type,
                            "severity": severity,
                            "matches": matches,
                            "source": f"training:{session}",
                        }
                    ]
                )[-20:]
                injuries.append(
                    {
                        "player": p.name,
                        "matches": matches,
                        "session": spec["label"],
                        "type": injury_type,
                        "severity": severity,
                    }
                )
            # recuperación de lesiones leves
            if session in ("recuperacion", "descanso") and p.injury > 0 and rng.random() < 0.10 + physio_q * 0.12:
                p.injury = max(0, p.injury - 1)
                recoveries.append(p.name)
            # progreso de atributos
            chance = _gain_chance(p, session_q, intense)
            for attr in spec.get("attrs", []):
                if rng.random() < chance:
                    old = p.attributes.get(attr, 50)
                    if old < 99:
                        p.attributes[attr] = old + 1
                        p.overall = round(min(99.0, p.overall + 0.03), 2)
                        if len(gains) < 20:
                            gains.append({"player": p.name, "attr": attr, "value": old + 1})
        cohesion_delta += spec.get("cohesion", 0.0)
        prep_bonus += spec.get("prep", 0.0) * (0.6 + analyst_q * 0.8)
    team.cohesion = int(round(max(1, min(20, team.cohesion + cohesion_delta))))
    team.morale = int(round(max(1, min(20, team.morale + sum(SESSION_TYPES[s].get("morale", 0.0) for s in plan)))))
    team.prep_bonus = round(min(2.5, prep_bonus + quality * 0.4), 2)
    fatigue_after = sum(p.fatigue for p in team.players) / max(1, len(team.players))
    form_after = sum(p.form for p in team.players) / max(1, len(team.players))
    return {
        "plan": list(plan),
        "plan_name": plan_name(plan),
        "delegated": delegated,
        "coach_rating": coach_rating,
        "fatigue_before": round(fatigue_before, 1),
        "fatigue_after": round(fatigue_after, 1),
        "morale_before": morale_before,
        "morale_after": team.morale,
        "form_before": round(form_before, 2),
        "form_after": round(form_after, 2),
        "cohesion": team.cohesion,
        "prep_bonus": team.prep_bonus,
        "injuries": injuries,
        "recoveries": recoveries,
        "gains": gains,
        "gain_count": len(gains),
        "message": (
            f"Plan {plan_name(plan)} aplicado. Fatiga media {fatigue_before:.1f}% → {fatigue_after:.1f}%. "
            f"Preparación del rival +{team.prep_bonus:.1f}."
        ),
    }
