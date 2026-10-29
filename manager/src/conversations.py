"""Conversaciones individuales y relaciones con jugadores y staff.

El módulo construye temas y opciones a partir del contexto real del objetivo:
edad, rol, rendimiento, minutos, contrato, lesiones, mercado y situación del
equipo. La UI solo tiene que pedir los temas y enviar la opción elegida.
"""

from __future__ import annotations

import random
import zlib
from datetime import date, timedelta
from typing import Any

from .market import STAFF_LABELS
from .models import GameState, PlayerState, StaffMember, TeamState


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def age_band(age: int) -> str:
    if age <= 21:
        return "joven"
    if age <= 28:
        return "madurez"
    return "veterano"


def _form(team: TeamState, state: GameState) -> str:
    played = [f for f in state.fixtures if f.phase == "regular" and f.played and team.id in (f.home_id, f.away_id)]
    played.sort(key=lambda f: f.round)
    out = []
    for f in played[-5:]:
        gf = f.home_goals if f.home_id == team.id else f.away_goals
        ga = f.away_goals if f.home_id == team.id else f.home_goals
        out.append("V" if gf > ga else ("E" if gf == ga else "D"))
    return " ".join(out) if out else "sin partidos"


def _next_rival(state: GameState) -> str:
    fx = state.next_user_fixture()
    if not fx:
        return "el próximo rival"
    rid = fx.away_id if fx.home_id == state.club_id else fx.home_id
    return state.teams[rid].name if rid in state.teams else "el próximo rival"


def _position(state: GameState) -> int:
    return next((i for i, t in enumerate(state.table(), 1) if t.id == state.club_id), 0)


def _contract_status(player: PlayerState, state: GameState) -> str:
    try:
        end_year = int(str(player.contract_until)[:4])
    except (TypeError, ValueError):
        return "sin datos"
    season_end = int(str(state.season)[:4]) + 1
    if end_year <= season_end:
        return "expira"
    if end_year <= season_end + 1:
        return "cerca"
    return "largo"


def _market_interest(state: GameState, player: PlayerState) -> bool:
    return any(o.get("player_id") == player.id for o in state.transfer_offers)


def _conversation_memory(state: GameState, target_type: str, target_id: str) -> dict[str, Any]:
    """Últimas conversaciones con este objetivo, para no repetir el mismo guion."""
    messages = [
        message
        for message in state.chat_messages
        if message.get("target_type", "player") == target_type
        and str(message.get("target_id", message.get("player_id", ""))) == str(target_id)
    ]
    answered = [message for message in messages if message.get("answered")]
    last = answered[-1] if answered else (messages[-1] if messages else None)
    last_topic = last.get("topic", "") if last else ""
    last_outcome = last.get("headline") or last.get("answer", "") if last else ""
    days_since = None
    if last:
        try:
            days_since = (date.fromisoformat(state.date) - date.fromisoformat(str(last.get("date", state.date)))).days
        except ValueError:
            days_since = None
    recent_topics = [str(message.get("topic", "")) for message in messages[-6:] if message.get("topic")]
    return {
        "conversation_count": len(messages),
        "answered_count": len(answered),
        "last_topic": last_topic,
        "last_outcome": last_outcome,
        "last_message": last,
        "days_since_talk": days_since,
        "recent_topics": recent_topics,
        "pending": any(not message.get("answered") for message in messages),
    }


def _team_last_result(state: GameState) -> str:
    played = [
        fixture
        for fixture in state.fixtures
        if fixture.phase == "regular" and fixture.played and state.club_id in (fixture.home_id, fixture.away_id)
    ]
    played.sort(key=lambda fixture: fixture.round)
    if not played:
        return "sin partidos oficiales"
    fixture = played[-1]
    gf = fixture.home_goals if fixture.home_id == state.club_id else fixture.away_goals
    ga = fixture.away_goals if fixture.home_id == state.club_id else fixture.home_goals
    rival_id = fixture.away_id if fixture.home_id == state.club_id else fixture.home_id
    rival = state.teams.get(rival_id)
    result = "victoria" if gf > ga else ("empate" if gf == ga else "derrota")
    return f"{result} {gf}-{ga} contra {rival.name if rival else 'el rival'}"


def _contextual_prompt(topic: str, ctx: dict[str, Any], base: str) -> str:
    """Añade datos reales al texto de apertura para que no sea genérico."""
    name = ctx.get("name", "Entrenador")
    details: dict[str, str] = {
        "role": (
            f"Llevo {ctx.get('apps', 0)} partidos y ahora mismo soy {str(ctx.get('role', 'rotación')).lower()}. "
            f"Mi forma es {ctx.get('form', 0):.1f} y mi moral está en {ctx.get('morale', 10)}/20."
        ),
        "performance": (
            f"Llevo {ctx.get('goals', 0)} goles, {ctx.get('assists', 0)} asistencias y un rating de "
            f"{ctx.get('rating', 0):.2f}. El equipo viene de {ctx.get('team_last_result', 'un partido reciente')}."
        ),
        "contract": (
            f"Mi contrato termina el {ctx.get('contract_until', '—')} y el club aún no me ha dicho nada. "
            f"Tengo {ctx.get('age', 0)} años y llevo {ctx.get('apps', 0)} partidos esta temporada."
        ),
        "recovery": (
            f"El parte médico habla de {ctx.get('injury_type', 'una lesión')} "
            f"({ctx.get('injury_severity', 'leve')}) y me quedan {ctx.get('injury', 0)} partido(s). "
            f"Quiero volver bien, no solo rápido."
        ),
        "market": (
            f"Sé que hay interés de mercado. Mi contrato va hasta {ctx.get('contract_until', '—')} "
            f"y el club no me ha aclarado nada."
        ),
        "development": (
            f"Tengo {ctx.get('age', 0)} años y un potencial de {ctx.get('potential', 0):.1f}. "
            f"Necesito saber qué plan hay para mí."
        ),
        "rival": (
            f"El próximo rival es {ctx.get('next_rival', 'el siguiente')} y el equipo llega con "
            f"forma {ctx.get('team_form', 'sin datos')}."
        ),
        "club": (
            f"El equipo es {ctx.get('team_position', 0)}º y viene de {ctx.get('team_last_result', 'un partido reciente')}. "
            f"La relación con el club es {ctx.get('relationship_label', 'normal')}."
        ),
        "staff_training": (
            f"El equipo viene de {ctx.get('team_last_result', 'un partido reciente')} y la fatiga media "
            f"es {ctx.get('avg_fatigue', 0):.0f}%."
        ),
        "staff_rival": (
            f"El próximo rival es {ctx.get('next_rival', 'el siguiente')} y llega con forma "
            f"{ctx.get('rival_form', 'sin datos')}. He preparado el informe."
        ),
        "staff_squad": (
            f"La moral del grupo es {ctx.get('team_morale', 10)}/20 y la cohesión "
            f"{ctx.get('team_cohesion', 10)}/20. Hay que decidir cómo entrar esta semana."
        ),
        "staff_fitness": (
            f"La fatiga media es {ctx.get('avg_fatigue', 0):.0f}% y tenemos "
            f"{ctx.get('injury_count', 0)} jugador(es) en enfermería."
        ),
    }
    detail = details.get(topic, "")
    if not detail:
        return base
    return f"{base}\n\n{detail}"


