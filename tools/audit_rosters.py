"""Genera una auditoría reproducible de equipos y plantillas 2026-27."""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAYERS = ROOT / "tools" / "player_attributes_v2.csv"
REGIONAL = ROOT / "manager" / "data" / "regional_teams.json"
OUT = ROOT / "manager" / "data" / "audit_rosters_2026_27.json"

LEAGUES = {
    "DHA": {
        "name": "Liga IATI Hockey - División de Honor A Masculina",
        "expected": 12,
        "sources": [
            "https://resultadoshockey.isquad.es/",
            "equipos_hockey_hierba_espana_masculino_2026_27.xlsx",
        ],
    },
    "DHB": {
        "name": "División de Honor B Masculina",
        "expected": 16,
        "sources": [
            "https://resultadoshockey.isquad.es/",
            "equipos_hockey_hierba_espana_masculino_2026_27.xlsx",
        ],
    },
    "1N": {
        "name": "Primera División Masculina - Liga Norte",
        "expected": 10,
        "sources": [
            "https://resultadoshockey.isquad.es/",
            "equipos_hockey_hierba_espana_masculino_2026_27.xlsx",
            "https://www.fmhockey.es/calendarios/1_masc_liga_2627.pdf",
        ],
    },
    "1A": {
        "name": "Campeonato de Andalucía - Primera División Masculina",
        "expected": 8,
        "sources": [
            "https://resultadoshockey.isquad.es/",
            "equipos_hockey_hierba_espana_masculino_2026_27.xlsx",
        ],
    },
    "1M": {
        "name": "Primera División Masculina Hierba - Liga Madrid",
        "expected": 9,
        "sources": [
            "https://resultadoshockey.isquad.es/",
            "equipos_hockey_hierba_espana_masculino_2026_27.xlsx",
            "https://www.fmhockey.es/calendarios/1_masc_liga_2627.pdf",
        ],
    },
    "1G": {
        "name": "Liga 1ª División Masculina (Galicia)",
        "expected": 6,
        "sources": [
            "https://resultadoshockey.isquad.es/",
            "equipos_hockey_hierba_espana_masculino_2026_27.xlsx",
        ],
    },
    "1C": {
        "name": "Campeonato de Canarias - 1ª División Masculina",
        "expected": 3,
        "sources": [
            "https://resultadoshockey.isquad.es/",
            "equipos_hockey_hierba_espana_masculino_2026_27.xlsx",
        ],
    },
    "1V": {
        "name": "1ª División Masculina Hockey Hierba (FHCV)",
        "expected": 7,
        "sources": [
            "https://fhcv.es/competiciones/1a-division-masculina-hockey-hierba-2026-2027/",
            "https://appweb.rfeh.es/descargar_acta_fhcv.php",
            "equipos_hockey_hierba_espana_masculino_2026_27.xlsx",
        ],
    },
    "SUP": {
        "name": "Superlliga Catalana Masculina",
        "expected": 8,
        "sources": [
            "https://www.fchockey.cat/temporada/10/competicio/1356/grup/2992/resultats",
            "https://www.fchockey.cat/partit/65609",
            "equipos_hockey_hierba_espana_masculino_2026_27.xlsx",
        ],
    },
    "CAT1": {
        "name": "Campionat de Catalunya 1ª Masculina (Primera Catalana)",
        "expected": 8,
        "sources": [
            "https://www.fchockey.cat/temporada/10/competicio/1359/grup/2994/resultats",
            "https://www.fchockey.cat/partit/66489",
            "equipos_hockey_hierba_espana_masculino_2026_27.xlsx",
        ],
    },
}


def norm(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^A-Z0-9]+", " ", text.upper()).strip()


def main() -> None:
    rows = list(csv.DictReader(PLAYERS.open(encoding="utf-8-sig")))
    by_team: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        code = str(row.get("liga") or "").strip()
        if code == "1ª Andaluza":
            code = "1A"
        if code not in LEAGUES:
            continue
        by_team[str(row.get("equipo") or "").strip()].append({**row, "_code": code})
    metadata_rows = json.loads(REGIONAL.read_text(encoding="utf-8"))
    metadata = {row["name"]: row for row in metadata_rows}
    metadata_by_base = {norm(row.get("base_name", "")): row for row in metadata_rows if row.get("base_name")}
    report = {"season": "2026-27", "generated": "2026-10-28", "leagues": {}, "duplicates": [], "warnings": []}
    for code, meta in LEAGUES.items():
        team_names = sorted({team for team, players in by_team.items() if players[0]["_code"] == code})
        team_rows = []
        for team in team_names:
            players = by_team[team]
            team_meta = metadata.get(team) or metadata_by_base.get(norm(team)) or {}
            display = team_meta.get("name", team)
            second = bool(team_meta.get("is_second_team"))
            team_rows.append(
                {
                    "team": display,
                    "players": len(players),
                    "second_team": second,
                    "parent_club": team_meta.get("parent_club", ""),
                    "source": team_meta.get("source", "iSquad/Excel"),
                }
            )
            if len(players) < 11:
                report["warnings"].append(f"{code}: {display} solo tiene {len(players)} jugadores")
        report["leagues"][code] = {
            "name": meta["name"],
            "expected_teams": meta["expected"],
            "actual_teams": len(team_names),
            "players": sum(len(by_team[team]) for team in team_names),
            "teams": team_rows,
            "sources": meta["sources"],
        }
    names = defaultdict(set)
    for team, players in by_team.items():
        for player in players:
            names[norm(player.get("jugador", ""))].add(team)
    report["duplicates"] = [
        {"player": name, "teams": sorted(teams)}
        for name, teams in sorted(names.items())
        if len(teams) > 1
    ]
    report["totals"] = {
        "teams": sum(item["actual_teams"] for item in report["leagues"].values()),
        "players": sum(item["players"] for item in report["leagues"].values()),
        "duplicates": len(report["duplicates"]),
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    for code, item in report["leagues"].items():
        print(f"{code:4} {item['actual_teams']:2}/{item['expected_teams']:2} equipos · {item['players']:3} jugadores")
    print("Duplicados:", len(report["duplicates"]))
    print("Avisos:", len(report["warnings"]))
    print("Guardado", OUT)


if __name__ == "__main__":
    main()
