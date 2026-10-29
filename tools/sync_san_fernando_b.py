"""Corrige las plantillas de San Fernando DHB y San Fernando B.

iSquad mezcla en la misma tabla jugadores, invitados y cuerpo técnico. Para
estos dos equipos se usan solo las filas con perfil `Jugador`; los invitados y
el staff no se convierten en futbolistas. El filial conserva su plantilla
propia y no se queda con los jugadores que el primer equipo lista como
invitados.
"""

from __future__ import annotations

import csv
import re
import time
import unicodedata
import urllib.request
from pathlib import Path

from fetch_lower_divisions import parse_roster, team_gender, team_page_url

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tools" / "todos_manifest_positions.csv"
TEAMS = {
    "ATICOS INMOBILIARIA CH SAN FERNANDO": {
        "id_equipo": 3891,
        "id_torneo": 9367,
        "liga": "DHB",
        "club": "Club Hockey San Fernando",
    },
    "CLUB DE HOCKEY SAN FERNANDO": {
        "id_equipo": 3939,
        "id_torneo": 9429,
        "liga": "1ª Andaluza",
        "club": "Club Hockey San Fernando",
    },
}


def norm(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^A-Z0-9]+", " ", text.upper()).strip()


def fetch(url: str) -> str:
    last = None
    for attempt in range(4):
        try:
            return urllib.request.urlopen(
                urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60
            ).read().decode("utf-8", "ignore")
        except Exception as exc:
            last = exc
            time.sleep(1 + attempt)
    raise last  # type: ignore[misc]


def main() -> None:
    rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8-sig")))
    fields = list(rows[0].keys())
    old_by_team: dict[str, dict[str, dict]] = {}
    for row in rows:
        old_by_team.setdefault(row["equipo"], {})[norm(row["jugador"])] = row
    kept = [row for row in rows if row["equipo"] not in TEAMS]
    for team, meta in TEAMS.items():
        url = team_page_url(meta)
        html = fetch(url)
        gender = team_gender(html)
        if gender != "M":
            raise RuntimeError(f"{team}: ficha no masculina ({gender})")
        players = [p for p in parse_roster(html) if p.get("profile") == "Jugador"]
        print(team, "jugadores oficiales:", len(players))
        for player in players:
            key = norm(player["name"])
            old = old_by_team.get(team, {}).get(key, {})
            row = {field: "" for field in fields}
            row.update(
                {
                    "liga": meta["liga"],
                    "equipo": team,
                    "club": meta["club"],
                    "perfil": "Jugador",
                    "jugador": player["name"],
                    "edad": player["age"],
                    "goles": player["goals"],
                    "goles_num": player["goals"],
                    "imagen_url": player["photo_remote"],
                    "team_url": url,
                    "imagen_ok": str(bool(player["photo_remote"])),
                    "pos": (
                        "Portero"
                        if team == "CLUB DE HOCKEY SAN FERNANDO" and key == norm("LAZARO NAVAS MONTALVO")
                        else ("" if team == "CLUB DE HOCKEY SAN FERNANDO" else old.get("pos", ""))
                    ),
                    "src": (
                        "Deporte de la Isla"
                        if team == "CLUB DE HOCKEY SAN FERNANDO" and key == norm("LAZARO NAVAS MONTALVO")
                        else ("Estimada" if team == "CLUB DE HOCKEY SAN FERNANDO" else old.get("src", "Estimada"))
                    ),
                    "conf": (
                        "Alta"
                        if team == "CLUB DE HOCKEY SAN FERNANDO" and key == norm("LAZARO NAVAS MONTALVO")
                        else ("Baja" if team == "CLUB DE HOCKEY SAN FERNANDO" else old.get("conf", "Baja"))
                    ),
                    "pos_url": (
                        "https://www.deportedelaisla.com/2026-10-13/hockey/el-ch-san-fernando-no-encuentra-camino-sufre-doble-derrota-madrid"
                        if team == "CLUB DE HOCKEY SAN FERNANDO" and key == norm("LAZARO NAVAS MONTALVO")
                        else ("" if team == "CLUB DE HOCKEY SAN FERNANDO" else old.get("pos_url", ""))
                    ),
                    "pos_fecha": "2026-10-28" if team == "CLUB DE HOCKEY SAN FERNANDO" else old.get("pos_fecha", "2026-10-27"),
                    "pos_nota": (
                        "Portero confirmado en la previa del primer equipo; el filial lo usa como guardameta."
                        if team == "CLUB DE HOCKEY SAN FERNANDO" and key == norm("LAZARO NAVAS MONTALVO")
                        else ("Ficha oficial iSquad; posición estimada." if team == "CLUB DE HOCKEY SAN FERNANDO" else old.get("pos_nota", ""))
                    ),
                }
            )
            kept.append(row)
    with MANIFEST.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(kept)
    print("Filas totales:", len(kept))


if __name__ == "__main__":
    main()