def _follow_up_stage(topic: str, ctx: dict[str, Any], option: dict[str, Any], target_type: str) -> tuple[str, list[dict[str, Any]]]:
    """Segunda parte de la conversación: el jugador responde y pide una decisión."""
    name = ctx.get("name", "el jugador")
    tone = option.get("tone", "neutral")
    rival = ctx.get("next_rival", "el próximo rival")
    if target_type == "staff":
        prompt = "Entrenador, ¿y cómo quieres que lo aterrice en el trabajo de esta semana?"
        options = [
            _opt("Cerrar con un plan concreto", {"relationship": 2, "prep_bonus": 0.1, "manager_rating": 1}, "El staff sale con una lista de tareas y una fecha.", "Plan cerrado", "ok"),
            _opt("Darle margen para proponer", {"relationship": 3, "cohesion": 1}, "El empleado agradece la confianza y propone su propia solución.", "Confianza", "ok"),
            _opt("Exigir resultados inmediatos", {"prep_bonus": 0.15, "relationship": -1, "morale": -1}, "El mensaje aprieta; el staff responde con tensión.", "Exigencia", "warn"),
        ]
        return prompt, options
    if tone in ("danger", "warn"):
        prompt = f"{name} baja la mirada. «Entrenador, lo entiendo, pero necesito saber si esto cambia algo entre nosotros.»"
        options = [
            _opt("Mantener la decisión", {"relationship": -1, "morale": -1, "board": 1}, "El jugador acepta la decisión, pero toma distancia.", "Firmeza", "warn"),
            _opt("Suavizar el mensaje", {"relationship": 3, "morale": 1, "cohesion": 1}, "La tensión baja y el jugador vuelve a sentirse escuchado.", "Corrección", "ok"),
            _opt("Escuchar su versión", {"relationship": 4, "morale": 1}, "El jugador se abre y la conversación termina con un compromiso.", "Escucha", "ok"),
        ]
    else:
        prompt = f"{name} asiente. «¿Y qué esperas de mí a partir de ahora?»"
        options = [
            _opt("Cerrar con un compromiso", {"relationship": 2, "morale": 1, "cohesion": 1}, "El jugador se marcha con una meta clara y el grupo lo nota.", "Compromiso", "ok"),
            _opt("Darle un objetivo medible", {"form": 0.2, "relationship": 1, "manager_rating": 1}, "El jugador apunta el objetivo y se compromete a trabajarlo.", "Objetivo", "neutral"),
            _opt("Dejar que lo demuestre", {"form": 0.3, "morale": -1, "relationship": -1}, "El jugador acepta el reto, aunque le habría gustado más apoyo.", "Exigencia", "warn"),
        ]
    if topic == "rival":
        prompt = f"{name} pregunta: «¿Qué quieres que haga distinto contra {rival}?»"
    return prompt, options


def _closing_line(ctx: dict[str, Any], option: dict[str, Any], target_type: str) -> str:
    name = ctx.get("name", "El jugador")
    tone = option.get("tone", "neutral")
    if target_type == "staff":
        return "El staff recoge sus notas y vuelve al trabajo."
    if tone == "ok":
        return f"{name} se marcha con más confianza y con una idea clara de lo que viene."
    if tone == "danger":
        return f"{name} se marcha en silencio. La conversación ha dejado poso, pero no todo está resuelto."
    return f"{name} asiente y vuelve al grupo con una mezcla de alivio y exigencia."


def player_context(state: GameState, player: PlayerState) -> dict[str, Any]:
    team = state.user_team
    lineup, _ = team.auto_lineup()
    starters = {p.id for p in lineup}
    top_goals = max((p.season_goals for p in team.players), default=0)
    rating = float(player.rating or 0)
    if player.injury > 0:
        performance = "Lesionado"
    elif player.suspension > 0:
        performance = "Sancionado"
    elif player.apps == 0:
        performance = "Sin minutos"
    elif rating >= 7.2:
        performance = "En racha"
    elif rating >= 6.5:
        performance = "Rendimiento estable"
    else:
        performance = "Por debajo de su nivel"
    memory = _conversation_memory(state, "player", player.id)
    fixture = state.next_user_fixture()
    rival = None
    if fixture:
        rival_id = fixture.away_id if fixture.home_id == state.club_id else fixture.home_id
        rival = state.teams.get(rival_id)
    return {
        "target_type": "player",
        "target_id": player.id,
        "name": player.name,
        "age": player.age,
        "age_band": age_band(player.age),
        "position": player.subposition,
        "overall": round(float(player.overall), 1),
        "potential": round(float(player.potential), 1),
        "form": round(float(player.form), 1),
        "fatigue": round(float(player.fatigue), 1),
        "morale": player.morale,
        "relationship": player.relationship,
        "apps": player.apps,
        "goals": player.season_goals,
        "assists": player.season_assists,
        "rating": round(rating, 2),
        "contract_until": player.contract_until,
        "contract_status": _contract_status(player, state),
        "injury": player.injury,
        "injury_type": player.injury_type,
        "injury_severity": player.injury_severity,
        "injury_expected": player.injury_expected,
        "suspension": player.suspension,
        "available": player.available,
        "is_starter": player.id in starters,
        "role": "Titular" if player.id in starters else ("Rotación" if player.apps else "Sin minutos"),
        "performance": performance,
        "team_position": _position(state),
        "team_name": team.name,
        "next_rival": _next_rival(state),
        "team_form": _form(team, state),
        "market_interest": _market_interest(state, player),
        "top_scorer": player.season_goals > 0 and player.season_goals == top_goals,
        "young": player.age <= 21,
        "veteran": player.age >= 29,
        "relationship_label": player.relationship_label,
        "team_last_result": _team_last_result(state),
        "team_morale": team.morale,
        "team_cohesion": team.cohesion,
        "avg_fatigue": round(sum(item.fatigue for item in team.players) / max(1, len(team.players)), 1),
        "injury_count": sum(1 for item in team.players if item.injury > 0),
        "rival_form": _form(rival, state) if rival else "sin datos",
        "promises": [promise for promise in player.promises if promise.get("status") == "open"],
        **memory,
    }


def staff_context(state: GameState, member: StaffMember) -> dict[str, Any]:
    team = state.user_team
    memory = _conversation_memory(state, "staff", member.role)
    fixture = state.next_user_fixture()
    rival = None
    if fixture:
        rival_id = fixture.away_id if fixture.home_id == state.club_id else fixture.home_id
        rival = state.teams.get(rival_id)
    return {
        "target_type": "staff",
        "target_id": member.role,
        "name": member.name,
        "role": STAFF_LABELS.get(member.role, member.role),
        "rating": member.rating,
        "salary": member.salary,
        "contract_until": member.contract_until,
        "relationship": member.relationship,
        "morale": member.morale,
        "team_position": _position(state),
        "team_name": team.name,
        "next_rival": _next_rival(state),
        "team_form": _form(team, state),
        "relationship_label": member.relationship_label,
        "team_last_result": _team_last_result(state),
        "team_morale": team.morale,
        "team_cohesion": team.cohesion,
        "avg_fatigue": round(sum(item.fatigue for item in team.players) / max(1, len(team.players)), 1),
        "injury_count": sum(1 for item in team.players if item.injury > 0),
        "rival_form": _form(rival, state) if rival else "sin datos",
        **memory,
    }


