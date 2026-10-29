"""Noticias avanzadas generadas desde el estado real de la partida.

Cada noticia lleva identificadores de equipos y jugadores relacionados para que
la interfaz pueda abrir sus fichas. Los premios individuales se calculan a
partir de las valoraciones y eventos del último partido.
"""

from __future__ import annotations

import hashlib
import random
from datetime import date
from typing import Any

from .models import GameState, PlayerState, TeamState


def _id(*parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return "N-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def _form(state: GameState, team_id: str, limit: int = 5) -> list[str]:
    played = [f for f in state.fixtures if f.phase == "regular" and f.played and team_id in (f.home_id, f.away_id)]
    played.sort(key=lambda f: f.round)
    out = []
    for f in played[-limit:]:
        gf = f.home_goals if f.home_id == team_id else f.away_goals
        ga = f.away_goals if f.home_id == team_id else f.home_goals
        out.append("V" if gf > ga else ("E" if gf == ga else "D"))
    return out


def _form_text(state: GameState, team_id: str) -> str:
    form = _form(state, team_id)
    return " ".join(form) if form else "sin partidos"


def _team_position(state: GameState, team_id: str) -> int:
    return next((i for i, t in enumerate(state.table(), 1) if t.id == team_id), 0)


def _team_by_name(state: GameState, name: str) -> TeamState | None:
    return next((t for t in state.teams.values() if t.name == name), None)


def _player_by_name(state: GameState, name: str) -> PlayerState | None:
    for team in state.teams.values():
        for player in team.players:
            if player.name == name:
                return player
    return next((p for p in state.free_agents if p.name == name), None)


def _event_counts(last_result: dict[str, Any]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for event in last_result.get("events", []):
        name = event.get("player_name")
        if not name:
            continue
        row = counts.setdefault(name, {"goals": 0, "assists": 0, "cards": 0})
        if event.get("type") == "goal":
            row["goals"] += 1
        if event.get("type") in ("card", "yellow", "red"):
            row["cards"] += 1
        # The engine includes the assistant in the goal text; use the explicit
        # player when available and leave assists as a best-effort extra.
        if event.get("type") == "goal" and "Asistencia de " in str(event.get("text", "")):
            assistant = str(event.get("text", "")).split("Asistencia de ", 1)[1].split(".")[0].strip()
            counts.setdefault(assistant, {"goals": 0, "assists": 0, "cards": 0})["assists"] += 1
    return counts


def awards_for_last_match(state: GameState) -> list[dict[str, Any]]:
    """Premios individuales del último partido del usuario."""
    result = state.last_result
    if not result:
        return []
    ratings = result.get("ratings") or {}
    counts = _event_counts(result)
    user = state.user_team
    players = [p for p in user.players if p.name in ratings]
    if not players:
        return []
    def rating(player: PlayerState) -> float:
        return float(ratings.get(player.name, 0))

    awards: list[dict[str, Any]] = []
    def add(award_id: str, label: str, player: PlayerState, metric: str, value: float) -> None:
        awards.append(
            {
                "id": award_id,
                "label": label,
                "player_id": player.id,
                "player_name": player.name,
                "team_id": user.id,
                "team_name": user.name,
                "metric": metric,
                "value": round(value, 2),
                "goals": counts.get(player.name, {}).get("goals", 0),
                "assists": counts.get(player.name, {}).get("assists", 0),
            }
        )

    mvp = max(players, key=rating)
    add("mvp", "MVP del partido", mvp, "rating", rating(mvp))
    scorers = sorted(players, key=lambda p: (counts.get(p.name, {}).get("goals", 0), rating(p)), reverse=True)
    if counts.get(scorers[0].name, {}).get("goals", 0) > 0:
        add("golden_boot", "Goleador del partido", scorers[0], "goles", counts[scorers[0].name]["goals"])
    keepers = [p for p in players if p.subposition == "Portero"]
    if keepers:
        add("wall", "Muro del partido", max(keepers, key=rating), "rating", rating(max(keepers, key=rating)))
    defenders = [p for p in players if p.position_group == "Defensa"]
    if defenders:
        add("defender", "Mejor defensa", max(defenders, key=rating), "rating", rating(max(defenders, key=rating)))
    youngsters = [p for p in players if p.age <= 21]
    if youngsters:
        add("young", "Joven del partido", max(youngsters, key=rating), "rating", rating(max(youngsters, key=rating)))
    return awards


def _match_news(state: GameState) -> dict[str, Any] | None:
    result = state.last_result
    if not result:
        return None
    awards = awards_for_last_match(state)
    top = awards[0] if awards else None
    top_player = next((p for p in state.user_team.players if top and p.id == top["player_id"]), None)
    home = _team_by_name(state, result.get("home_name", ""))
    away = _team_by_name(state, result.get("away_name", ""))
    team_ids = [t.id for t in (home, away) if t]
    player_ids = list(dict.fromkeys([a["player_id"] for a in awards]))
    body = (
        f"{result.get('home_name')} {result.get('home_goals')}-{result.get('away_goals')} {result.get('away_name')}. "
        f"{result.get('result')} para el equipo, con {result.get('user_goals', 0)} goles a favor y "
        f"{result.get('user_against', 0)} en contra."
    )
    if top:
        body += f" {top['player_name']} se llevó el MVP con {top['value']:.2f} de valoración."
    return {
        "id": _id("match", result.get("fixture_id"), result.get("round")),
        "category": "Partido",
        "headline": f"{result.get('home_name')} {result.get('home_goals')}-{result.get('away_goals')} {result.get('away_name')}",
        "body": body,
        "summary": f"Crónica, estadísticas y premios de la jornada {result.get('round', '')}.",
        "date": result.get("date", state.date),
        "hot": True,
        "importance": 5,
        "crest_id": home.id if home else state.club_id,
        "crest_id2": away.id if away else "",
        "photo": top_player.photo if top_player else "",
        "team_ids": team_ids,
        "player_ids": player_ids,
        "awards": awards,
        "stats": {
            "posesión": f"{result.get('home_stats', {}).get('possession', 0)}% - {result.get('away_stats', {}).get('possession', 0)}%",
            "tiros": f"{result.get('home_stats', {}).get('shots', 0)} - {result.get('away_stats', {}).get('shots', 0)}",
            "a puerta": f"{result.get('home_stats', {}).get('shots_on_target', 0)} - {result.get('away_stats', {}).get('shots_on_target', 0)}",
            "asistencia": result.get("attendance", 0),
        },
        "tags": ["crónica", "premios", "rendimiento"],
    }


def _preview_news(state: GameState) -> dict[str, Any] | None:
    fx = state.next_user_fixture()
    if not fx:
        return None
    home = state.teams[fx.home_id]
    away = state.teams[fx.away_id]
    user = state.user_team
    rival = away if home.id == user.id else home
    venue = "en casa" if home.id == user.id else "a domicilio"
    started = any(t.played for t in state.teams.values() if t.league == state.competition)
    position = _team_position(state, user.id)
    if state.phase == "promotion":
        group = next(
            (item for item in state.promotion.get("groups", []) if state.club_id in item.get("team_ids", [])),
            None,
        )
        group_name = group.get("name", "Fase Nacional") if group else "Fase Nacional"
        body = (
            f"{group_name} · {fx.date}. {user.name} juega {venue} la fase de ascenso a DHB "
            f"con forma {_form_text(state, user.id)}."
        )
    else:
        body = (
            f"Jornada {fx.round} · {fx.date}. {user.name} llega {venue} con forma {_form_text(state, user.id)} "
            f"y es {position}º en {state.competition}."
            if started
            else f"Jornada {fx.round} · {fx.date}. La temporada aún no ha empezado; el equipo ultima la pretemporada {venue}."
        )
    body += f" {rival.name} es {_team_position(state, rival.id)}º y llega con forma {_form_text(state, rival.id)}."
    return {
        "id": _id("preview", fx.id, state.date),
        "category": "Previa",
        "headline": f"{user.name} y {rival.name} miden su momento",
        "body": body,
        "summary": f"Todo lo que rodea al {home.name} - {away.name}: forma, bajas, datos y declaraciones.",
        "date": fx.date,
        "hot": True,
        "importance": 4,
        "crest_id": user.id,
        "crest_id2": rival.id,
        "team_ids": [home.id, away.id],
        "player_ids": [],
        "awards": [],
        "stats": {
            "forma local": _form_text(state, home.id),
            "forma visitante": _form_text(state, away.id),
            "posición local": f"{_team_position(state, home.id)}º",
            "posición visitante": f"{_team_position(state, away.id)}º",
        },
        "tags": ["previa", "datos", "rival"],
    }


def _performance_news(state: GameState) -> dict[str, Any] | None:
    table = state.table()
    if not table:
        return None
    user = state.user_team
    position = _team_position(state, user.id)
    form = _form(state, user.id)
    if not form:
        return None
    wins = form.count("V")
    losses = form.count("D")
    if wins >= 3:
        tone = "racha"
        headline = f"{user.name} entra en racha: {wins} victorias en los últimos {len(form)}"
        body = f"El equipo es {position}º con {user.points} puntos. La gestión del grupo y el rendimiento individual sostienen la escalada."
    elif losses >= 3:
        tone = "crisis"
        headline = f"{user.name} necesita una reacción: {losses} derrotas en los últimos {len(form)}"
        body = f"El equipo es {position}º con {user.points} puntos. La presión sobre el vestuario y la junta empieza a notarse."
    else:
        tone = "regularidad"
        headline = f"{user.name} busca regularidad en {state.competition}"
        body = f"El equipo es {position}º con {user.points} puntos y una forma reciente de {_form_text(state, user.id)}. El siguiente paso es convertir los empates en victorias."
    top = max(user.players, key=lambda p: (p.season_goals, p.overall), default=None)
    return {
        "id": _id("performance", user.id, state.round, state.date),
        "category": "Rendimiento",
        "headline": headline,
        "body": body,
        "summary": f"Análisis de la forma, la clasificación y los nombres propios del {user.name}.",
        "date": state.date,
        "hot": tone == "crisis",
        "importance": 4 if tone == "crisis" else 3,
        "crest_id": user.id,
        "team_ids": [user.id],
        "player_ids": [top.id] if top else [],
        "awards": [],
        "stats": {
            "posición": f"{position}º",
            "puntos": user.points,
            "forma": _form_text(state, user.id),
            "goleador": top.name if top else "—",
            "goles": top.season_goals if top else 0,
        },
        "tags": ["rendimiento", "clasificación", "análisis"],
    }


def _league_news(state: GameState) -> dict[str, Any] | None:
    table = state.table()
    if not table:
        return None
    leader = table[0]
    second = table[1] if len(table) > 1 else None
    if not any(t.played for t in state.teams.values() if t.league == state.competition):
        return {
            "id": _id("preseason", state.competition, state.date),
            "category": "Pretemporada",
            "headline": f"{state.competition}: la temporada está a punto",
            "body": "Los clubes ultiman la preparación. La clasificación todavía no refleja partidos oficiales.",
            "summary": "Guía de pretemporada, plantillas y objetivos de la competición.",
            "date": state.date,
            "hot": False,
            "importance": 2,
            "crest_id": leader.id,
            "team_ids": [leader.id],
            "player_ids": [],
            "awards": [],
            "stats": {"equipos": len(table)},
            "tags": ["pretemporada", "liga"],
        }
    gap = leader.points - second.points if second else 0
    body = f"{leader.name} manda con {leader.points} puntos y {leader.goals_for - leader.goals_against:+d} de diferencia."
    if second:
        body += f" {second.name} le sigue a {gap} punto(s)."
    return {
        "id": _id("league", state.competition, state.round, state.date),
        "category": "Liga",
        "headline": f"{leader.name} lidera {state.competition}",
        "body": body,
        "summary": f"La lucha por el título y la zona alta de {state.competition}.",
        "date": state.date,
        "hot": gap <= 2,
        "importance": 3,
        "crest_id": leader.id,
        "crest_id2": second.id if second else "",
        "team_ids": [t.id for t in (leader, second) if t],
        "player_ids": [],
        "awards": [],
        "stats": {
            "líder": leader.name,
            "puntos": leader.points,
            "segundo": second.name if second else "—",
            "diferencia": gap,
        },
        "tags": ["liga", "clasificación", "título"],
    }


def _market_news(state: GameState) -> dict[str, Any] | None:
    user = state.user_team
    if state.transfer_offers:
        offer = state.transfer_offers[0]
        player = next((p for p in user.players if p.id == offer.get("player_id")), None)
        from_team = state.teams.get(offer.get("from_club_id"))
        return {
            "id": _id("offer", offer.get("id"), state.date),
            "category": "Mercado",
            "headline": f"{offer.get('from_club_name', 'Un club')} pregunta por {offer.get('player_name', 'tu jugador')}",
            "body": f"Oferta de {int(offer.get('fee', 0)):,} € y salario de {int(offer.get('salary', 0)):,} €. La pelota está en tu tejado.".replace(",", "."),
            "summary": "Rumor real de mercado con oferta económica y contexto de plantilla.",
            "date": state.date,
            "hot": True,
            "importance": 4,
            "crest_id": user.id,
            "crest_id2": from_team.id if from_team else "",
            "team_ids": [t for t in (user.id, from_team.id if from_team else "") if t],
            "player_ids": [player.id] if player else [],
            "awards": [],
            "stats": {
                "traspaso": f"{int(offer.get('fee', 0)):,} €".replace(",", "."),
                "salario": f"{int(offer.get('salary', 0)):,} €".replace(",", "."),
                "club": offer.get("from_club_name", "—"),
            },
            "tags": ["mercado", "oferta", "rumor"],
        }
    if state.market_history:
        entry = state.market_history[-1]
        player = next((p for p in user.players if p.name == entry.get("player")), None)
        return {
            "id": _id("transfer", entry.get("player"), entry.get("round"), entry.get("season")),
            "category": "Mercado",
            "headline": f"{entry.get('player', 'Un jugador')} cambia de club",
            "body": f"{entry.get('from', '')} → {entry.get('to', '')}. {int(entry.get('fee', 0)):,} € de traspaso.".replace(",", "."),
            "summary": "Movimiento confirmado en el mercado.",
            "date": state.date,
            "hot": False,
            "importance": 3,
            "crest_id": user.id,
            "team_ids": [user.id],
            "player_ids": [player.id] if player else [],
            "awards": [],
            "stats": {"traspaso": f"{int(entry.get('fee', 0)):,} €".replace(",", "."), "temporada": entry.get("season", "")},
            "tags": ["mercado", "fichaje"],
        }
    return None


def _rumor_news(state: GameState) -> dict[str, Any] | None:
    """Rumor determinista basado en el estado real, no una noticia inventada."""
    teams = [t for t in state.teams.values() if t.league == state.competition and t.id != state.club_id]
    if not teams:
        return None
    rng = random.Random(state.seed * 1000 + date.fromisoformat(state.date).toordinal() + 17)
    candidates = []
    for team in teams:
        for player in team.players:
            if player.age <= 31 and player.overall >= 65:
                candidates.append((team, player))
    if not candidates:
        return None
    seller, player = rng.choice(candidates[:24])
    buyer = rng.choice([t for t in teams if t.id != seller.id] or teams)
    return {
        "id": _id("rumor", player.id, buyer.id, state.date),
        "category": "Rumor",
        "headline": f"{buyer.name} sigue de cerca a {player.name}",
        "body": f"El {player.subposition.lower()} de {player.age} años entra en la agenda de {buyer.name}. {seller.name} no ha recibido una oferta formal, pero el interés existe.",
        "summary": "Rumor de mercado generado desde el nivel, la edad y la situación real de la plantilla.",
        "date": state.date,
        "hot": False,
        "importance": 2,
        "crest_id": buyer.id,
        "crest_id2": seller.id,
        "team_ids": [buyer.id, seller.id],
        "player_ids": [player.id],
        "awards": [],
        "stats": {
            "jugador": player.name,
            "edad": player.age,
            "overall": f"{player.overall:.1f}",
            "club actual": seller.name,
            "interesado": buyer.name,
        },
        "tags": ["rumor", "mercado", "scouting"],
    }


def _top_scorers_news(state: GameState) -> dict[str, Any] | None:
    teams = [t for t in state.teams.values() if t.league == state.competition]
    players = [p for t in teams for p in t.players]
    if not players:
        return None
    ranking = sorted(players, key=lambda p: (p.season_goals, p.season_assists, p.overall), reverse=True)[:5]
    if ranking[0].season_goals <= 0:
        return None
    leader = ranking[0]
    owner = next((t for t in teams if leader in t.players), None)
    names = ", ".join(f"{p.name} ({p.season_goals})" for p in ranking[:3])
    return {
        "id": _id("scorers", state.competition, state.round, state.date),
        "category": "Rendimiento",
        "headline": f"{leader.name} lidera el gol en {state.competition}",
        "body": f"La tabla de goleadores la encabeza {leader.name} con {leader.season_goals} goles. Le siguen {names}.",
        "summary": "Clasificación de goleadores y nombres que están marcando la temporada.",
        "date": state.date,
        "hot": leader.season_goals >= 5,
        "importance": 3,
        "crest_id": owner.id if owner else state.club_id,
        "team_ids": [owner.id] if owner else [],
        "player_ids": [p.id for p in ranking[:3]],
        "awards": [],
        "stats": {f"{p.name}": f"{p.season_goals} goles" for p in ranking[:3]},
        "tags": ["goleadores", "rendimiento", "datos"],
    }


def _ehl_news(state: GameState) -> dict[str, Any] | None:
    ehl = state.ehl or {}
    if not ehl.get("active"):
        return None
    participants = ehl.get("participants") or []
    return {
        "id": _id("ehl", ehl.get("round"), state.date),
        "category": "Europa",
        "headline": f"La EHL entra en escena: {', '.join(participants[:3])}",
        "body": f"El torneo europeo afronta la ronda {ehl.get('round', 1)}. Los clubes españoles buscan dar el salto continental.",
        "summary": "Cuadro, participantes y calendario de la EHL.",
        "date": state.date,
        "hot": True,
        "importance": 4,
        "crest_id": state.club_id,
        "team_ids": [state.club_id],
        "player_ids": [],
        "awards": [],
        "stats": {"ronda": ehl.get("round", 1), "participantes": len(participants)},
        "tags": ["europa", "ehl", "competición"],
    }


def _injury_news(state: GameState) -> dict[str, Any] | None:
    injured = [p for p in state.user_team.players if p.injury or p.suspension]
    if not injured:
        return None
    player = injured[0]
    return {
        "id": _id("injury", player.id, state.date),
        "category": "Enfermería",
        "headline": f"{player.name}, baja por {player.absence_label.lower()}",
        "body": f"El cuerpo médico estima {player.injury or player.suspension} partido(s) de baja. El jugador trabajará en recuperación.",
        "summary": "Parte médico y efecto en la plantilla.",
        "date": state.date,
        "hot": False,
        "importance": 3,
        "crest_id": state.club_id,
        "team_ids": [state.club_id],
        "player_ids": [player.id],
        "awards": [],
        "stats": {"baja": player.injury or player.suspension, "motivo": player.absence_label},
        "tags": ["enfermería", "plantilla"],
    }


def _youth_news(state: GameState) -> dict[str, Any] | None:
    if not state.user_team.youth:
        return None
    best = max(state.user_team.youth, key=lambda p: p.potential)
    return {
        "id": _id("youth", best.id, state.date),
        "category": "Cantera",
        "headline": f"{best.name}, la perla que empuja desde abajo",
        "body": f"{best.youth_category} · {best.subposition} de {best.age} años · overall {best.overall:.1f} · potencial {best.potential:.1f}. La academia está en {state.user_team.academy_rating}/100.",
        "summary": "Seguimiento individual de la cantera.",
        "date": state.date,
        "hot": False,
        "importance": 2,
        "crest_id": state.club_id,
        "team_ids": [state.club_id],
        "player_ids": [best.id],
        "awards": [],
        "stats": {"potencial": f"{best.potential:.1f}", "academia": state.user_team.academy_rating},
        "tags": ["cantera", "futuro"],
    }


def _scouting_news(state: GameState) -> dict[str, Any] | None:
    fx = state.next_user_fixture()
    if not fx:
        return None
    home = state.teams[fx.home_id]
    away = state.teams[fx.away_id]
    user = state.user_team
    rival = away if home.id == user.id else home
    return {
        "id": _id("scouting", rival.id, fx.id),
        "category": "Scouting",
        "headline": f"Cómo juega {rival.name}",
        "body": f"Sale con {rival.tactics.formation}, mentalidad {rival.tactics.mentality.replace('_', ' ')} y presión {rival.tactics.press}. Moral {rival.morale}/20 y cohesión {rival.cohesion}/20.",
        "summary": "Informe de rival: sistema, moral y contexto.",
        "date": state.date,
        "hot": False,
        "importance": 3,
        "crest_id": rival.id,
        "team_ids": [rival.id],
        "player_ids": [],
        "awards": [],
        "stats": {
            "formación": rival.tactics.formation,
            "mentalidad": rival.tactics.mentality.replace("_", " "),
            "presión": rival.tactics.press,
            "moral": f"{rival.morale}/20",
        },
        "tags": ["scouting", "rival", "táctica"],
    }


def _club_news(state: GameState) -> dict[str, Any] | None:
    user = state.user_team
    return {
        "id": _id("club", user.id, state.date),
        "category": "Club",
        "headline": f"La junta mantiene la confianza en {user.name}",
        "body": f"Confianza {user.board_confidence}/100 · presión {user.board_pressure} · paciencia {user.board_patience}/5. Objetivo: {user.board_expectation}.",
        "summary": "Contexto institucional del club.",
        "date": state.date,
        "hot": user.board_confidence < 40,
        "importance": 3,
        "crest_id": user.id,
        "team_ids": [user.id],
        "player_ids": [],
        "awards": [],
        "stats": {"confianza": user.board_confidence, "presión": user.board_pressure, "objetivo": user.board_expectation},
        "tags": ["club", "junta"],
    }


def _cup_news(state: GameState) -> dict[str, Any] | None:
    if not state.cup_active:
        return None
    return {
        "id": _id("cup", state.cup_round, state.date),
        "category": "Copa",
        "headline": "La Copa del Rey entra en escena",
        "body": "Los ocho mejores de DHA se citan en un fin de semana de eliminatorias a partido único.",
        "summary": "Cuadro, resultados y premios de la Copa.",
        "date": state.date,
        "hot": True,
        "importance": 4,
        "crest_id": state.club_id,
        "team_ids": [state.club_id],
        "player_ids": [],
        "awards": [],
        "stats": {"ronda": state.cup_round},
        "tags": ["copa", "eliminatoria"],
    }



def _promotion_news(state: GameState) -> dict[str, Any] | None:
    """Noticia de la fase nacional de ascenso a DHB."""
    raw = state.promotion if state.phase == "promotion" else state.playout
    if not raw or raw.get("format") != "regional_promotion":
        return None
    groups = raw.get("groups", [])
    final_group = raw.get("final_group") or {}
    if not groups and not final_group:
        return None
    user = state.user_team
    group = next((item for item in groups if state.club_id in item.get("team_ids", [])), None)
    group_name = group.get("name", "") if group else ""
    qualified = [team for item in groups for team in item.get("team_ids", [])]
    qualified_names = [state.teams[tid].name for tid in qualified if tid in state.teams]
    table = (final_group or group or {}).get("table", [])
    lines = [f"{row['position']}. {row['team']} · {row['points']} pts" for row in table[:4]]
    if final_group:
        promoted = final_group.get("promoted_ids", [])
        promoted_names = [state.teams[tid].name for tid in promoted if tid in state.teams]
        headline = "La fase de ascenso a DHB llega a su liguilla final"
        body = (
            f"La fase final reúne a los cuatro campeones de grupo. "
            f"Ascenderán los dos primeros: {', '.join(promoted_names) if promoted_names else 'por decidir'}."
        )
    elif group:
        headline = f"{user.name} disputa el {group_name} por el ascenso a DHB"
        body = (
            f"El equipo está en la fase nacional junto a {len(qualified_names)} clubes. "
            f"Clasificación actual: {'; '.join(lines)}."
        )
    else:
        headline = "La fase de ascenso a DHB ya tiene sus cuatro grupos"
        body = (
            f"Los campeones de grupo buscarán las dos plazas de ascenso. "
            f"Equipos clasificados: {', '.join(qualified_names) if qualified_names else 'por confirmar'}."
        )
    return {
        "id": _id("promotion", state.season, state.promotion_round, group_name),
        "category": "Ascenso",
        "headline": headline,
        "body": body,
        "summary": "Fase Nacional de Primera División: grupos, liguilla final y dos plazas para DHB.",
        "date": state.date,
        "hot": True,
        "importance": 5,
        "crest_id": user.id,
        "team_ids": list(dict.fromkeys(qualified))[:8],
        "player_ids": [],
        "awards": [],
        "stats": {
            "grupo": group_name or "—",
            "equipos": len(qualified_names),
            "plazas": 2,
            "fase": "final" if final_group else "grupos",
        },
        "tags": ["ascenso", "DHB", "fase nacional"],
    }

def news_feed(state: GameState, limit: int = 20) -> list[dict[str, Any]]:
    items = [
        _match_news(state),
        _preview_news(state),
        _performance_news(state),
        _league_news(state),
        _market_news(state),
        _rumor_news(state),
        _top_scorers_news(state),
        _injury_news(state),
        _youth_news(state),
        _scouting_news(state),
        _club_news(state),
        _cup_news(state),
        _ehl_news(state),
        _promotion_news(state),
    ]
    return [item for item in items if item][:limit]
