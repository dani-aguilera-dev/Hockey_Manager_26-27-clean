"""Simulación día a día: calendario, eventos, noticias y vestuario.

La simulación diaria no juega partidos. Se detiene en la fecha del próximo
partido del usuario para que pueda preparar el once y decidir cómo jugarlo.
"""

from __future__ import annotations

import random
import zlib
from datetime import date, timedelta
from typing import Any

from .competitions import code_for_system, competition
from .models import GameState, PlayerState, TeamState
from .conversations import add_player_chat, check_promises, random_conversation


def _rng(state: GameState, day: date, salt: int = 0) -> random.Random:
    return random.Random(state.seed * 10000 + day.toordinal() * 37 + salt)


def add_event(
    state: GameState,
    day: date,
    category: str,
    headline: str,
    body: str,
    *,
    important: bool = False,
    team_id: str = "",
    player_id: str = "",
    league: str = "",
    kind: str = "news",
) -> dict[str, Any]:
    event = {
        "date": day.isoformat(),
        "category": category,
        "headline": headline,
        "body": body,
        "important": important,
        "team_id": team_id,
        "player_id": player_id,
        "league": league,
        "type": kind,
    }
    if any(e.get("headline") == headline for e in state.daily_events[-4:]):
        return event
    state.daily_events = (state.daily_events + [event])[-240:]
    if important:
        state.inbox = (
            state.inbox
            + [
                {
                    "date": day.isoformat(),
                    "from": category,
                    "subject": headline,
                    "body": body,
                }
            ]
        )[-80:]
    return event


def _pick_player(state: GameState, rng: random.Random) -> PlayerState:
    pool = state.user_team.available_players or state.user_team.players
    return rng.choice(pool)


def _league_event(state: GameState, day: date, rng: random.Random) -> None:
    table = state.table()
    if not table:
        return
    leader = table[0]
    user_pos = next((i for i, t in enumerate(table, 1) if t.id == state.club_id), 0)
    next_fx = state.next_user_fixture()
    rival = ""
    if next_fx:
        rival = (
            state.teams[next_fx.away_id].name if next_fx.home_id == state.club_id else state.teams[next_fx.home_id].name
        )
    if not any(t.played for t in state.teams.values() if t.league == state.competition):
        preseason = [
            (
                f"{state.competition}: cuenta atrás para el arranque",
                "Los clubes ultiman la pretemporada. La clasificación todavía no refleja partidos oficiales.",
            ),
            (
                "Pretemporada: sesiones y pruebas",
                f"Los técnicos de {state.competition} siguen ajustando sistemas y minutos de pretemporada.",
            ),
            (
                "La liga calienta motores",
                f"A falta de competición oficial, los clubes de {state.competition} cierran su preparación.",
            ),
            (
                "Últimos días para cerrar la plantilla",
                "El mercado sigue abierto y los clubes valoran sus últimas incorporaciones.",
            ),
        ]
        headline, body = rng.choice(preseason)
        add_event(state, day, "Liga", headline, body, league=state.competition, important=False)
        return
    variants = [
        (
            f"{leader.name} lidera {state.competition}",
            f"El líder suma {leader.points} puntos. {state.user_team.name} es {user_pos}º."
            + (f" Próximo rival: {rival}." if rival else ""),
        ),
        (
            "La zona alta aprieta",
            f"{leader.name} marca el ritmo y {state.user_team.name} pelea desde la {user_pos}ª plaza.",
        ),
        (
            "La jornada se acerca",
            f"Los clubes de {state.competition} preparan una nueva fecha de liga. El liderato está en juego.",
        ),
        (
            "Parte médico de la liga",
            f"Varios equipos ajustan sus plantillas antes de la próxima jornada de {state.competition}.",
        ),
    ]
    headline, body = rng.choice(variants)
    add_event(state, day, "Liga", headline, body, league=state.competition, important=False)