def target_summary(state: GameState, target_type: str, target_id: str) -> dict[str, Any] | None:
    if target_type == "player":
        player = next((p for p in state.user_team.players if p.id == target_id), None)
        if not player:
            return None
        context = player_context(state, player)
        return {
            **context,
            "photo": player.photo,
            "photo_remote": player.photo_remote,
            "initials": "".join(part[0] for part in player.name.split()[:2]).upper(),
            "overall": round(float(player.overall), 1),
            "potential": round(float(player.potential), 1),
            "archetype": player.archetype,
            "team_name": state.user_team.name,
        }
    member = next((m for m in state.user_team.staff if m.role == target_id and m.role != "head_coach"), None)
    if not member:
        return None
    context = staff_context(state, member)
    return {
        **context,
        "photo": "",
        "initials": "".join(part[0] for part in member.name.split()[:2]).upper(),
        "archetype": "Staff",
        "team_name": state.user_team.name,
    }


def conversation_targets(state: GameState) -> dict[str, list[dict[str, Any]]]:
    players = []
    for player in sorted(state.user_team.players, key=lambda p: (p.position_group, -p.overall)):
        summary = target_summary(state, "player", player.id)
        if summary:
            summary["topic_count"] = len(topics_for_target(state, "player", player.id)["topics"])
            players.append(summary)
    staff = []
    for member in state.user_team.staff:
        if member.role == "head_coach":
            continue
        summary = target_summary(state, "staff", member.role)
        if summary:
            summary["topic_count"] = len(topics_for_target(state, "staff", member.role)["topics"])
            staff.append(summary)
    return {"players": players, "staff": staff}


# ---------------------------------------------------------------------------
# topics
# ---------------------------------------------------------------------------


def _topic(topic_id: str, label: str, description: str, category: str) -> dict[str, str]:
    return {"id": topic_id, "label": label, "description": description, "category": category}


def _topics_player(ctx: dict[str, Any]) -> list[dict[str, str]]:
    topics = [
        _topic("role", "Rol y minutos", "Aclara su papel en el once y qué esperas de él.", "Equipo"),
        _topic("performance", "Rendimiento", "Habla de su momento, sus números y el siguiente paso.", "Rendimiento"),
    ]
    if ctx["young"]:
        topics += [
            _topic("development", "Desarrollo", "Plan individual, minutos y crecimiento a medio plazo.", "Cantera"),
            _topic("confidence", "Confianza", "Protege su progreso y ayúdale a gestionar la presión.", "Vestuario"),
        ]
    if ctx["veteran"]:
        topics += [
            _topic("legacy", "Liderazgo y legado", "Su peso en el grupo, la carga física y el futuro.", "Vestuario"),
            _topic("future", "Futuro y contrato", "Continuidad, renovación o transición al staff.", "Club"),
        ]
    if ctx["contract_status"] in ("expira", "cerca"):
        topics.append(_topic("contract", "Renovación", "Aclara el contrato antes de que el mercado lo use.", "Club"))
    if ctx["injury"] or ctx["suspension"]:
        topics.append(_topic("recovery", "Recuperación", "Plan de vuelta, cargas y apoyo del club.", "Enfermería"))
    if ctx["market_interest"]:
        topics.append(_topic("market", "Mercado", "Hay interés real. Define tu postura y la del club.", "Mercado"))
    if ctx["team_position"] and ctx["team_position"] <= 3:
        topics.append(_topic("ambition", "Ambición", "El equipo está arriba; sube el listón sin romper el grupo.", "Club"))
    if ctx["performance"] in ("Por debajo de su nivel", "Sin minutos"):
        topics.append(_topic("confidence", "Confianza", "Trabaja la cabeza y el rol sin prometer lo que no toca.", "Vestuario"))
    topics += [
        _topic("rival", "Próximo rival", "Mensaje específico para el partido que viene.", "Partido"),
        _topic("club", "Proyecto de club", "Objetivo, vestuario y relación con la junta.", "Club"),
    ]
    if ctx["suspension"]:
        topics.append(_topic("discipline", "Disciplina", "Marca consecuencias sin destruir la relación.", "Vestuario"))
    return topics


def _topics_staff(ctx: dict[str, Any]) -> list[dict[str, str]]:
    return [
        _topic("staff_training", "Plan de entrenamiento", "Carga, sesiones y preparación del rival.", "Staff"),
        _topic("staff_rival", "Análisis del rival", "Ajustes tácticos y plan de partido.", "Staff"),
        _topic("staff_squad", "Clima del vestuario", "Moral, conflictos y liderazgo del grupo.", "Vestuario"),
        _topic("staff_market", "Mercado y ojeador", "Refuerzos, ventas y perfiles que encajan.", "Mercado"),
        _topic("staff_fitness", "Carga física", "Fatiga, recuperación y riesgo de lesión.", "Preparación"),
        _topic("staff_youth", "Cantera", "Promociones, cesiones y desarrollo de jóvenes.", "Cantera"),
        _topic("staff_club", "Proyecto y junta", "Presupuesto, objetivo y confianza institucional.", "Club"),
    ]


def topics_for_target(state: GameState, target_type: str, target_id: str) -> dict[str, Any]:
    summary = target_summary(state, target_type, target_id)
    if not summary:
        raise KeyError("Objetivo no encontrado")
    topics = _topics_player(summary) if target_type == "player" else _topics_staff(summary)
    recent = set(summary.get("recent_topics", []))
    urgent = {
        "role" if summary.get("apps", 0) < 4 else "",
        "contract" if summary.get("contract_status") in ("expira", "cerca") else "",
        "recovery" if summary.get("injury") or summary.get("suspension") else "",
        "market" if summary.get("market_interest") else "",
        "rival",
        "staff_fitness" if summary.get("avg_fatigue", 0) >= 55 else "",
    }
    for topic in topics:
        topic["recent"] = topic["id"] in recent
        topic["recommended"] = topic["id"] in urgent and not topic["recent"]
    return {"target": summary, "topics": topics}


# ---------------------------------------------------------------------------
# options
# ---------------------------------------------------------------------------


def _opt(label: str, effects: dict[str, Any], response: str, headline: str, tone: str = "neutral") -> dict[str, Any]:
    return {"label": label, "effects": effects, "response": response, "headline": headline, "tone": tone}


