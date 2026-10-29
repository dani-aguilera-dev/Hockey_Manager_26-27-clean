"""Ruedas de prensa: previa, rival, presión, vestuario y objetivo."""
from __future__ import annotations

import random
import zlib

from .models import GameState


def _next_rival(state: GameState):
    fixture = state.next_user_fixture()
    if not fixture:
        return None, None, None
    opponent_id = fixture.away_id if fixture.home_id == state.club_id else fixture.home_id
    opponent = state.teams.get(opponent_id)
    return fixture, opponent, opponent_id


def press_context(state: GameState) -> dict:
    fixture, rival, rival_id = _next_rival(state)
    if not rival:
        return {"rival": "el próximo rival", "coach": "el entrenador rival", "quote": "Será un partido competido.", "date": state.date}
    coach = next((m.name for m in rival.staff if m.role == "head_coach"), "el entrenador rival")
    table = state.table()
    pos = next((i for i, t in enumerate(table, 1) if t.id == rival_id), 0)
    quotes = [
        f"Respetamos mucho a {state.user_team.name}, pero venimos a competir y a intentar llevarnos los tres puntos.",
        f"Sabemos que {state.user_team.name} es fuerte, pero tenemos nuestras armas y no vamos a renunciar a nada.",
        f"La clasificación no decide este partido. Vamos a salir a por todas desde el primer minuto.",
        f"Conocemos bien a {state.user_team.name}; tendremos que estar muy concentrados y aprovechar nuestras ocasiones.",
    ]
    rival_seed = zlib.crc32(rival_id.encode("utf-8")) % 10000 if rival_id else 0
    rng = random.Random(state.seed + state.round * 47 + rival_seed)
    return {
        "rival": rival.name, "rival_id": rival.id, "coach": coach,
        "quote": rng.choice(quotes), "position": pos, "date": fixture.date if fixture else state.date,
        "fixture": fixture,
    }


def _player_context(state: GameState) -> tuple[str, str]:
    team = state.user_team
    injured = [p for p in team.players if p.injury or p.suspension]
    if injured:
        p = injured[0]
        return p.id, f"{p.name} está de baja por {p.absence_label.lower()}."
    top = max(team.players, key=lambda p: p.overall, default=None)
    if top:
        return top.id, f"{top.name} llega como uno de los referentes del equipo."
    return "", "El grupo está preparado."


def press_questions(state: GameState) -> list[dict]:
    context = press_context(state)
    rival = context["rival"]
    coach = context["coach"]
    player_id, player_note = _player_context(state)
    questions = [
        {
            "id": "partido",
            "question": f"¿Cómo afrontáis el partido contra {rival}?",
            "options": [
                ("Vamos a por la victoria", {"morale": 1, "fan": 1, "board": 0}, "El equipo se crece ante la prensa."),
                ("Respetamos mucho al rival", {"morale": 0, "fan": 0, "board": 1}, "Mensaje prudente y profesional."),
                ("Es una final para nosotros", {"morale": 1, "fan": 1, "board": -1}, "La afición responde, la junta frunce el ceño."),
            ],
        },
        {
            "id": "rival_coach",
            "question": f"{coach} ha dicho: «{context['quote']}» ¿Qué le respondes?",
            "options": [
                ("Cada uno habla en su vestuario; nosotros miramos al nuestro", {"morale": 1, "fan": 1, "board": 1}, "Respuesta serena que gusta en el club."),
                ("Que se preocupe por su equipo", {"morale": 1, "fan": 1, "board": -1}, "La chispa está servida para la previa."),
                ("Tiene razón: será un partido muy igualado", {"morale": 0, "fan": 0, "board": 1}, "Mensaje de respeto mutuo."),
            ],
        },
        {
            "id": "presion",
            "question": "¿Siente presión por los resultados?",
            "options": [
                ("Asumo toda la responsabilidad", {"morale": 0, "fan": 1, "board": 2}, "La junta valora tu compromiso."),
                ("El equipo está conmigo", {"morale": 1, "fan": 1, "board": -1}, "El grupo agradece tu defensa."),
                ("Pensamos en el proceso", {"morale": 0, "fan": -1, "board": 1}, "Discurso de proyecto; parte de la afición duda."),
            ],
        },
        {
            "id": "vestuario",
            "question": f"{player_note} ¿Cómo está el vestuario?",
            "player_id": player_id,
            "options": [
                ("Está fuerte y unido; vamos a competir", {"morale": 1, "cohesion": 1, "relationship": 3}, "El grupo recibe el mensaje con confianza."),
                ("Hay que mejorar y lo saben", {"morale": -1, "cohesion": 0, "relationship": -2}, "La exigencia llega al vestuario."),
                ("Los nombres propios no importan; importa el equipo", {"morale": 0, "cohesion": 1, "relationship": 1}, "Mensaje colectivo que calma las aguas."),
            ],
        },
        {
            "id": "objetivo",
            "question": f"La junta habla de «{state.user_team.board_expectation}». ¿Es realista?",
            "options": [
                ("Sí, trabajamos para cumplirlo", {"morale": 1, "board": 2, "fan": 1}, "La junta aplaude la ambición."),
                ("Vamos partido a partido", {"morale": 0, "board": 1, "fan": 0}, "Mensaje prudente y centrado."),
                ("Prefiero no poner techo", {"morale": 1, "board": 0, "fan": 1}, "La afición sueña, la junta escucha."),
            ],
        },
    ]
    return questions


def answer_press(state: GameState, question_id: str, option_index: int) -> dict:
    q = next((x for x in press_questions(state) if x["id"] == question_id), None)
    if not q or not (0 <= option_index < len(q["options"])):
        return {"ok": False, "message": "Respuesta no válida."}
    label, effects, headline = q["options"][option_index]
    team = state.user_team
    team.morale = max(1, min(20, team.morale + effects.get("morale", 0)))
    team.fan_confidence = max(0, min(100, team.fan_confidence + effects.get("fan", 0)))
    team.board_confidence = max(0, min(100, team.board_confidence + effects.get("board", 0)))
    team.cohesion = max(1, min(20, team.cohesion + effects.get("cohesion", 0)))
    player_id = q.get("player_id", "")
    player = next((p for p in team.players if p.id == player_id), None)
    if player and effects.get("relationship"):
        player.relationship = max(0, min(100, player.relationship + int(effects["relationship"])))
    context = press_context(state)
    state.press_history.append(
        {
            "round": state.round,
            "question": q["question"],
            "answer": label,
            "headline": headline,
            "opponent": context.get("rival", ""),
            "opponent_coach": context.get("coach", ""),
            "opponent_quote": context.get("quote", ""),
        }
    )
    state.press_history = state.press_history[-30:]
    return {"ok": True, "message": headline, "effects": effects}


def mark_press_done(state: GameState) -> None:
    state.press_done_round = state.round