def _other_league_event(state: GameState, day: date, rng: random.Random) -> None:
    current_system = competition(state.competition).system
    national_codes = {code_for_system("dha"), code_for_system("dhb_two_phase")}
    if current_system in ("dha", "dhb_two_phase"):
        other_system = "dhb_two_phase" if current_system == "dha" else "dha"
        other = code_for_system(other_system)
        teams = [t for t in state.teams.values() if t.league == other]
    else:
        teams = [t for t in state.teams.values() if t.league not in national_codes and t.league != state.competition]
        other = rng.choice(sorted({t.league for t in teams})) if teams else ""
    if not teams:
        return
    team = rng.choice(teams)
    if rng.random() < 0.5:
        headline = f"{team.name} prepara su próximo compromiso"
        body = f"En {other}, el club afina la semana con la vista puesta en la competición."
    else:
        headline = f"Movimiento en {other}: el mercado sigue vivo"
        body = f"{team.name} es uno de los clubes que sigue peinando el mercado en busca de refuerzos."
    add_event(state, day, "Otras ligas", headline, body, league=other, important=False)


def _market_event(state: GameState, day: date, rng: random.Random) -> None:
    teams = [
        t
        for t in state.teams.values()
        if (t.league in {code_for_system("dha"), code_for_system("dhb_two_phase")} or t.league == state.competition) and t.id != state.club_id
    ]
    if not teams:
        return
    team = rng.choice(teams)
    players = [p for p in team.players if p.available]
    if not players:
        return
    player = rng.choice(players)
    add_event(
        state,
        day,
        "Mercado",
        f"{team.name} sigue de cerca a {player.name}",
        f"El {player.subposition.lower()} de {player.age} años entra en la lista de clubes que buscan reforzar su plantilla.",
        player_id=player.id,
        team_id=team.id,
        league=team.league,
    )


def _performance_event(state: GameState, day: date, rng: random.Random) -> None:
    table = state.table()
    if not table:
        return
    user = state.user_team
    position = next((i for i, t in enumerate(table, 1) if t.id == user.id), 0)
    played = [f for f in state.fixtures if f.phase == "regular" and f.played and user.id in (f.home_id, f.away_id)]
    form = []
    for fixture in sorted(played, key=lambda f: f.round)[-5:]:
        gf = fixture.home_goals if fixture.home_id == user.id else fixture.away_goals
        ga = fixture.away_goals if fixture.home_id == user.id else fixture.home_goals
        form.append("V" if gf > ga else ("E" if gf == ga else "D"))
    form_text = " ".join(form) if form else "sin partidos"
    top = max(user.players, key=lambda p: (p.season_goals, p.overall), default=None)
    headline = rng.choice(
        [
            f"{user.name} busca regularidad en {state.competition}",
            f"El vestuario analiza la forma de {user.name}",
            f"{position}º puesto: el siguiente paso de {user.name}",
        ]
    )
    body = f"El equipo es {position}º con {user.points} puntos y forma {form_text}."
    if top:
        body += f" {top.name} es el referente ofensivo con {top.season_goals} goles."
    add_event(state, day, "Rendimiento", headline, body, team_id=user.id, player_id=top.id if top else "", league=state.competition)


def _rumor_event(state: GameState, day: date, rng: random.Random) -> None:
    teams = [t for t in state.teams.values() if t.league == state.competition and t.id != state.club_id]
    if not teams:
        return
    seller = rng.choice(teams)
    buyer = rng.choice([t for t in teams if t.id != seller.id] or teams)
    candidates = [p for p in seller.players if p.age <= 31]
    if not candidates:
        return
    player = rng.choice(candidates)
    add_event(
        state,
        day,
        "Rumor",
        f"{buyer.name} sigue de cerca a {player.name}",
        f"El {player.subposition.lower()} de {player.age} años entra en la agenda de {buyer.name}. No hay oferta formal, pero el interés es real.",
        team_id=buyer.id,
        player_id=player.id,
        league=state.competition,
    )


