"""Equipos y competiciones regionales jugables.

Los equipos se construyen con las plantillas reales descargadas de iSquad.
No se inventan jugadores: si un equipo no tiene plantilla pública, no entra
en el catálogo jugable.
"""

from __future__ import annotations

import json
from pathlib import Path

from .data_loader import load_lower_division_free_agents, load_teams, norm
from .models import TeamState, Tactics

DATA = Path(__file__).resolve().parents[1] / "data" / "regional_teams.json"


def _metadata() -> tuple[dict[str, dict], dict[str, dict]]:
    if not DATA.exists():
        return {}, {}
    rows = json.loads(DATA.read_text(encoding="utf-8"))
    by_name = {norm(row["name"]): row for row in rows}
    by_base = {norm(row["base_name"]): row for row in rows if row.get("base_name")}
    return by_name, by_base


def load_regional_teams() -> tuple[dict[str, TeamState], dict[str, dict], dict[str, dict]]:
    metadata, metadata_by_base = _metadata()
    lower_agents = load_lower_division_free_agents()
    grouped: dict[str, list] = {}
    for player in lower_agents:
        grouped.setdefault(player.origin_team, []).append(player)

    # San Fernando 1ª ya existe como equipo base; se incorpora a la liga 1A.
    # El nombre interno del filial puede llevar sufijo B, así que se busca por
    # `base_name` además de por el nombre visible.
    base_teams, _, _ = load_teams()
    # Los jugadores de DHA/DHB no pueden aparecer a la vez en un filial
    # regional. Se reservan sus nombres antes de repartir las plantillas.
    used_names: set[str] = {
        norm(player.name)
        for team in base_teams.values()
        if team.league in ("DHA", "DHB")
        for player in team.players
    }
    san_fernando = base_teams.get("san-fernando-andaluza")
    if san_fernando is not None:
        grouped.setdefault(san_fernando.name, san_fernando.players)

    def meta_for(team_name: str) -> dict | None:
        return metadata.get(norm(team_name)) or metadata_by_base.get(norm(team_name))

    def order(item: tuple[str, list]) -> tuple:
        team_name, _ = item
        meta = meta_for(team_name) or {}
        return (bool(meta.get("is_second_team")), meta.get("league", ""), team_name)

    teams: dict[str, TeamState] = {}
    clubs: dict[str, dict] = {}
    for team_name, players in sorted(grouped.items(), key=order):
        meta = meta_for(team_name)
        if not meta or not players:
            continue
        code = meta.get("league", "")
        if not code:
            continue
        # Los segundos equipos no pueden repetir jugadores del primer equipo.
        # Se recorre primero a los primeros equipos por el orden anterior.
        unique_players = []
        for player in players:
            key = norm(player.name)
            if not key or key in used_names:
                continue
            used_names.add(key)
            unique_players.append(player)
        players = unique_players
        if not players:
            continue
        for player in players:
            player.team_name = meta["name"]
            player.origin_team = ""
            player.league = code
            if not player.salary:
                player.salary = max(6000, int((player.overall - 40) * 1200))
        wage_budget = sum(max(0, int(player.salary)) for player in players)
        team = TeamState(
            id=meta["id"],
            name=meta["name"],
            league=code,
            city=meta.get("city", ""),
            community=meta.get("community", ""),
            players=players,
            tactics=Tactics(),
            stadium_name=meta.get("stadium_name", ""),
            stadium_capacity=int(meta.get("stadium_capacity", 300) or 300),
            board_expectation="Ascenso a DHB",
            board_patience=3,
            board_pressure="media",
            academy_rating=45,
            preferred_mode="bus",
            assistant_rating=50,
            budget=max(120000, wage_budget),
            wage_budget=wage_budget,
            transfer_budget=0,
            club_tier=1,
        )
        teams[team.id] = team
        clubs[team.id] = {
            "id": team.id,
            "name": team.name,
            "full_name": meta.get("club", team.name),
            "league": code,
            "city": team.city,
            "community": team.community,
            "stadium": {
                "name": team.stadium_name,
                "capacity": team.stadium_capacity,
            },
            "board": {
                "expectation": team.board_expectation,
                "patience": team.board_patience,
                "pressure": team.board_pressure,
            },
            "finances": {
                "tier": 1,
                "transfer_budget": 0,
                "wage_budget": wage_budget,
            },
            "is_second_team": bool(meta.get("is_second_team")),
            "parent_club": meta.get("parent_club", ""),
        }
    return teams, clubs, {}
