"""Validación de datos de la partida.

No sustituye a los tests: detecta inconsistencias de plantilla que pueden
pasar desapercibidas, como staff cargado como jugador, perfiles desconocidos,
edades imposibles o jugadores duplicados entre equipos y mercado.
"""

from __future__ import annotations

import json
from typing import Any

from .data_loader import STAFF_PROFILES
from .models import GameState, PlayerState

VALID_GROUPS = {"Portero", "Defensa", "Medio", "Delantero", "Polivalente"}
VALID_PROFILES = {"Jugador", "Invitado"}
SPANISH_TOP = {"DHA", "DHB"}


def _issue(kind: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"kind": kind, "message": message, **extra}


def validate_state(state: GameState) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    info: list[dict[str, Any]] = []
    seen_ids: dict[str, str] = {}
    seen_names: dict[str, str] = {}
    guests = 0

    def check_player(player: PlayerState, team_name: str) -> None:
        nonlocal guests
        profile = str(player.perfil or "").strip()
        if profile.lower() in STAFF_PROFILES:
            errors.append(_issue("staff_as_player", f"{player.name} es staff y aparece como jugador", player_id=player.id, team=team_name))
        elif profile not in VALID_PROFILES:
            warnings.append(_issue("unknown_profile", f"{player.name} tiene perfil desconocido: {profile or 'vacío'}", player_id=player.id, team=team_name))
        if profile == "Invitado":
            guests += 1
        if not 10 <= int(player.age) <= 75:
            errors.append(_issue("invalid_age", f"{player.name} tiene una edad imposible: {player.age}", player_id=player.id, team=team_name))
        elif int(player.age) > 50:
            warnings.append(_issue("unusual_age", f"{player.name} tiene una edad poco habitual: {player.age}", player_id=player.id, team=team_name))
        if player.position_group not in VALID_GROUPS:
            warnings.append(_issue("invalid_position_group", f"{player.name} tiene grupo posicional inválido: {player.position_group}", player_id=player.id, team=team_name))
        if player.id in seen_ids:
            errors.append(_issue("duplicate_id", f"{player.name} comparte id con {seen_ids[player.id]}", player_id=player.id, team=team_name))
        else:
            seen_ids[player.id] = team_name
        name_key = player.name.strip().upper()
        if name_key:
            if name_key in seen_names:
                warnings.append(_issue("duplicate_name", f"{player.name} aparece en {seen_names[name_key]} y en {team_name}", player_id=player.id, team=team_name))
            else:
                seen_names[name_key] = team_name
        if team_name != "Agente libre" and player.team_name != team_name:
            warnings.append(_issue("team_name_mismatch", f"{player.name} dice pertenecer a {player.team_name} pero está en {team_name}", player_id=player.id, team=team_name))

    for team in state.teams.values():
        if team.league in SPANISH_TOP and len(team.players) < 11:
            errors.append(_issue("short_roster", f"{team.name} tiene menos de 11 jugadores", team=team.name, count=len(team.players)))
        for player in team.players:
            check_player(player, team.name)
    for player in state.free_agents:
        check_player(player, "Agente libre")

    if guests:
        info.append(_issue("guest_profiles", f"Hay {guests} jugadores con perfil Invitado; se conservan en sus equipos", count=guests))
    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "info": info,
        "summary": {
            "teams": len(state.teams),
            "players": sum(len(team.players) for team in state.teams.values()),
            "free_agents": len(state.free_agents),
            "guests": guests,
            "errors": len(errors),
            "warnings": len(warnings),
        },
    }


def main() -> None:
    from .season import new_game

    state = new_game("cd-terrassa", "Auditoría de datos", seed=2026)
    print(json.dumps(validate_state(state), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
