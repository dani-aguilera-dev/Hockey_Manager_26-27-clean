"""Calendario y clasificación de la DHA (Fase 1)."""

from __future__ import annotations

from datetime import date, timedelta

from .models import Fixture, TeamState


def _round_robin(ids: list[str]) -> list[list[tuple[str, str]]]:
    arr = list(ids)
    if len(arr) % 2:
        arr.append("BYE")
    n = len(arr)
    rounds = []
    for r in range(n - 1):
        pairs = []
        for i in range(n // 2):
            a, b = arr[i], arr[n - 1 - i]
            if a != "BYE" and b != "BYE":
                pairs.append((a, b) if r % 2 == 0 else (b, a))
        rounds.append(pairs)
        arr = [arr[0]] + [arr[-1]] + arr[1:-1]
    return rounds


def create_fixtures(team_ids: list[str], start: str = "2026-09-20", double: bool = True) -> list[Fixture]:
    if len(team_ids) < 2:
        raise ValueError("La liga debe tener al menos dos equipos")
    first = _round_robin(team_ids)
    second = [[(b, a) for a, b in rd] for rd in first]
    rounds = first + (second if double else [])
    fixtures: list[Fixture] = []
    d0 = date.fromisoformat(start)
    for i, rd in enumerate(rounds, 1):
        d = d0 + timedelta(days=7 * (i - 1))
        for j, (h, a) in enumerate(rd):
            fixtures.append(
                Fixture(
                    id=f"J{i}-{j + 1}",
                    round=i,
                    date=d.isoformat(),
                    home_id=h,
                    away_id=a,
                    phase="regular",
                )
            )
    return fixtures


def create_dha_fixtures(team_ids: list[str], start: str = "2026-09-20") -> list[Fixture]:
    if len(team_ids) != 12:
        raise ValueError("La DHA debe tener 12 equipos")
    return create_fixtures(team_ids, start)


def sort_table(teams: list[TeamState]) -> list[TeamState]:
    return sorted(teams, key=lambda t: (-t.points, -(t.goals_for - t.goals_against), -t.goals_for, t.name))


def reset_table(teams: dict[str, TeamState]) -> None:
    for t in teams.values():
        t.played = t.won = t.drawn = t.lost = 0
        t.goals_for = t.goals_against = t.points = 0


def apply_result(teams: dict[str, TeamState], home_id: str, away_id: str, hg: int, ag: int) -> None:
    h, a = teams[home_id], teams[away_id]
    h.played += 1
    a.played += 1
    h.goals_for += hg
    h.goals_against += ag
    a.goals_for += ag
    a.goals_against += hg
    if hg > ag:
        h.won += 1
        h.points += 3
        a.lost += 1
    elif hg < ag:
        a.won += 1
        a.points += 3
        h.lost += 1
    else:
        h.drawn += 1
        a.drawn += 1
        h.points += 1
        a.points += 1


def recompute_table(teams: dict[str, TeamState], fixtures: list[Fixture]) -> None:
    reset_table(teams)
    for f in fixtures:
        if f.played and f.phase == "regular":
            apply_result(teams, f.home_id, f.away_id, f.home_goals, f.away_goals)


def league_table(teams: dict[str, TeamState], league: str) -> list[TeamState]:
    return sort_table([t for t in teams.values() if t.league == league])


def dha_table(teams: dict[str, TeamState]) -> list[TeamState]:
    return league_table(teams, "DHA")


def top_four(teams: dict[str, TeamState]) -> list[TeamState]:
    return dha_table(teams)[:4]


def bottom_two(teams: dict[str, TeamState]) -> list[TeamState]:
    return dha_table(teams)[-2:]