def _options(topic: str, ctx: dict[str, Any]) -> list[dict[str, Any]]:
    age = ctx.get("age_band", "madurez")
    performance = ctx.get("performance", "")
    if topic == "role":
        prompt = {
            "joven": f"Entrenador, soy joven y necesito saber qué papel voy a tener. No quiero quedarme en el banquillo sin entender por qué.",
            "veterano": "A estas alturas quiero claridad. Sé lo que puedo dar y necesito saber si el club cuenta conmigo de verdad.",
            "madurez": "Quiero saber cuál es mi rol en el equipo. Estoy en un momento en el que necesito minutos y responsabilidad.",
        }.get(age, "Quiero saber cuál es mi papel en el equipo.")
        return [
            _opt("Te veo titular y con confianza", {"morale": 2, "relationship": 5, "form": 0.3}, "El jugador se marcha con el pecho más ancho y promete devolver la confianza.", "Confianza ganada", "ok"),
            _opt("Vas a tener minutos desde el banquillo", {"morale": 1, "relationship": 2, "cohesion": 1, "promise": "minutes", "promise_text": "Tendrás minutos en los próximos partidos."}, "Acepta el rol, aunque deja claro que quiere pelear por más.", "Rol aceptado", "neutral"),
            _opt("Tienes que ganarte el puesto", {"morale": -1, "relationship": -2, "form": 0.5}, "La conversación es dura; el jugador responde con más intensidad en la sesión.", "Exigencia", "warn"),
            _opt("El rol lo marcará el rendimiento", {"relationship": 1, "form": 0.2, "manager_rating": 1}, "Entiende que la competencia es real y que el cuerpo técnico no regala nada.", "Mensaje profesional", "neutral"),
        ], prompt
    if topic == "performance":
        prompt = {
            "En racha": "Sé que estoy en un buen momento, pero no quiero que el equipo dependa solo de mí. ¿Cómo lo ves?",
            "Rendimiento estable": "Quiero dar un paso más. Mi rendimiento es regular, pero sé que puedo aportar más en ataque.",
            "Por debajo de su nivel": "No estoy contento con mi nivel. Quiero entender qué esperas de mí para darle la vuelta.",
            "Sin minutos": "No he tenido minutos y necesito saber qué tengo que hacer para entrar en el plan.",
            "Lesionado": "Estoy trabajando para volver, pero necesito saber qué papel tendré cuando esté listo.",
            "Sancionado": "Sé que no he estado a la altura. Quiero saber cómo recuperar la confianza del grupo.",
        }.get(performance, "Quiero hablar de mi rendimiento y de lo que esperas de mí.")
        return [
            _opt("Reconocer su momento", {"morale": 2, "relationship": 4, "form": 0.2}, "El jugador agradece el reconocimiento y se siente valorado.", "Reconocimiento", "ok"),
            _opt("Exigirle un paso más", {"form": 0.5, "morale": -1, "relationship": -1}, "El mensaje le incomoda, pero activa su competitividad.", "Exigencia", "warn"),
            _opt("Analizar el partido juntos", {"relationship": 3, "manager_rating": 1, "form": 0.2}, "Salen con un plan concreto y una lectura compartida.", "Trabajo compartido", "neutral"),
            _opt("Darle descanso y protección", {"fatigue": -6, "morale": 1, "relationship": 2}, "El jugador respira y entiende que el club mira también su carga.", "Protección", "ok"),
        ], prompt
    if topic == "development":
        return [
            _opt("Diseñar un plan individual", {"relationship": 5, "form": 0.4, "cohesion": 1}, "El canterano sale con deberes claros y una hoja de ruta.", "Plan individual", "ok"),
            _opt("Prometerle minutos en Copa", {"morale": 2, "relationship": 3, "form": 0.2, "promise": "minutes", "promise_text": "Tendrás minutos en la Copa."}, "La promesa le ilusiona, aunque sabe que debe entrenar para ganarla.", "Oportunidad", "ok"),
            _opt("Plantear una cesión", {"morale": -1, "relationship": 2, "form": 0.2}, "La idea no le entusiasma, pero entiende que necesita jugar.", "Cesión", "warn"),
            _opt("Pedirle paciencia y trabajo", {"morale": 1, "relationship": 1, "form": 0.2}, "Acepta el proceso y se queda a trabajar.", "Paciencia", "neutral"),
        ], "Entrenador, quiero crecer aquí. ¿Qué plan tienes para mí? Necesito saber qué pasos dar para llegar al primer equipo."
    if topic == "legacy":
        return [
            _opt("Darle liderazgo en el vestuario", {"morale": 2, "relationship": 4, "cohesion": 2}, "El veterano asume el rol de referente y el grupo lo nota.", "Liderazgo", "ok"),
            _opt("Gestionar su carga física", {"fatigue": -8, "relationship": 2, "form": 0.2}, "Agradece que el club piense en su cuerpo y no solo en el resultado.", "Gestión", "ok"),
            _opt("Hablar de renovación", {"morale": 3, "relationship": 5, "board": -1}, "La conversación le ilusiona; la junta pide prudencia.", "Continuidad", "warn"),
            _opt("Abrir la puerta al staff", {"relationship": 3, "manager_rating": 1, "cohesion": 1}, "Le atrae la idea de seguir ligado al club cuando deje de jugar.", "Transición", "neutral"),
        ], "He vivido mucho en este club. Quiero saber cómo ves mi papel ahora y qué viene después."
    if topic == "future":
        return [
            _opt("Apostar por su continuidad", {"morale": 2, "relationship": 4, "board": 1}, "El jugador respira: siente que el club cuenta con él.", "Continuidad", "ok"),
            _opt("Escuchar ofertas con calma", {"relationship": -1, "board": 2, "morale": 0}, "Entiende la postura del club, pero no le gusta sentirse en el escaparate.", "Mercado", "warn"),
            _opt("Ofrecerle un rol técnico", {"relationship": 3, "morale": 1, "manager_rating": 1}, "Le interesa el proyecto más allá de los terrenos de juego.", "Proyecto", "neutral"),
            _opt("Dejar el futuro abierto", {"relationship": -2, "morale": -1}, "La falta de claridad le deja frío.", "Incertidumbre", "danger"),
        ], "No sé qué va a pasar con mi futuro. Quiero que el club sea claro conmigo."
    if topic == "contract":
        return [
            _opt("Prometer una renovación", {"morale": 3, "relationship": 5, "board": -1, "promise": "renewal", "promise_days": 30, "promise_text": "El club abrirá tu renovación."}, "El jugador se ilusiona y pide que el club lo formalice pronto.", "Renovación", "ok"),
            _opt("Mejorar su salario", {"morale": 2, "relationship": 4, "fine": 0}, "La conversación avanza, pero el club tendrá que hacer números.", "Esfuerzo económico", "warn"),
            _opt("Pedirle que se gane el contrato", {"morale": -1, "form": 0.4, "relationship": -2}, "Acepta el reto con gesto serio.", "Exigencia", "warn"),
            _opt("Dejar la decisión al director deportivo", {"morale": 0, "relationship": -1, "board": 1}, "El jugador entiende el procedimiento, pero esperaba más de ti.", "Procedimiento", "neutral"),
        ], "Mi contrato termina pronto y necesito claridad. ¿Cuenta el club conmigo?"
    if topic == "recovery":
        return [
            _opt("No forzar la vuelta", {"injury": -1, "relationship": 3, "morale": 1}, "El jugador agradece que el club priorice su salud.", "Paciencia", "ok"),
            _opt("Marcar un plan de vuelta", {"relationship": 2, "form": 0.2, "manager_rating": 1}, "Sale con fechas y objetivos, sin promesas vacías.", "Plan de vuelta", "neutral"),
            _opt("Exigirle que apriete", {"injury": 1, "relationship": -4, "morale": -2}, "El mensaje le presiona y el cuerpo médico frunce el ceño.", "Riesgo", "danger"),
            _opt("Apoyo del club y del fisio", {"injury": -1, "relationship": 4, "cohesion": 1}, "Se siente acompañado en la recuperación.", "Apoyo", "ok"),
        ], "Quiero volver cuanto antes, pero también quiero hacerlo bien. ¿Cómo lo enfocamos?"
    if topic == "market":
        return [
            _opt("No te vendo", {"morale": 2, "relationship": 6, "board": -2}, "El jugador siente el respaldo del club y el vestuario lo comenta.", "Blindaje", "ok"),
            _opt("Escuchar ofertas", {"relationship": -2, "board": 2, "morale": 0}, "La conversación deja una puerta abierta y algo de frialdad.", "Mercado", "warn"),
            _opt("Mejorar su contrato", {"morale": 2, "relationship": 3, "board": -1, "promise": "renewal", "promise_days": 30, "promise_text": "El club mejorará tu contrato."}, "El jugador quiere quedarse, pero con condiciones.", "Contrato", "warn"),
            _opt("Pensar en el proyecto", {"morale": 1, "relationship": 2, "cohesion": 1}, "Acepta escuchar el proyecto antes de decidir.", "Proyecto", "neutral"),
        ], "Sé que hay clubes preguntando por mí. Quiero saber qué piensa el club y qué quieres tú."
    if topic == "rival":
        rival = ctx.get("next_rival", "el próximo rival")
        return [
            _opt("Mensaje motivador", {"morale": 1, "form": 0.2, "relationship": 1}, f"El jugador sale con energía para medirse a {rival}.", "Motivación", "ok"),
            _opt("Plan específico para el rival", {"prep_bonus": 0.2, "relationship": 2, "manager_rating": 1}, "Trabajan juntos una idea concreta para el partido.", "Plan de partido", "ok"),
            _opt("Prudencia y respeto", {"cohesion": 1, "morale": 0, "board": 1}, "El mensaje baja el ruido y centra al grupo.", "Prudencia", "neutral"),
            _opt("Responsabilidad individual", {"relationship": 1, "form": 0.3, "manager_rating": 1}, "El jugador asume su parte del plan.", "Responsabilidad", "neutral"),
        ], f"Entrenador, ¿cómo quieres que afrontemos el partido contra {rival}?"
    if topic == "club":
        return [
            _opt("Objetivo ambicioso", {"morale": 1, "board": 2, "fan": 1}, "El grupo compra el discurso y la junta lo escucha.", "Ambición", "ok"),
            _opt("Paso a paso", {"board": 1, "fan": 1, "cohesion": 1}, "Mensaje de estabilidad que calma el entorno.", "Estabilidad", "neutral"),
            _opt("Proteger al grupo", {"cohesion": 2, "relationship": 2}, "El jugador siente que el entrenador pone al equipo por delante.", "Protección", "ok"),
            _opt("Exigencia máxima", {"form": 0.3, "morale": -1, "board": 1}, "La exigencia sube, pero también la tensión.", "Exigencia", "warn"),
        ], "¿Qué espera el club de nosotros esta temporada? Quiero entender el objetivo real."
    if topic == "confidence":
        return [
            _opt("Confianza plena", {"morale": 2, "relationship": 4, "form": 0.3}, "El jugador se siente respaldado y recupera aire.", "Confianza", "ok"),
            _opt("Trabajo específico", {"form": 0.5, "relationship": 2, "fatigue": 2}, "Sale con deberes concretos y más carga de trabajo.", "Trabajo", "neutral"),
            _opt("Un paso al banquillo", {"morale": -2, "relationship": -3, "cohesion": -1}, "La decisión le duele, aunque la entiende.", "Decisión dura", "danger"),
            _opt("Apoyo de un veterano", {"cohesion": 1, "relationship": 2, "morale": 1}, "El grupo se protege y el jugador no se siente solo.", "Vestuario", "ok"),
        ], "No estoy pasando por mi mejor momento. Necesito saber si confías en mí."
    if topic == "discipline":
        return [
            _opt("Sanción interna y apartado", {"relationship": -10, "morale": -2, "suspension": 1, "board": 3, "fan": 2, "fine": 2500, "note": "Sanción disciplinaria"}, "El club marca distancia y la junta respira. El jugador se siente señalado.", "Sanción", "danger"),
            _opt("Defenderlo públicamente", {"relationship": 8, "morale": 2, "board": -3, "fan": -2}, "El jugador agradece el apoyo; parte de la afición critica la protección.", "Respaldo", "warn"),
            _opt("Apoyo privado y responsabilidad", {"relationship": 6, "cohesion": 1, "morale": 1}, "La conversación queda entre vosotros y el jugador entiende la gravedad.", "Gestión privada", "ok"),
            _opt("Trabajo con la cantera", {"relationship": 3, "board": 2, "fan": 1, "cohesion": 1}, "El club convierte el error en una acción formativa.", "Segunda oportunidad", "neutral"),
        ], "Sé que lo que pasó no es propio de un profesional. Quiero saber qué vas a hacer conmigo."
    if topic == "family":
        return [
            _opt("Darle permiso para resolverlo", {"relationship": 8, "morale": 2, "cohesion": 1}, "El jugador agradece la comprensión del club.", "Comprensión", "ok"),
            _opt("Pedirle concentración", {"relationship": -4, "morale": -1}, "Acata la decisión, pero se le nota más frío.", "Exigencia", "warn"),
            _opt("Buscar apoyo del club", {"relationship": 5, "morale": 1, "fan": 1}, "El club se vuelca y el vestuario lo percibe.", "Apoyo", "ok"),
            _opt("Hablar con el psicólogo", {"relationship": 3, "morale": 1, "cohesion": 1}, "Acepta ayuda profesional sin sentirse juzgado.", "Cuidado", "neutral"),
        ], "En casa hay un asunto familiar que me está afectando. Quería contártelo antes de que sea un problema."
    if topic == "media":
        return [
            _opt("Salir a defenderlo", {"relationship": 7, "fan": 1, "board": -1}, "La prensa recoge tu respaldo y el jugador lo agradece.", "Respaldo", "ok"),
            _opt("Mantener silencio y hablar dentro", {"relationship": 2, "cohesion": 1}, "El vestuario entiende que los temas se resuelven en casa.", "Discreción", "neutral"),
            _opt("Señalarlo como ejemplo negativo", {"relationship": -6, "board": 2, "fan": -1}, "El mensaje es contundente; el jugador queda tocado.", "Mensaje público", "danger"),
            _opt("Preparar una entrevista juntos", {"relationship": 4, "manager_rating": 1, "fan": 1}, "El jugador sale preparado y el club controla el relato.", "Comunicación", "ok"),
        ], "La prensa está preguntando por mí y por el club. ¿Cómo prefieres que lo lleve?"
    if topic == "teammate":
        return [
            _opt("Reunir a los dos y mediar", {"relationship": 5, "cohesion": 2, "morale": 1}, "La disputa se rebaja y el grupo recupera aire.", "Mediación", "ok"),
            _opt("Castigar a los dos", {"relationship": -4, "cohesion": -2, "morale": -1}, "El grupo entiende la disciplina, pero el ambiente se enfría.", "Disciplina", "danger"),
            _opt("Dejar que lo arreglen ellos", {"relationship": -1, "cohesion": -1}, "La tensión sigue en el vestuario.", "Distancia", "warn"),
            _opt("Hablar con el líder del grupo", {"cohesion": 1, "relationship": 2, "manager_rating": 1}, "El vestuario se autorregula con tu ayuda.", "Liderazgo", "neutral"),
        ], "He tenido un roce con un compañero en el entrenamiento. Prefiero que lo sepas por mí."
    if topic == "ambition":
        return [
            _opt("Pelear por el título", {"morale": 2, "board": 2, "fan": 2, "cohesion": 1}, "El grupo se crece con el mensaje y la grada lo nota.", "Ambición", "ok"),
            _opt("Consolidar el proyecto", {"board": 1, "morale": 1, "cohesion": 1}, "Mensaje sereno que protege al grupo de la presión.", "Proyecto", "neutral"),
            _opt("Pensar en el próximo partido", {"form": 0.2, "relationship": 1, "prep_bonus": 0.1}, "El foco baja al partido y el ruido se reduce.", "Foco", "neutral"),
            _opt("No poner techo", {"morale": 1, "fan": 1, "board": -1}, "La afición sueña; la junta prefiere prudencia.", "Sueño", "warn"),
        ], "El equipo está arriba. ¿Nos permitimos soñar o seguimos escondiéndonos?"
    # staff
    if topic == "staff_training":
        return [
            _opt("Subir la intensidad", {"prep_bonus": 0.25, "cohesion": 1, "fatigue": 3}, "El staff prepara una semana exigente; el grupo acusa la carga.", "Intensidad", "warn"),
            _opt("Priorizar recuperación", {"fatigue": -5, "morale": 1, "cohesion": 1}, "La semana baja revoluciones y el vestuario respira.", "Recuperación", "ok"),
            _opt("Sesión de vídeo y rival", {"prep_bonus": 0.35, "manager_rating": 1}, "El análisis del rival gana peso en el plan.", "Vídeo", "ok"),
            _opt("Dejar el plan al segundo", {"relationship": 2, "cohesion": 1, "prep_bonus": 0.1}, "El staff agradece la confianza y asume el mando.", "Delegación", "neutral"),
        ], "Entrenador, ¿cómo quieres enfocar la semana? Podemos apretar, recuperar o cargar el vídeo del rival."
    if topic == "staff_rival":
        return [
            _opt("Presión alta y ritmo", {"prep_bonus": 0.3, "form": 0.2, "fatigue": 2}, "El plan apuesta por ahogar al rival desde el inicio.", "Presión", "warn"),
            _opt("Bloque medio y orden", {"prep_bonus": 0.25, "cohesion": 1, "form": 0.1}, "El equipo prioriza no conceder espacios.", "Orden", "ok"),
            _opt("Explotar el set piece", {"prep_bonus": 0.35, "manager_rating": 1}, "El staff dedica la sesión a los penaltis córner.", "Set pieces", "ok"),
            _opt("Confiar en el plan automático", {"relationship": 2, "prep_bonus": 0.15}, "El analista prepara una propuesta equilibrada.", "Confianza", "neutral"),
        ], "He preparado el informe del rival. ¿Qué quieres priorizar en el plan de partido?"
    if topic == "staff_squad":
        return [
            _opt("Reunión de grupo", {"cohesion": 2, "morale": 1, "relationship": 2}, "El staff convoca una charla abierta y el clima mejora.", "Reunión", "ok"),
            _opt("Hablar con los líderes", {"cohesion": 1, "relationship": 2, "manager_rating": 1}, "Los capitanes ayudan a sostener al grupo.", "Liderazgo", "ok"),
            _opt("Apretar la exigencia", {"form": 0.2, "morale": -1, "cohesion": -1}, "La exigencia sube, pero el ambiente se tensa.", "Exigencia", "warn"),
            _opt("Bajar el ruido y descansar", {"morale": 1, "fatigue": -3}, "El grupo desconecta y recupera energía.", "Descanso", "neutral"),
        ], "El vestuario tiene días buenos y días raros. ¿Cómo quieres que lo gestione esta semana?"
    if topic == "staff_market":
        return [
            _opt("Buscar un perfil concreto", {"prep_bonus": 0.1, "manager_rating": 1, "relationship": 2}, "El ojeador recibe una misión clara y se pone a trabajar.", "Scouting", "ok"),
            _opt("Priorizar renovaciones", {"cohesion": 1, "board": 1, "relationship": 2}, "El staff centra el foco en proteger la plantilla.", "Contratos", "neutral"),
            _opt("Escuchar ofertas por todos", {"board": 2, "morale": -1, "relationship": -1}, "La junta aprueba la apertura; el vestuario no lo ve igual.", "Mercado", "warn"),
            _opt("No tocar nada", {"relationship": 1, "cohesion": 1}, "El staff respira y el grupo mantiene la calma.", "Estabilidad", "ok"),
        ], "El mercado sigue moviéndose. ¿Qué perfil buscamos y hasta dónde estamos dispuestos a llegar?"
    if topic == "staff_fitness":
        return [
            _opt("Reducir carga", {"fatigue": -6, "form": -0.1, "relationship": 2}, "El preparador físico baja revoluciones y protege al grupo.", "Descarga", "ok"),
            _opt("Mantener el plan", {"form": 0.2, "fatigue": 1, "prep_bonus": 0.1}, "El equipo sigue el plan sin sorpresas.", "Continuidad", "neutral"),
            _opt("Apretar físicamente", {"form": 0.3, "fatigue": 4, "prep_bonus": 0.2}, "La carga sube y el riesgo de lesión también.", "Carga", "warn"),
            _opt("Trabajo individual", {"relationship": 3, "injury": -1, "form": 0.1}, "El staff diseña un plan para los jugadores más cargados.", "Individual", "ok"),
        ], "Tenemos jugadores al límite. ¿Cómo quieres gestionar la carga esta semana?"
    if topic == "staff_youth":
        return [
            _opt("Promocionar a un joven", {"cohesion": 1, "morale": 1, "manager_rating": 1}, "La cantera recibe un mensaje de confianza.", "Promoción", "ok"),
            _opt("Buscar una cesión", {"relationship": 2, "board": 1, "form": 0.1}, "El staff trabaja en una salida para que juegue.", "Cesión", "neutral"),
            _opt("Reforzar la academia", {"board": 2, "fan": 1, "academy": 2}, "El club apuesta por el futuro y la afición lo valora.", "Academia", "ok"),
            _opt("Mantener el plan actual", {"cohesion": 1, "relationship": 1}, "El staff sigue con el desarrollo previsto.", "Continuidad", "neutral"),
        ], "La cantera pide paso. ¿Qué hacemos con los jóvenes que están llamando a la puerta?"
    if topic == "staff_club":
        return [
            _opt("Apostar por el proyecto", {"board": 2, "fan": 1, "cohesion": 1}, "El staff comparte una visión ambiciosa y estable.", "Proyecto", "ok"),
            _opt("Cuidar las cuentas", {"board": 1, "relationship": 1, "morale": 0}, "La sostenibilidad manda; el staff entiende la prudencia.", "Cuentas", "neutral"),
            _opt("Pedir más recursos", {"board": -1, "manager_rating": 1, "fan": 1}, "La junta escucha, pero no promete nada.", "Recursos", "warn"),
            _opt("Proteger al grupo", {"cohesion": 2, "morale": 1, "relationship": 2}, "El staff se siente respaldado y el vestuario lo nota.", "Protección", "ok"),
        ], "La junta pregunta por el proyecto. ¿Qué les transmitimos y qué necesitas tú de verdad?"
    return [
        _opt("Hablar con claridad", {"relationship": 2, "morale": 1}, "La conversación deja un ambiente más limpio.", "Claridad", "ok"),
        _opt("Escuchar y no prometer", {"relationship": 1, "morale": 0}, "El jugador agradece que le escuches.", "Escucha", "neutral"),
    ], "Entrenador, ¿podemos hablar un momento?"


