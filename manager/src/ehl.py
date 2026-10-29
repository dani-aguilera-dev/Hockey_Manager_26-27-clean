"""EHL: torneo europeo simplificado de final a ocho."""

from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path

from .competitions import code_for_system
from .models import GameState

_DATA = Path(__file__).resolve().parents[1] / "data" / "ehl.json"
_CONFIG = json.loads(_DATA.read_text(encoding="utf-8"))
EHL_OFFSETS = list(_CONFIG["offsets_days"])
ROUND_LABELS = {int(key): value for key, value in _CONFIG["round_labels"].items()}
EURO_TEAMS = [
    (row["name"], row["country"], float(row["strength"]))
    for row in _CONFIG["european_teams"]
]
SPANISH_SLOTS = int(_CONFIG["spanish_slots"])
FOREIGN_SLOTS = int(_CONFIG["foreign_slots"])


def _strength(team) -> float:
    line, _ = team.auto_lineup()
    a, d = team.lineup_strength(line)
    return (a + d) / 2


def create_ehl(state: GameState) -> None:
    top_code = code_for_system("dha")
    dha = [t for t in state.teams.values() if t.league == top_code]
    dha.sort(key=lambda t: (-t.points, -(t.goals_for - t.goals_against), t.name))
    spanish = []
    for t in dha:
        if len(spanish) < 2:
            spanish.append(t)
    if state.cup_winner_id in state.teams and state.teams[state.cup_winner_id].league == top_code:
        cup = state.teams[state.cup_winner_id]
        if cup not in spanish:
            spanish.append(cup)
    for t in dha:
        if len(spanish) >= 3:
            break
        if t not in spanish:
            spanish.append(t)
    participants = []
    for i, t in enumerate(spanish[:SPANISH_SLOTS], 1):
        participants.append(
            {"id": t.id, "name": t.name, "country": "España", "strength": _strength(t), "spanish": True}
        )
    for i, (name, country, strength) in enumerate(EURO_TEAMS[:FOREIGN_SLOTS], 1):
        participants.append(
            {"id": f"euro-{i}", "name": name, "country": country, "strength": strength, "spanish": False}
        )
    rng = random.Random(state.seed + int(state.season[:4]) + 909)
    rng.shuffle(participants)
    fixtures = []
    for i in range((SPANISH_SLOTS + FOREIGN_SLOTS) // 2):
        fixtures.append(
            {
                "home": participants[2 * i],
                "away": participants[2 * i + 1],
                "home_goals": 0,
                "away_goals": 0,
                "played": False,
                "winner_id": "",
            }
        )
    first = next((f for f in state.fixtures if f.phase == "regular"), None)
    base = date.fromisoformat(first.date) if first else date.fromisoformat(state.date)
    dates = [(base + timedelta(days=offset)).isoformat() for offset in EHL_OFFSETS]
    state.ehl = {
        "round": 1,
        "fixtures": fixtures,
        "winner_id": "",
        "active": True,
        "participants": [p["name"] for p in participants],
        "dates": dates,
        "results": [],
    }


def _sim_match(home, away, rng):
    hs, as_ = home["strength"], away["strength"]
    hg = max(0, int(rng.gauss(2.6 + (hs - as_) / 18, 1.3)))
    ag = max(0, int(rng.gauss(2.2 + (as_ - hs) / 18, 1.3)))
    winner = home["id"] if hg > ag else (away["id"] if ag > hg else "")
    if not winner:
        winner = home["id"] if rng.random() < 0.5 + (hs - as_) / 100 else away["id"]
    return hg, ag, winner


def ehl_next_date(state: GameState) -> str:
    ehl = state.ehl
    if not ehl or not ehl.get("active"):
        return ""
    dates = ehl.get("dates", [])
    index = max(0, min(len(dates) - 1, int(ehl.get("round", 1)) - 1))
    return dates[index] if dates else ""


def ehl_status_text(state: GameState) -> str:
    ehl = state.ehl
    if not ehl:
        return "Pendiente"
    if ehl.get("active"):
        return f"{ROUND_LABELS.get(ehl.get('round', 1), 'Ronda')} · {ehl_next_date(state)}"
    return f"Campeón: {ehl.get('winner_name', '—')}"


def simulate_ehl_round(state: GameState) -> None:
    ehl = state.ehl
    if not ehl or not ehl.get("active"):
        return
    round_no = ehl["round"]
    rng = random.Random(state.seed + 1200 + ehl["round"])
    winners = []
    for fx in ehl["fixtures"]:
        if not fx["played"]:
            hg, ag, win = _sim_match(fx["home"], fx["away"], rng)
            fx["home_goals"], fx["away_goals"], fx["winner_id"], fx["played"] = hg, ag, win, True
        if fx["winner_id"]:
            winners.append(fx["home"] if fx["winner_id"] == fx["home"]["id"] else fx["away"])
    ehl.setdefault("results", []).append(
        {
            "round": round_no,
            "label": ROUND_LABELS.get(round_no, f"Ronda {round_no}"),
            "fixtures": [
                {
                    "home": fx["home"]["name"],
                    "away": fx["away"]["name"],
                    "home_goals": fx["home_goals"],
                    "away_goals": fx["away_goals"],
                    "winner": fx["winner_id"],
                }
                for fx in ehl["fixtures"]
            ],
        }
    )
    if ehl["round"] < 3:
        nxt = []
        for i in range(0, len(winners), 2):
            nxt.append(
                {
                    "home": winners[i],
                    "away": winners[i + 1],
                    "home_goals": 0,
                    "away_goals": 0,
                    "played": False,
                    "winner_id": "",
                }
            )
        ehl["fixtures"] = nxt
        ehl["round"] += 1
    else:
        ehl["winner_id"] = winners[0]["id"] if winners else ""
        ehl["winner_name"] = winners[0]["name"] if winners else ""
        ehl["active"] = False


def simulate_ehl(state: GameState) -> None:
    while state.ehl.get("active"):
        simulate_ehl_round(state)
