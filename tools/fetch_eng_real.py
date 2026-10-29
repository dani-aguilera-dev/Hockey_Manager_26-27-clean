"""Importa plantillas masculinas reales de la England Hockey Premier Division.

Fuente: API oficial de England Hockey (GMS). Los nombres y equipos salen de
las estadísticas oficiales de la competición. Las posiciones de campo se
estiman cuando la fuente no publica una posición individual; los porteros
confirmados en las actas EHL se respetan.
"""

from __future__ import annotations

import json
import re
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image
import io

ROOT = Path(__file__).resolve().parents[1]
INTL = ROOT / "manager" / "data" / "international.json"
REAL = ROOT / "manager" / "data" / "international_real.json"
CRESTS = ROOT / "manager" / "web" / "static" / "crests"
API = "https://ehdwapi.englandhockey.co.uk/api"
KEY = "xfozTX349H17Bn8nHHk5"
COMPETITION = "c793707a-6ae9-462f-8046-0fc6a02dce08"
UA = "Mozilla/5.0 (X11; Linux x86_64) HockeyManager/1.0"

# Porteros confirmados en las actas de los EHL Finals 2026.
GOALKEEPERS = {
    "hampstead & westminster": {"VIJAY PAWAR", "LEKAN OGUNLANA"},
    "old georgians": {"JAMES MAZARELO", "JOSH GRIGG"},
    "surbiton": {"CALUM DOUGLAS", "DEWI ROBLIN", "MARK HAYCROFT"},
    "wimbledon": {"TOBY REYNOLDS-COTTERILL", "HARRY BOSTELMANN", "HARRY MCGUGAN"},
}


def norm(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", norm(value)).strip("-")


def api(path: str):
    request = urllib.request.Request(API + path, headers={"User-Agent": UA, "x-api-key": KEY})
    with urllib.request.urlopen(request, timeout=40) as response:
        return json.loads(response.read().decode("utf-8"))


def all_appearances():
    first = api(f"/competitions/{COMPETITION}/players/stats/appearances?page=1&pageSize=100")
    rows = list(first.get("data", []))
    total_pages = int(first.get("totalPages", 1))
    for page in range(2, total_pages + 1):
        payload = api(f"/competitions/{COMPETITION}/players/stats/appearances?pageNo={page}&pageSize=100")
        rows.extend(payload.get("data", []))
    return rows


def main() -> None:
    intl = json.loads(INTL.read_text(encoding="utf-8"))
    real = json.loads(REAL.read_text(encoding="utf-8")) if REAL.exists() else {}
    clubs = {norm(c["name"]): c for c in intl["clubs"] if c["league"] == "ENG"}
    teams = api(f"/competitions/{COMPETITION}/teams")
    rows = all_appearances()
    by_club: dict[str, dict] = {}
    for team in teams:
        key = norm(team.get("clubName", ""))
        club = clubs.get(key)
        if not club and key == "bowdon hc":
            club = next((candidate for candidate in clubs.values() if candidate["id"] == "eng-bowdon"), None)
        if not club:
            # Alias por si el nombre comercial varía.
            for candidate_key, candidate in clubs.items():
                if candidate_key in key or key in candidate_key:
                    club = candidate
                    break
        if not club:
            print("SIN MAPA", team.get("clubName"))
            continue
        by_club[club["id"]] = {"club": club, "team": team, "players": []}
    for row in rows:
        club = next((item["club"] for item in by_club.values() if norm(item["team"].get("teamName", "")) == norm(row.get("teamName", ""))), None)
        if not club:
            # La API puede cambiar el sufijo M1; se busca por nombre de club.
            club = next((item["club"] for item in by_club.values() if norm(item["team"].get("clubName", "")) == norm(row.get("clubName", ""))), None)
        if not club:
            continue
        by_club[club["id"]]["players"].append(row)

    payload = {}
    for club_id, item in by_club.items():
        players = item["players"]
        # Un miembro por id; conserva la fila con más apariciones.
        unique = {}
        for row in players:
            key = row.get("memberId") or row.get("displayName")
            if key not in unique or int(row.get("appearances", 0)) > int(unique[key].get("appearances", 0)):
                unique[key] = row
        ordered = sorted(unique.values(), key=lambda row: (-int(row.get("appearances", 0)), norm(row.get("displayName", ""))))
        gk_names = GOALKEEPERS.get(norm(item["team"].get("clubName", "")), set())
        output = []
        n = len(ordered)
        def_count = max(4, round(n * 0.28))
        mid_count = max(4, round(n * 0.28))
        for index, row in enumerate(ordered):
            name = str(row.get("displayName", "")).strip()
            if not name:
                continue
            if norm(name) in gk_names:
                position = "Portero"
            elif index < 2:
                position = "Portero"
            elif index < 2 + def_count:
                position = "Defensa"
            elif index < 2 + def_count + mid_count:
                position = "Medio"
            else:
                position = "Delantero"
            output.append(
                {
                    "id": f"{club_id}-{slug(name)}",
                    "name": name,
                    "position": position,
                    "dob": "",
                    "nationality": "",
                    "shirt": "",
                    "overall": round(79.0 + min(3.0, int(row.get("goals", 0)) * 0.15), 1),
                    "source": f"https://www.englandhockey.co.uk/teams/{item['team'].get('id', '')}",
                    "photo_remote": "",
                    "photo": "",
                    "appearances": int(row.get("appearances", 0)),
                    "goals": int(row.get("goals", 0)),
                }
            )
        if output:
            payload[club_id] = {"players": output}
            print(club_id, len(output), "jugadores")
    real["ENG"] = {"clubs": payload}
    REAL.write_text(json.dumps(real, ensure_ascii=False, indent=1), encoding="utf-8")

    # Escudos oficiales de la API.
    CRESTS.mkdir(parents=True, exist_ok=True)
    for club_id, item in by_club.items():
        url = item["team"].get("clubLogoUrl", "")
        if not url:
            continue
        try:
            raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=40).read()
            image = Image.open(io.BytesIO(raw)).convert("RGBA")
            image.thumbnail((320, 320), Image.LANCZOS)
            image.save(CRESTS / f"{club_id}.png", optimize=True)
            print("ESCUDO", club_id)
        except Exception as exc:
            print("ERROR escudo", club_id, exc)
    print("Equipos ENG:", len(payload))


if __name__ == "__main__":
    main()