def _topic_label(topic_id: str, target_type: str) -> str:
    summary = _topics_staff({}) if target_type == "staff" else []
    for item in summary:
        if item["id"] == topic_id:
            return item["label"]
    # Fallback: derive a readable label from the id.
    return topic_id.replace("_", " ").capitalize()


def _topic_prompt_and_options(topic_id: str, ctx: dict[str, Any], target_type: str) -> tuple[str, list[dict[str, Any]]]:
    options, prompt = _options(topic_id, ctx)
    return prompt, options


def _resolve(state: GameState, target_type: str, target_id: str):
    if target_type == "player":
        target = next((p for p in state.user_team.players if p.id == target_id), None)
        if target is None:
            raise KeyError("Jugador no encontrado")
        return target, player_context(state, target)
    target = next((m for m in state.user_team.staff if m.role == target_id and m.role != "head_coach"), None)
    if target is None:
        raise KeyError("Empleado no encontrado")
    return target, staff_context(state, target)


def _message_id(day: date, target_id: str, count: int) -> str:
    return f"CH-{day.toordinal()}-{count}-{zlib.crc32(target_id.encode('utf-8')) % 10000}"


SPECIAL_TOPICS = {
    "family": ("Asunto personal", "Un tema de familia que afecta al jugador.", "Vestuario"),
    "media": ("Prensa", "La exposición pública del jugador y del club.", "Vestuario"),
    "teammate": ("Conflicto con un compañero", "Un roce que puede afectar al grupo.", "Vestuario"),
    "discipline": ("Disciplina", "Consecuencias y gestión de un incidente.", "Vestuario"),
}