def _injury_event(state: GameState, day: date, rng: random.Random) -> None:
    player = _pick_player(state, rng)
    if not player.available:
        return
    reason = rng.choice(["una sobrecarga muscular", "un esguince de tobillo", "un golpe en el entrenamiento", "una molestia en la rodilla"])
    injury_type = "muscular" if "muscular" in reason or "rodilla" in reason else ("esguince" if "esguince" in reason else "golpe")
    days_out = rng.randint(1, 5)
    severity = "leve" if days_out <= 2 else "moderada"
    player.injury = max(player.injury, days_out)
    player.injury_type = injury_type
    player.injury_severity = severity
    player.injury_started = day.isoformat()
    player.injury_expected = days_out
    player.absence_note = f"{injury_type.capitalize()} ({severity})"
    player.injury_history = (
        player.injury_history
        + [
            {
                "date": day.isoformat(),
                "type": injury_type,
                "severity": severity,
                "matches": days_out,
                "source": "daily",
            }
        ]
    )[-20:]
    player.form = max(1, player.form - 0.4)
    player.relationship = max(10, player.relationship - 1)
    add_event(
        state,
        day,
        "Enfermería",
        f"{player.name}, baja por {reason}",
        f"El cuerpo médico estima {days_out} partido(s) de baja. El jugador trabajará en recuperación.",
        important=True,
        team_id=state.club_id,
        player_id=player.id,
        league=state.competition,
    )


def _illness_event(state: GameState, day: date, rng: random.Random) -> None:
    player = _pick_player(state, rng)
    if not player.available:
        return
    days_out = rng.randint(1, 3)
    player.injury = max(player.injury, days_out)
    player.injury_type = "enfermedad"
    player.injury_severity = "leve"
    player.injury_started = day.isoformat()
    player.injury_expected = days_out
    player.absence_note = "Enfermedad"
    player.injury_history = (
        player.injury_history
        + [
            {
                "date": day.isoformat(),
                "type": "enfermedad",
                "severity": "leve",
                "matches": days_out,
                "source": "daily",
            }
        ]
    )[-20:]
    player.morale = max(1, player.morale - 1)
    add_event(
        state, day, "Enfermería",
        f"{player.name} causa baja por enfermedad",
        f"El jugador queda apartado {days_out} partido(s). El club activa el protocolo de recuperación.",
        important=True, team_id=state.club_id, player_id=player.id, league=state.competition,
    )


def _legal_event(state: GameState, day: date, rng: random.Random) -> None:
    player = _pick_player(state, rng)
    if not player.available:
        return
    days_out = rng.randint(1, 3)
    player.suspension = max(player.suspension, days_out)
    player.suspension_reason = "Citación judicial"
    player.suspension_started = day.isoformat()
    player.absence_note = "Citación judicial"
    player.morale = max(1, player.morale - 3)
    player.relationship = max(5, player.relationship - 4)
    add_event(
        state, day, "Sucesos",
        f"{player.name}, citado por un incidente fuera del club",
        "El jugador se vio envuelto en una pelea a la salida de una discoteca. El club abre un expediente interno y recibe una citación judicial; queda apartado hasta que se aclare el caso.",
        important=True, team_id=state.club_id, player_id=player.id, league=state.competition,
    )
    add_player_chat(
        state, day, player, kind="discipline",
        detail="Entrenador, sé que el club está en una situación delicada por lo que pasó. Necesito saber si vas a defenderme o si esto ha terminado aquí.",
    )


def _family_event(state: GameState, day: date, rng: random.Random) -> None:
    player = _pick_player(state, rng)
    player.morale = max(1, player.morale - 1)
    add_player_chat(
        state, day, player, kind="family",
        detail="Entrenador, en casa hay un asunto familiar que me está afectando. No quiero que el equipo pague las consecuencias, pero necesito hablar con alguien.",
    )


