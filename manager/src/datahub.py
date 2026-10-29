"""Data hub: análisis del rival e instrucciones de partido.

El data hub no inventa métricas: trabaja con el calendario, las estadísticas
guardadas en los partidos y la plantilla real del rival. Las instrucciones se
aplican después en `MatchEngine` como una penalización de ataque/defensa.
"""

from __future__ import annotations

from typing import Any

from . import rules
from .competitions import competition
from .models import GameState, PlayerState, TeamState


def _played_fixtures(state: GameState, team_id: str) -> list:
    pool = list(state.fixtures)
    for fixtures in state.league_fixtures.values():
        pool.extend(fixtures)
    by_id = {fixture.id: fixture for fixture in pool}
    return sorted(
        [
            fixture
            for fixture in by_id.values()
            if fixture.played and team_id in (fixture.home_id, fixture.away_id)
        ],
        key=lambda fixture: (fixture.date, fixture.round, fixture.id),
    )


def _form(state: GameState, team_id: str, limit: int = 5) -> str:
    rows = []
    for fixture in _played_fixtures(state, team_id)[-limit:]:
        gf = fixture.home_goals if fixture.home_id == team_id else fixture.away_goals
        ga = fixture.away_goals if fixture.home_id == team_id else fixture.home_goals
        rows.append("V" if gf > ga else ("E" if gf == ga else "D"))
    return " ".join(rows) if rows else "—"


def _position(state: GameState, team: TeamState) -> int:
    if state.competition == team.league:
        table = state.table()
    else:
        table = sorted(
            [item for item in state.teams.values() if item.league == team.league],
            key=lambda item: (-item.points, -(item.goals_for - item.goals_against), -item.goals_for, item.name),
        )
    return next((index for index, item in enumerate(table, 1) if item.id == team.id), 0)


def _stats(state: GameState, team: TeamState) -> dict[str, Any]:
    fixtures = _played_fixtures(state, team.id)
    goals_for = goals_against = shots = shots_on_target = pc = possession = 0.0
    wins = draws = losses = 0
    for fixture in fixtures:
        home = fixture.home_id == team.id
        gf = fixture.home_goals if home else fixture.away_goals
        ga = fixture.away_goals if home else fixture.home_goals
        goals_for += gf
        goals_against += ga
        if gf > ga:
            wins += 1
        elif gf == ga:
            draws += 1
        else:
            losses += 1
        stats = (fixture.home_stats if home else fixture.away_stats) or {}
        shots += float(stats.get("shots", 0) or 0)
        shots_on_target += float(stats.get("shots_on_target", 0) or 0)
        pc += float(stats.get("pc", 0) or 0)
        possession += float(stats.get("possession", 0) or 0)
    played = max(1, len(fixtures))
    return {
        "played": len(fixtures),
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "goals_for": int(goals_for),
        "goals_against": int(goals_against),
        "goals_per_game": round(goals_for / played, 2),
        "goals_against_per_game": round(goals_against / played, 2),
        "shots_per_game": round(shots / played, 1),
        "shots_on_target_per_game": round(shots_on_target / played, 1),
        "pc_per_game": round(pc / played, 1),
        "possession": round(possession / played, 1),
        "form": _form(state, team.id),
        "position": _position(state, team),
    }


def _threat_label(player: PlayerState) -> str:
    if player.subposition == "Portero":
        return "Muro"
    if player.position_group == "Delantero":
        return "Goleador"
    if player.position_group == "Medio":
        return "Motor"
    return "Solidez"


def _recommended_instruction(player: PlayerState) -> str:
    if player.subposition == "Portero":
        return ""
    if player.position_group == "Delantero":
        return "tight_marking"
    if player.position_group == "Medio":
        return "press"
    return "force_weak_side"


def _key_players(team: TeamState, limit: int = 6) -> list[dict[str, Any]]:
    rows = sorted(
        team.players,
        key=lambda player: (
            -(player.season_goals * 3 + player.overall + player.rating * 2),
            -player.overall,
            player.name,
        ),
    )[:limit]
    out = []
    for player in rows:
        status = "Baja" if player.injury else ("Sancionado" if player.suspension else "Disponible")
        out.append(
            {
                "id": player.id,
                "name": player.name,
                "position": player.subposition,
                "position_group": player.position_group,
                "age": player.age,
                "overall": round(float(player.overall), 1),
                "goals": player.season_goals,
                "assists": player.season_assists,
                "rating": round(float(player.rating), 2),
                "apps": player.apps,
                "status": status,
                "threat": _threat_label(player),
                "recommended_instruction": _recommended_instruction(player),
            }
        )
    return out


def _availability(team: TeamState) -> list[dict[str, Any]]:
    return [
        {
            "id": player.id,
            "name": player.name,
            "reason": player.absence_label,
            "injury": player.injury,
            "suspension": player.suspension,
        }
        for player in team.players
        if player.injury or player.suspension
    ]