def create_conversation(
    state: GameState,
    day: date,
    target_type: str,
    target_id: str,
    topic_id: str | None = None,
    custom_text: str = "",
) -> dict[str, Any]:
    target, ctx = _resolve(state, target_type, target_id)
    topics = _topics_player(ctx) if target_type == "player" else _topics_staff(ctx)
    if topic_id is None:
        topic_id = topics[0]["id"]
    if not any(item["id"] == topic_id for item in topics):
        special = SPECIAL_TOPICS.get(topic_id)
        if special:
            topics = topics + [_topic(topic_id, special[0], special[1], special[2])]
        else:
            raise KeyError("Tema no disponible para este objetivo")
    prompt, options = _topic_prompt_and_options(topic_id, ctx, target_type)
    prompt = custom_text or _contextual_prompt(topic_id, ctx, prompt)
    label = next((item["label"] for item in topics if item["id"] == topic_id), topic_id.replace("_", " ").title())
    name = target.name
    message = {
        "id": _message_id(day, target_id, len(state.chat_messages)),
        "date": day.isoformat(),
        "target_type": target_type,
        "target_id": target_id,
        "player_id": target.id if target_type == "player" else "",
        "staff_role": target.role if target_type == "staff" else "",
        "player_name": name,
        "target_name": name,
        "target_role": ctx.get("role", ""),
        "target_photo": getattr(target, "photo", ""),
        "target_initials": "".join(part[0] for part in name.split()[:2]).upper(),
        "team_id": state.club_id,
        "kind": topic_id,
        "topic": topic_id,
        "topic_label": label,
        "text": prompt,
        "options": options,
        "answered": False,
        "answer": "",
        "response": "",
        "relationship": ctx.get("relationship", 50),
        "stage": 0,
        "max_stage": 1,
        "status": "open",
        "turns": [{"speaker": "player", "text": prompt, "date": day.isoformat()}],
        "context": {
            "age": ctx.get("age"),
            "age_band": ctx.get("age_band"),
            "performance": ctx.get("performance"),
            "role": ctx.get("role"),
            "form": ctx.get("form"),
            "apps": ctx.get("apps"),
            "goals": ctx.get("goals"),
            "assists": ctx.get("assists"),
            "rating": ctx.get("rating"),
            "contract_status": ctx.get("contract_status"),
            "contract_until": ctx.get("contract_until"),
            "market_interest": ctx.get("market_interest"),
            "team_position": ctx.get("team_position"),
            "injury": ctx.get("injury"),
            "injury_type": ctx.get("injury_type"),
            "injury_severity": ctx.get("injury_severity"),
            "last_topic": ctx.get("last_topic"),
            "last_outcome": ctx.get("last_outcome"),
            "days_since_talk": ctx.get("days_since_talk"),
            "conversation_count": ctx.get("conversation_count"),
            "promises": ctx.get("promises", []),
        },
    }
    state.chat_messages = (state.chat_messages + [message])[-100:]
    state.daily_events = (
        state.daily_events
        + [
            {
                "date": day.isoformat(),
                "category": "Vestuario" if target_type == "player" else "Staff",
                "headline": f"{name} quiere hablar contigo",
                "body": message["text"],
                "important": False,
                "team_id": state.club_id,
                "player_id": message["player_id"],
                "league": state.competition,
                "type": "chat",
            }
        ]
    )[-240:]
    return message