def _dressing_event(state: GameState, day: date, rng: random.Random) -> None:
    player = _pick_player(state, rng)
    teammate = rng.choice([p for p in state.user_team.players if p.id != player.id] or [player])
    player.relationship = max(5, player.relationship - 2)
    state.user_team.cohesion = max(1, state.user_team.cohesion - 1)
    add_event(
        state, day, "Vestuario",
        f"Tensión entre {player.name} y {teammate.name}",
        "Un roce en el entrenamiento obliga al cuerpo técnico a intervenir para que no afecte al grupo.",
        team_id=state.club_id, player_id=player.id, league=state.competition,
    )
    add_player_chat(state, day, player, kind="teammate")


def _media_event(state: GameState, day: date, rng: random.Random) -> None:
    player = _pick_player(state, rng)
    add_event(
        state, day, "Prensa",
        f"La prensa pregunta por {player.name}",
        "El jugador ha dado una entrevista personal y el club debe decidir cómo acompañarle ante los medios.",
        team_id=state.club_id, player_id=player.id, league=state.competition,
    )
    add_player_chat(state, day, player, kind="media")


def _training_event(state: GameState, day: date, rng: random.Random) -> None:
    player = _pick_player(state, rng)
    player.form = min(10, player.form + 0.2)
    player.morale = min(20, player.morale + 1)
    add_event(
        state,
        day,
        "Entrenamiento",
        f"Buena sesión de {player.name}",
        "El cuerpo técnico destaca su intensidad y su actitud durante el entrenamiento.",
        team_id=state.club_id,
        player_id=player.id,
        league=state.competition,
    )


def _club_event(state: GameState, day: date, rng: random.Random) -> None:
    team = state.user_team
    options = [
        ("La afición prepara el próximo partido", f"El club espera un gran ambiente en {team.stadium_name}."),
        ("Reunión de la junta directiva", f"La junta repasa el presupuesto y el objetivo: {team.board_expectation}."),
        ("La cantera vuelve a sonreír", "Los técnicos de la academia destacan el crecimiento de los jóvenes."),
        ("Nueva sesión de video", "El staff prepara el plan táctico para el siguiente rival."),
    ]
    headline, body = rng.choice(options)
    add_event(state, day, "Club", headline, body, team_id=state.club_id, league=state.competition)


def daily_tick(state: GameState, day: date | None = None) -> list[dict[str, Any]]:
    """Genera un día de vida del club. No juega partidos."""
    day = day or date.fromisoformat(state.date)
    rng = _rng(state, day)
    before = len(state.daily_events)

    # Recuperación diaria suave para el usuario.
    for player in state.user_team.players:
        player.fatigue = max(0.0, player.fatigue - 1.2)

    # El mercado se mantiene vivo mientras la ventana esté abierta.
    try:
        from .market import market_window

        if market_window(state) != "cerrado" and rng.random() < 0.22:
            _market_event(state, day, rng)
    except Exception:
        pass

    roll = rng.random()
    if roll < 0.07:
        _legal_event(state, day, rng)
    elif roll < 0.25:
        _injury_event(state, day, rng)
    elif roll < 0.33:
        _illness_event(state, day, rng)
    elif roll < 0.44:
        _training_event(state, day, rng)
    elif roll < 0.54:
        _dressing_event(state, day, rng)
    elif roll < 0.65:
        _family_event(state, day, rng)
    elif roll < 0.72:
        _media_event(state, day, rng)
    elif roll < 0.82:
        _league_event(state, day, rng)
    elif roll < 0.90:
        _other_league_event(state, day, rng)
    elif rng.random() < 0.55:
        _club_event(state, day, rng)

    if rng.random() < 0.16:
        _performance_event(state, day, rng)
    if rng.random() < 0.14:
        _rumor_event(state, day, rng)
    try:
        from .commercial import daily_commercial_tick

        daily_commercial_tick(state, day, rng)
    except Exception:
        pass
    try:
        from .market import daily_transfer_activity

        daily_transfer_activity(state, day, rng)
    except Exception:
        pass

    # Conversaciones de vestuario y staff: no saturamos; como máximo dos pendientes.
    unanswered = [m for m in state.chat_messages if not m.get("answered")]
    if len(unanswered) < 2 and rng.random() < 0.34:
        random_conversation(state, day, rng)

    # Eventos con decisión: activa cadenas programadas y, como máximo, abre
    # una nueva decisión importante por día.
    from .events import maybe_trigger_event, tick_events

    tick_events(state, day, rng)
    maybe_trigger_event(state, day, rng)
    check_promises(state, day)

    return state.daily_events[before:]


