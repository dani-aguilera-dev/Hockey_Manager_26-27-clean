"""Ruedas de prensa con periodistas, medios y consecuencias reales.

La conferencia no es un cuestionario decorativo: cada respuesta mueve moral,
cohesión, junta, afición, relación con un jugador y confianza de los medios.
El periodista y el medio cambian el tono de la sala.
"""

from __future__ import annotations

import random
import zlib
from typing import Any

from .models import GameState

JOURNALISTS = [
    {"name": "Marta Ferrer", "outlet": "Hockey Total", "style": "analítica", "bias": "juego"},
    {"name": "Jordi Soler", "outlet": "Campo Azul", "style": "crítica", "bias": "resultados"},
    {"name": "Nerea Vidal", "outlet": "La Jugada", "style": "cercana", "bias": "vestuario"},
    {"name": "Luis Aranda", "outlet": "Prensa Local", "style": "directa", "bias": "afición"},
    {"name": "Irene Costa", "outlet": "Hockey de Hoy", "style": "incisiva", "bias": "junta"},
    {"name": "Pablo Rueda", "outlet": "Deporte & Club", "style": "narrativa", "bias": "proyecto"},
]

OUTLET_TONE = {
    "Hockey Total": "Una sala técnica, atenta a los detalles tácticos.",
    "Campo Azul": "El medio llega con preguntas incómodas sobre resultados.",
    "La Jugada": "Ambiente cercano; el foco está en el grupo y las personas.",
    "Prensa Local": "La afición y el club ocupan casi todas las preguntas.",
    "Hockey de Hoy": "Mirada exigente: presupuesto, junta y expectativas.",
    "Deporte & Club": "Interés por el proyecto, la cantera y el estilo.",
}


def _next_rival(state: GameState):
    fixture = state.next_user_fixture()
    if not fixture:
        return None, None, None
    opponent_id = fixture.away_id if fixture.home_id == state.club_id else fixture.home_id
    opponent = state.teams.get(opponent_id)
    return fixture, opponent, opponent_id


def _journalist(state: GameState, rival_id: str | None) -> dict[str, str]:
    seed = state.seed * 131 + state.round * 17 + (zlib.crc32((rival_id or "").encode("utf-8")) % 997)
    return JOURNALISTS[seed % len(JOURNALISTS)]