def _apply_conversation_effects(
    state: GameState,
    target: Any,
    target_type: str,
    effects: dict[str, Any],
    option: dict[str, Any],
    message: dict[str, Any],
    day: date,
) -> None:
    if target_type == "player":
        player = target
        if "morale" in effects:
            player.morale = int(_clamp(player.morale + int(effects["morale"]), 1, 20))
        if "form" in effects:
            player.form = _clamp(player.form + float(effects["form"]), 1.0, 10.0)
        if "relationship" in effects:
            player.relationship = int(_clamp(player.relationship + int(effects["relationship"]), 0, 100))
        if "fatigue" in effects:
            player.fatigue = _clamp(player.fatigue + float(effects["fatigue"]), 0.0, 100.0)
        if "injury" in effects:
            player.injury = int(max(0, player.injury + int(effects["injury"])))
        if "suspension" in effects:
            player.suspension = int(max(0, player.suspension + int(effects["suspension"])))
        if effects.get("note"):
            player.absence_note = str(effects["note"])
        if effects.get("promise"):
            promise_type = str(effects["promise"])
            due = day + timedelta(days=int(effects.get("promise_days", 21)))
            player.promises = (
                player.promises
                + [
                    {
                        "type": promise_type,
                        "text": str(effects.get("promise_text", option.get("label", "Promesa"))),
                        "created": day.isoformat(),
                        "due": due.isoformat(),
                        "status": "open",
                        "start_apps": player.apps,
                        "target_apps": player.apps + int(effects.get("promise_apps", 3)),
                        "contract_before": player.contract_until,
                        "salary_before": player.salary,
                    }
                ]
            )[-12:]
            message["promise"] = player.promises[-1]
    else:
        staff = target
        if "relationship" in effects:
            staff.relationship = int(_clamp(staff.relationship + int(effects["relationship"]), 0, 100))
        if "morale" in effects:
            staff.morale = int(_clamp(staff.morale + int(effects["morale"]), 1, 20))
        if "staff_rating" in effects:
            staff.rating = int(_clamp(staff.rating + int(effects["staff_rating"]), 40, 99))
    team = state.user_team
    if "cohesion" in effects:
        team.cohesion = int(_clamp(team.cohesion + int(effects["cohesion"]), 1, 20))
    if "manager_rating" in effects:
        team.manager_rating = int(_clamp(team.manager_rating + int(effects["manager_rating"]), 0, 100))
    if "board" in effects:
        team.board_confidence = int(_clamp(team.board_confidence + int(effects["board"]), 0, 100))
    if "fan" in effects:
        team.fan_confidence = int(_clamp(team.fan_confidence + int(effects["fan"]), 0, 100))
    if "fine" in effects:
        team.budget -= int(effects["fine"])
    if "prep_bonus" in effects:
        team.prep_bonus = _clamp(team.prep_bonus + float(effects["prep_bonus"]), -5.0, 5.0)
    if "academy" in effects:
        team.academy_rating = int(_clamp(team.academy_rating + int(effects["academy"]), 0, 100))