def _simulate_scheduled_ehl(state: GameState, day: date) -> None:
    """La EHL se resuelve automáticamente en sus fechas de calendario."""
    from .ehl import ROUND_LABELS, ehl_next_date, simulate_ehl_round

    guard = 0
    while state.ehl.get("active") and ehl_next_date(state) and day >= date.fromisoformat(ehl_next_date(state)):
        round_no = state.ehl.get("round", 1)
        simulate_ehl_round(state)
        add_event(
            state,
            day,
            "EHL",
            f"EHL · {ROUND_LABELS.get(round_no, 'Ronda')} resuelta",
            "Los resultados europeos actualizan el cuadro de la EHL.",
            league="EHL",
            important=round_no == 3,
        )
        guard += 1
        if guard > 4:
            break


def next_match_date(state: GameState) -> date | None:
    fixture = state.next_user_fixture()
    if not fixture:
        return None
    return date.fromisoformat(fixture.date)


def simulate_days(
    state: GameState,
    target_date: str | date | None = None,
    days: int = 1,
    stop_at_match: bool = True,
    stop_at_decision: bool = False,
) -> dict[str, Any]:
    """Avanza el calendario sin jugar partidos.

    Si se alcanza la fecha del próximo partido, se detiene ahí y devuelve
    ``stopped_at_match=True``. Nunca simula el partido por su cuenta.
    """
    if state.phase not in ("regular", "promotion"):
        return {"ok": False, "message": "La temporada no está en fase regular.", "days": 0}
    current = date.fromisoformat(state.date)
    match_day = next_match_date(state)
    if target_date:
        target = date.fromisoformat(target_date) if isinstance(target_date, str) else target_date
    else:
        target = current + timedelta(days=max(0, int(days)))
    if target < current:
        return {"ok": False, "message": "La fecha objetivo es anterior a hoy.", "days": 0}

    stopped = False
    if stop_at_match and match_day and target >= match_day:
        target = match_day
        stopped = True

    advanced = 0
    before_events = len(state.daily_events)
    pending_before = len(state.pending_events)
    stopped_decision = False
    while current < target:
        current += timedelta(days=1)
        state.date = current.isoformat()
        advanced += 1
        if stop_at_match and match_day and current >= match_day:
            break
        daily_tick(state, current)
        _simulate_scheduled_ehl(state, current)
        if stop_at_decision and len(state.pending_events) > pending_before:
            stopped_decision = True
            break

    hit_match = bool(match_day and date.fromisoformat(state.date) >= match_day and stopped)
    if hit_match:
        has_notice = any(e.get("type") == "matchday" and e.get("date") == state.date for e in state.daily_events[-8:])
        if not has_notice:
            rival = state.next_user_fixture()
            rival_name = ""
            if rival:
                rid = rival.away_id if rival.home_id == state.club_id else rival.home_id
                rival_name = state.teams[rid].name
            add_event(
                state,
                date.fromisoformat(state.date),
                "Partido",
                "Hoy hay partido" + (f" contra {rival_name}" if rival_name else ""),
                "El calendario se detiene en la fecha de partido para que prepares el once y decidas cómo jugarlo.",
                important=True,
                team_id=state.club_id,
                league=state.competition,
                kind="matchday",
            )
    return {
        "ok": True,
        "days": advanced,
        "date": state.date,
        "stopped_at_match": hit_match,
        "stopped_at_decision": stopped_decision,
        "match_date": match_day.isoformat() if match_day else "",
        "events": state.daily_events[before_events:] if advanced else [],
    }