def _head_to_head(state: GameState, user_id: str, opponent_id: str, limit: int = 5) -> list[dict[str, Any]]:
    rows = [
        fixture
        for fixture in state.fixtures
        if fixture.played and {fixture.home_id, fixture.away_id} == {user_id, opponent_id}
    ]
    rows.sort(key=lambda fixture: (fixture.date, fixture.round))
    out = []
    for fixture in rows[-limit:]:
        out.append(
            {
                "date": fixture.date,
                "round": fixture.round,
                "home_name": state.teams[fixture.home_id].name,
                "away_name": state.teams[fixture.away_id].name,
                "home_goals": fixture.home_goals,
                "away_goals": fixture.away_goals,
            }
        )
    return out


def _analysis(user_stats: dict[str, Any], opp_stats: dict[str, Any], key_players: list[dict[str, Any]]) -> list[str]:
    lines = []
    if opp_stats["goals_per_game"] >= 2.5:
        lines.append(f"El rival marca {opp_stats['goals_per_game']} goles por partido: llega con mucho peligro.")
    elif opp_stats["goals_per_game"] <= 1.0:
        lines.append("El rival tiene problemas para convertir: concede pocas ocasiones claras.")
    if opp_stats["goals_against_per_game"] >= 2.0:
        lines.append("El rival concede mucho atrás; hay espacios para atacar el área.")
    if opp_stats["possession"] >= 55:
        lines.append("Domina la posesión: la presión alta puede incomodarle la salida.")
    if opp_stats["shots_per_game"] >= 12:
        lines.append("Genera volumen de tiro; conviene proteger el círculo y evitar PC.")
    if user_stats["goals_against_per_game"] > opp_stats["goals_for"]:
        lines.append("Tu equipo concede más de lo que el rival suele marcar: la solidez defensiva es prioritaria.")
    if key_players:
        first = key_players[0]
        lines.append(f"Jugador a vigilar: {first['name']} ({first['position']}, {first['overall']}).")
    return lines[:6]


def _effect(opponent: TeamState, instructions: dict[str, str]) -> dict[str, Any]:
    attack = defense = 0.0
    players = 0
    for player_id, instruction in instructions.items():
        player = next((p for p in opponent.players if p.id == player_id), None)
        profile = rules.OPPOSITION_INSTRUCTIONS.get(instruction)
        if player is None or profile is None:
            continue
        attack += float(profile.get("attack", 0.0))
        defense += float(profile.get("defense", 0.0))
        players += 1
    return {"attack": round(attack, 2), "defense": round(defense, 2), "players": players}


def datahub_overview(state: GameState) -> dict[str, Any]:
    fixture = state.next_user_fixture()
    user = state.user_team
    if fixture is None:
        return {
            "fixture": None,
            "message": "No hay un partido oficial pendiente para analizar.",
            "options": [
                {"id": key, **value} for key, value in rules.OPPOSITION_INSTRUCTIONS.items()
            ],
        }
    user_side = 0 if fixture.home_id == user.id else 1
    opponent = state.teams[fixture.away_id if user_side == 0 else fixture.home_id]
    user_stats = _stats(state, user)
    opp_stats = _stats(state, opponent)
    key_players = _key_players(opponent)
    current = dict(state.opposition_instructions.get(opponent.id, {}))
    options = [{"id": key, **value} for key, value in rules.OPPOSITION_INSTRUCTIONS.items()]
    recommended = {
        player["id"]: player["recommended_instruction"]
        for player in key_players
        if player["recommended_instruction"]
    }
    return {
        "fixture": {
            "id": fixture.id,
            "date": fixture.date,
            "round": fixture.round,
            "phase": fixture.phase,
            "home_id": fixture.home_id,
            "away_id": fixture.away_id,
            "home_name": state.teams[fixture.home_id].name,
            "away_name": state.teams[fixture.away_id].name,
            "user_is_home": user_side == 0,
        },
        "user_side": user_side,
        "competition": {
            "code": competition(state.competition).code,
            "name": competition(state.competition).name,
            "short_name": competition(state.competition).short_name,
        },
        "user": {
            "id": user.id,
            "name": user.name,
            "stats": user_stats,
            "availability": _availability(user),
        },
        "opponent": {
            "id": opponent.id,
            "name": opponent.name,
            "league": opponent.league,
            "city": opponent.city,
            "stadium_name": opponent.stadium_name,
            "stats": opp_stats,
            "tactics": opponent.tactics.to_dict(),
            "availability": _availability(opponent),
        },
        "key_players": key_players,
        "head_to_head": _head_to_head(state, user.id, opponent.id),
        "analysis": _analysis(user_stats, opp_stats, key_players),
        "options": options,
        "instructions": current,
        "recommended": recommended,
        "effect": _effect(opponent, current),
    }


def set_instructions(state: GameState, opponent_id: str, instructions: dict[str, str]) -> dict[str, Any]:
    opponent = state.teams.get(opponent_id)
    if opponent is None or opponent.id == state.club_id:
        return {"ok": False, "message": "El rival no es válido."}
    valid_players = {player.id for player in opponent.players}
    clean: dict[str, str] = {}
    for player_id, instruction in (instructions or {}).items():
        if player_id in valid_players and instruction in rules.OPPOSITION_INSTRUCTIONS:
            clean[player_id] = instruction
    if clean:
        state.opposition_instructions[opponent_id] = clean
    else:
        state.opposition_instructions.pop(opponent_id, None)
    return {
        "ok": True,
        "message": f"Instrucciones guardadas para {opponent.name}.",
        "opponent_id": opponent_id,
        "instructions": clean,
    }
