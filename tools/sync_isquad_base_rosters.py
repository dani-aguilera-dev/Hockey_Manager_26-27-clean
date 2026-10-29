"""Sincroniza las plantillas DHA/DHB con las fichas actuales de iSquad.

Sustituye las plantillas antiguas del manifiesto por las convocatorias
masculinas actuales. Así los filiales dejan de compartir jugadores con sus
primeros equipos y desaparecen las duplicidades históricas.
"""

from __future__ import annotations

import csv
import re
import time
import unicodedata
import urllib.request
from collections import OrderedDict
from pathlib import Path

from bs4 import BeautifulSoup
from fetch_lower_divisions import parse_roster, team_gender

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tools" / "todos_manifest_positions.csv"
UA = "Mozilla/5.0 (X11; Linux x86_64) HockeyManager/1.0"


def norm(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^A-Z0-9]+", " ", text.upper()).strip()


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", "ignore")


def main() -> None:
    rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8-sig")))
    fieldnames = list(rows[0].keys())
    teams: OrderedDict[str, dict] = OrderedDict()
    for row in rows:
        if row["liga"] in ("DHA", "DHB"):
            teams.setdefault(
                row["equipo"],
                {"liga": row["liga"], "club": row["club"], "url": row["team_url"]},
            )
    # DHA primero: si iSquad repitiese un jugador en un filial, se queda en el
    # primer equipo.
    ordered = sorted(teams.items(), key=lambda item: (item[1]["liga"] != "DHA", item[0]))
    old_by_team: dict[str, dict[str, dict]] = {}
    for row in rows:
        old_by_team.setdefault(row["equipo"], {})[norm(row["jugador"])] = row
    kept = [row for row in rows if row["liga"] not in ("DHA", "DHB")]
    used_names: set[str] = set()
    report = []
    for team, meta in ordered:
        html = fetch(meta["url"])
        gender = team_gender(html)
        if gender != "M":
            print(f"ERROR {team}: ficha no masculina ({gender})")
            continue
        players = parse_roster(html)
        # San Fernando mezcla invitados y staff en la misma tabla; para este
        # club solo las filas "Jugador" son plantilla oficial.
        if team == "ATICOS INMOBILIARIA CH SAN FERNANDO":
            players = [player for player in players if player.get("profile") == "Jugador"]
        new_rows = []
        for player in players:
            key = norm(player["name"])
            if not key or key in used_names:
                continue
            used_names.add(key)
            old = old_by_team.get(team, {}).get(key, {})
            row = {column: "" for column in fieldnames}
            row.update(
                {
                    "liga": meta["liga"],
                    "equipo": team,
                    "club": meta["club"],
                    "perfil": player["profile"],
                    "jugador": player["name"],
                    "edad": player["age"],
                    "goles": player["goals"],
                    "fecha_baja": "",
                    "imagen_url": player["photo_remote"],
                    "team_url": meta["url"],
                    "archivo_original": "",
                    "archivo_thumb": "",
                    "imagen_ok": str(bool(player["photo_remote"])),
                    "imagen_error": "",
                    "goles_num": player["goals"],
                    "pos": old.get("pos", ""),
                    "src": old.get("src", "Estimada"),
                    "conf": old.get("conf", "Baja"),
                    "pos_url": old.get("pos_url", ""),
                    "pos_fecha": old.get("pos_fecha", "2026-10-27"),
                    "pos_nota": old.get("pos_nota", "Ficha oficial iSquad; posición estimada."),
                }
            )
            new_rows.append(row)
        kept.extend(new_rows)
        report.append((meta["liga"], team, len(players), len(new_rows)))
        print(f"{meta['liga']} {team}: iSquad={len(players)} final={len(new_rows)}")
        time.sleep(0.15)
    with MANIFEST.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(kept)
    print("\nEquipos sincronizados:", len(report))
    print("Filas totales:", len(kept))


if __name__ == "__main__":
    main()