def _record_chat_event(state: GameState, message: dict[str, Any], body: str) -> None:
    target_type = message.get("target_type", "player")
    state.daily_events = (
        state.daily_events
        + [
            {
                "date": message.get("date", state.date),
                "category": "Vestuario" if target_type == "player" else "Staff",
                "headline": f"Conversación con {message.get('target_name', message.get('player_name', 'el jugador'))}",
                "body": body,
                "important": False,
                "team_id": state.club_id,
                "player_id": message.get("player_id", ""),
                "league": state.competition,
                "type": "chat",
            }
        ]
    )[-240:]


def apply_conversation_choice(state: GameState, message: dict[str, Any], option_index: int) -> dict[str, Any]:
    options = message.get("options", [])
    if not options:
        return {"ok": False, "message": "La conversación no tiene opciones."}
    option = options[max(0, min(int(option_index), len(options) - 1))]
    effects = option.get("effects", {})
    target_type = message.get("target_type", "player")
    target_id = message.get("target_id", message.get("player_id", ""))
    try:
        target, ctx = _resolve(state, target_type, target_id)
    except KeyError:
        return {"ok": False, "message": "El objetivo ya no está disponible."}
    day = date.fromisoformat(str(message.get("date", state.date)))
    turns = message.setdefault("turns", [])
    if not turns:
        turns.append({"speaker": "player", "text": message.get("text", ""), "date": day.isoformat()})
    turns.append(
        {
            "speaker": "manager",
            "text": option.get("label", ""),
            "headline": option.get("headline", ""),
            "tone": option.get("tone", "neutral"),
            "date": day.isoformat(),
        }
    )
    _apply_conversation_effects(state, target, target_type, effects, option, message, day)
    stage = int(message.get("stage", 0))
    max_stage = int(message.get("max_stage", 1))
    if stage < max_stage:
        prompt, follow_options = _follow_up_stage(message.get("topic", ""), ctx, option, target_type)
        message["stage"] = stage + 1
        message["text"] = prompt
        message["options"] = follow_options
        message["answer"] = option.get("label", "")
        message["headline"] = option.get("headline", "")
        message["tone"] = option.get("tone", "neutral")
        message["answered"] = False
        message["status"] = "open"
        reaction = str(option.get("response", "")).strip()
        turns.append({"speaker": "player", "text": f"{reaction}\n\n{prompt}".strip(), "date": day.isoformat()})
        return {
            "ok": True,
            "continued": True,
            "message": option.get("headline", "La conversación continúa."),
            "effects": effects,
        }
    closing = _closing_line(ctx, option, target_type)
    reaction = str(option.get("response", "")).strip()
    final_text = f"{reaction} {closing}".strip()
    turns.append({"speaker": "player", "text": final_text, "date": day.isoformat()})
    message["answered"] = True
    message["status"] = "closed"
    message["answer"] = option.get("label", "")
    message["response"] = final_text
    message["headline"] = option.get("headline", "")
    message["tone"] = option.get("tone", "neutral")
    message["relationship"] = target.relationship
    _record_chat_event(state, message, final_text)
    return {
        "ok": True,
        "continued": False,
        "message": option.get("headline", "Conversación registrada."),
        "effects": effects,
    }


def check_promises(state: GameState, day: date | None = None) -> list[dict[str, Any]]:
    """Comprueba promesas vencidas y convierte la conversación en consecuencias."""
    day = day or date.fromisoformat(state.date)
    checked = []
    for player in state.user_team.players:
        for promise in player.promises:
            if promise.get("status") != "open":
                continue
            try:
                due = date.fromisoformat(str(promise.get("due", day.isoformat())))
            except ValueError:
                due = day
            if due > day:
                continue
            promise_type = promise.get("type", "")
            if promise_type == "minutes":
                kept = player.apps >= int(promise.get("target_apps", player.apps + 3))
            elif promise_type == "renewal":
                kept = player.contract_until != promise.get("contract_before") or player.salary > int(promise.get("salary_before", player.salary))
            else:
                kept = True
            promise["status"] = "kept" if kept else "broken"
            promise["checked"] = day.isoformat()
            if kept:
                player.relationship = int(_clamp(player.relationship + 4, 0, 100))
                player.morale = int(_clamp(player.morale + 1, 1, 20))
                body = f"{player.name} ha visto cumplida la promesa: {promise.get('text', '')}."
            else:
                player.relationship = int(_clamp(player.relationship - 7, 0, 100))
                player.morale = int(_clamp(player.morale - 2, 1, 20))
                body = f"{player.name} siente que la promesa no se ha cumplido: {promise.get('text', '')}."
            _record_chat_event(
                state,
                {
                    "target_type": "player",
                    "target_name": player.name,
                    "player_id": player.id,
                    "date": day.isoformat(),
                },
                body,
            )
            checked.append({"player_id": player.id, "promise": promise, "kept": kept})
    return checked


def random_conversation(state: GameState, day: date, rng: random.Random | None = None) -> dict[str, Any] | None:
    rng = rng or random.Random(0)
    targets: list[tuple[str, str]] = [("player", p.id) for p in state.user_team.players]
    targets += [("staff", m.role) for m in state.user_team.staff if m.role != "head_coach"]
    if not targets:
        return None
    pending = {(m.get("target_type"), m.get("target_id")) for m in state.chat_messages if not m.get("answered")}
    choices = [item for item in targets if item not in pending] or targets
    weights = []
    for target_type, target_id in choices:
        ctx = player_context(state, next(p for p in state.user_team.players if p.id == target_id)) if target_type == "player" else staff_context(state, next(m for m in state.user_team.staff if m.role == target_id))
        weight = 1.0 + max(0, 50 - int(ctx.get("relationship", 50))) / 18.0
        weight += max(0, 10 - int(ctx.get("morale", 10))) / 10.0
        if ctx.get("contract_status") in ("expira", "cerca"):
            weight += 1.2
        if ctx.get("injury") or ctx.get("suspension"):
            weight += 1.0
        if ctx.get("market_interest"):
            weight += 0.8
        weights.append(weight)
    target_type, target_id = rng.choices(choices, weights=weights, k=1)[0]
    topics = topics_for_target(state, target_type, target_id)["topics"]
    available = [topic for topic in topics if not topic.get("recent")]
    if not available:
        available = topics
    recommended = [topic for topic in available if topic.get("recommended")]
    pool = recommended if recommended and rng.random() < 0.65 else available
    topic = rng.choice(pool)
    return create_conversation(state, day, target_type, target_id, topic["id"])


def add_player_chat(
    state: GameState,
    day: date,
    player: PlayerState,
    kind: str = "role",
    detail: str = "",
) -> dict[str, Any]:
    """Compatibilidad con la API antigua de eventos de vestuario."""
    mapping = {
        "minutes": "role",
        "mood": "club",
        "contract": "contract",
        "discipline": "discipline",
        "family": "family",
        "media": "media",
        "teammate": "teammate",
        "role": "role",
    }
    topic = mapping.get(kind, kind if kind in {t["id"] for t in _topics_player(player_context(state, player))} else "role")
    return create_conversation(state, day, "player", player.id, topic, custom_text=detail)