def press_context(state: GameState) -> dict[str, Any]:
    fixture, rival, rival_id = _next_rival(state)
    journalist = _journalist(state, rival_id)
    if not rival:
        return {
            "rival": "el próximo rival",
            "rival_id": "",
            "coach": "el entrenador rival",
            "quote": "Será un partido competido.",
            "position": 0,
            "date": state.date,
            "journalist": journalist["name"],
            "outlet": journalist["outlet"],
            "style": journalist["style"],
            "bias": journalist["bias"],
            "tone": OUTLET_TONE.get(journalist["outlet"], "La sala espera respuestas."),
            "media_confidence": state.user_team.media_confidence,
        }
    coach = next((m.name for m in rival.staff if m.role == "head_coach"), "el entrenador rival")
    table = state.table()
    pos = next((i for i, t in enumerate(table, 1) if t.id == rival_id), 0)
    quotes = [
        f"Respetamos mucho a {state.user_team.name}, pero venimos a competir y a intentar llevarnos los tres puntos.",
        f"Sabemos que {state.user_team.name} es fuerte, pero tenemos nuestras armas y no vamos a renunciar a nada.",
        "La clasificación no decide este partido. Vamos a salir a por todas desde el primer minuto.",
        f"Conocemos bien a {state.user_team.name}; tendremos que estar muy concentrados y aprovechar nuestras ocasiones.",
    ]
    rival_seed = zlib.crc32(rival_id.encode("utf-8")) % 10000 if rival_id else 0
    rng = random.Random(state.seed + state.round * 47 + rival_seed)
    return {
        "rival": rival.name,
        "rival_id": rival.id,
        "coach": coach,
        "quote": rng.choice(quotes),
        "position": pos,
        "date": fixture.date if fixture else state.date,
        "journalist": journalist["name"],
        "outlet": journalist["outlet"],
        "style": journalist["style"],
        "bias": journalist["bias"],
        "tone": OUTLET_TONE.get(journalist["outlet"], "La sala espera respuestas."),
        "media_confidence": state.user_team.media_confidence,
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


def press_questions(state: GameState) -> list[dict[str, Any]]:
    context = press_context(state)
    rival = context["rival"]
    coach = context["coach"]
    player_id, player_note = _player_context(state)
    media = context["journalist"]
    return [
        {
            "id": "partido",
            "question": f"{media} · ¿Cómo afrontáis el partido contra {rival}?",
            "topic": "Enfoque",
            "options": [
                ("Vamos a por la victoria", {"morale": 1, "fan": 1, "media": 1}, "El equipo se crece ante la prensa."),
                ("Respetamos mucho al rival", {"board": 1, "media": 1}, "Mensaje prudente y profesional."),
                ("Es una final para nosotros", {"morale": 1, "fan": 1, "board": -1, "media": -1}, "La afición responde, la junta frunce el ceño."),
            ],
        },
        {
            "id": "rival_coach",
            "question": f"{coach} ha dicho: «{context['quote']}» ¿Qué le respondes?",
            "topic": "Rival",
            "options": [
                ("Cada uno habla en su vestuario; nosotros miramos al nuestro", {"morale": 1, "fan": 1, "board": 1, "media": 1}, "Respuesta serena que gusta en el club."),
                ("Que se preocupe por su equipo", {"morale": 1, "fan": 1, "board": -1, "media": -1}, "La chispa está servida para la previa."),
                ("Tiene razón: será un partido muy igualado", {"board": 1, "media": 1}, "Mensaje de respeto mutuo."),
            ],
        },
        {
            "id": "presion",
            "question": "¿Siente presión por los resultados y por la posición en la tabla?",
            "topic": "Presión",
            "options": [
                ("Asumo toda la responsabilidad", {"morale": 0, "fan": 1, "board": 2, "media": 1}, "La junta valora tu compromiso."),
                ("El equipo está conmigo", {"morale": 1, "fan": 1, "board": -1, "media": -1}, "El grupo agradece tu defensa."),
                ("Pensamos en el proceso", {"fan": -1, "board": 1, "media": 0}, "Discurso de proyecto; parte de la afición duda."),
            ],
        },
        {
            "id": "vestuario",
            "question": f"{player_note} ¿Cómo está el vestuario?",
            "player_id": player_id,
            "topic": "Vestuario",
            "options": [
                ("Está fuerte y unido; vamos a competir", {"morale": 1, "cohesion": 1, "relationship": 3, "media": 1}, "El grupo recibe el mensaje con confianza."),
                ("Hay que mejorar y lo saben", {"morale": -1, "relationship": -2, "media": 1}, "La exigencia llega al vestuario."),
                ("Los nombres propios no importan; importa el equipo", {"cohesion": 1, "relationship": 1, "media": 1}, "Mensaje colectivo que calma las aguas."),
            ],
        },
        {
            "id": "aficion",
            "question": "La grada quiere saber si este equipo va a competir hasta el final.",
            "topic": "Afición",
            "options": [
                ("Esta camiseta no se rinde", {"fan": 2, "morale": 1, "media": 1}, "La afición se identifica con el mensaje."),
                ("Necesitamos que empujen con nosotros", {"fan": 1, "cohesion": 1, "media": 1}, "Llamada a la unidad."),
                ("Prefiero hablar con hechos", {"fan": 0, "media": -1, "board": 1}, "La sala lo lee como cautela."),
            ],
        },
        {
            "id": "objetivo",
            "question": f"La junta habla de «{state.user_team.board_expectation}». ¿Es realista?",
            "topic": "Objetivo",
            "options": [
                ("Sí, trabajamos para cumplirlo", {"morale": 1, "board": 2, "fan": 1, "media": 1}, "La junta aplaude la ambición."),
                ("Vamos partido a partido", {"board": 1, "media": 0}, "Mensaje prudente y centrado."),
                ("Prefiero no poner techo", {"morale": 1, "fan": 1, "media": 1, "board": 0}, "La afición sueña, la junta escucha."),
            ],
        },
    ]


def answer_press(state: GameState, question_id: str, option_index: int) -> dict[str, Any]:
    q = next((x for x in press_questions(state) if x["id"] == question_id), None)
    if not q or not (0 <= option_index < len(q["options"])):
        return {"ok": False, "message": "Respuesta no válida."}
    label, effects, headline = q["options"][option_index]
    team = state.user_team
    team.morale = max(1, min(20, team.morale + int(effects.get("morale", 0))))
    team.fan_confidence = max(0, min(100, team.fan_confidence + int(effects.get("fan", 0))))
    team.board_confidence = max(0, min(100, team.board_confidence + int(effects.get("board", 0))))
    team.cohesion = max(1, min(20, team.cohesion + int(effects.get("cohesion", 0))))
    team.media_confidence = max(0, min(100, team.media_confidence + int(effects.get("media", 0))))
    player_id = q.get("player_id", "")
    player = next((p for p in team.players if p.id == player_id), None)
    if player and effects.get("relationship"):
        player.relationship = max(0, min(100, player.relationship + int(effects["relationship"])))
    context = press_context(state)
    state.press_history.append(
        {
            "round": state.round,
            "question": q["question"],
            "topic": q.get("topic", ""),
            "answer": label,
            "headline": headline,
            "opponent": context.get("rival", ""),
            "opponent_coach": context.get("coach", ""),
            "opponent_quote": context.get("quote", ""),
            "journalist": context.get("journalist", ""),
            "outlet": context.get("outlet", ""),
            "effects": effects,
            "media_confidence": team.media_confidence,
        }
    )
    state.press_history = state.press_history[-30:]
    return {"ok": True, "message": headline, "effects": effects, "media_confidence": team.media_confidence}


def mark_press_done(state: GameState) -> None:
    state.press_done_round = state.round
