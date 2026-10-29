"""Premios y galardones de la competición.

Los premios salen de las estadísticas reales de la temporada: goles,
asistencias, rating, partidos y posición. No se inventan votos.
"""

from __future__ import annotations

from typing import Any

from .competitions import competition
from .models import GameState, PlayerState, TeamState
from .news import awards_for_last_match


def _league_players(state: GameState) -> list[tuple[PlayerState, TeamState]]:
    return [
        (player, team)
        for team in state.teams.values()
        if team.league == state.competition
        for player in team.players
        if player.apps > 0
    ]


def _award_row(award_id: str, label: str, player: PlayerState, team: TeamState, metric: str, value: float) -> dict[str, Any]:
    return {
        "id": award_id,
        "label": label,
        "player_id": player.id,
        "player_name": player.name,
        "team_id": team.id,
        "team_name": team.name,
        "position": player.subposition,
        "age": player.age,
        "overall": round(float(player.overall), 1),
        "apps": player.apps,
        "goals": player.season_goals,
        "assists": player.season_assists,
        "rating": round(float(player.rating), 2),
        "metric": metric,
        "value": round(float(value), 2),
    }


def _best_xi(players: list[tuple[PlayerState, TeamState]]) -> list[dict[str, Any]]:
    used: set[str] = set()
    rows: list[dict[str, Any]] = []

    def pick(group: str, count: int) -> None:
        candidates = [
            (player, team)
            for player, team in players
            if player.id not in used and player.position_group == group
        ]
        candidates.sort(key=lambda item: (-item[0].rating, -item[0].overall, item[0].name))
        for player, team in candidates[:count]:
            used.add(player.id)
            rows.append(_award_row(f"xi-{group}-{len(rows)}", "Once ideal", player, team, "rating", player.rating))

    pick("Portero", 1)
    pick("Defensa", 4)
    pick("Medio", 3)
    pick("Delantero", 3)
    if len(rows) < 11:
        rest = sorted(
            [(player, team) for player, team in players if player.id not in used],
            key=lambda item: (-item[0].rating, -item[0].overall, item[0].name),
        )
        for player, team in rest[: 11 - len(rows)]:
            rows.append(_award_row(f"xi-extra-{len(rows)}", "Once ideal", player, team, "rating", player.rating))
    return rows[:11]


def season_awards(state: GameState) -> dict[str, Any]:
    players = _league_players(state)
    meta = competition(state.competition)
    if not players:
        return {
            "season": state.season,
            "competition": meta.short_name,
            "awards": [],
            "best_xi": [],
        }
    by_goals = max(players, key=lambda item: (item[0].season_goals, item[0].season_assists, item[0].rating))
    eligible_rating = [item for item in players if item[0].apps >= 3] or players
    by_rating = max(eligible_rating, key=lambda item: (item[0].rating, item[0].overall))
    young = [item for item in players if item[0].age <= 21]
    by_young = max(young, key=lambda item: (item[0].rating, item[0].season_goals, item[0].overall)) if young else None
    keepers = [item for item in players if item[0].subposition == "Portero"]
    by_keeper = max(keepers, key=lambda item: (item[0].rating, item[0].overall)) if keepers else None
    defenders = [item for item in players if item[0].position_group == "Defensa"]
    by_defender = max(defenders, key=lambda item: (item[0].rating, item[0].overall)) if defenders else None
    awards = [
        _award_row("top_scorer", "Máximo goleador", by_goals[0], by_goals[1], "goles", by_goals[0].season_goals),
        _award_row("mvp", "MVP de la temporada", by_rating[0], by_rating[1], "rating", by_rating[0].rating),
    ]
    if by_young:
        awards.append(_award_row("young", "Mejor joven", by_young[0], by_young[1], "rating", by_young[0].rating))
    if by_keeper:
        awards.append(_award_row("goalkeeper", "Mejor portero", by_keeper[0], by_keeper[1], "rating", by_keeper[0].rating))
    if by_defender:
        awards.append(_award_row("defender", "Mejor defensa", by_defender[0], by_defender[1], "rating", by_defender[0].rating))
    return {
        "season": state.season,
        "competition": meta.short_name,
        "awards": awards,
        "best_xi": _best_xi(players),
    }


def archive_season_awards(state: GameState) -> dict[str, Any]:
    payload = season_awards(state)
    if not payload["awards"]:
        return payload
    if any(item.get("season") == state.season and item.get("competition") == payload["competition"] for item in state.awards_history):
        return payload
    state.awards_history.append(
        {
            "season": state.season,
            "competition": payload["competition"],
            "awards": payload["awards"],
            "best_xi": payload["best_xi"],
        }
    )
    state.awards_history = state.awards_history[-20:]
    return payload


def awards_overview(state: GameState) -> dict[str, Any]:
    current = season_awards(state)
    return {
        **current,
        "last_match": awards_for_last_match(state),
        "history": list(reversed(state.awards_history[-10:])),
    }
