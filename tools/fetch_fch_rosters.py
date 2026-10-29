"""Descarga plantillas masculinas de la Federació Catalana de Hockey.

Las actas de partido de fchockey.cat publican la convocatoria completa de cada
equipo. Se usan para las ligas Superlliga Catalana y Primera Catalana, que no
están en iSquad. No se inventan jugadores ni se mezclan equipos B con primeros
equipos.
"""

from __future__ import annotations

import csv
import json
import re
import time
import unicodedata
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
LOWER = ROOT / "tools" / "lower_divisions_players.csv"
PLAYERS = ROOT / "tools" / "player_attributes_v2.csv"
REGIONAL = ROOT / "manager" / "data" / "regional_teams.json"
UA = "Mozilla/5.0 (X11; Linux x86_64) HockeyManager/1.0"
BASE = "https://www.fchockey.cat"
PAGES = {
    "SUP": "/temporada/10/competicio/1356/grup/2992/resultats",
    "CAT1": "/temporada/10/competicio/1359/grup/2994/resultats",
}
# Nombres que usa el acta -> nombre interno del equipo.
TEAM_MAP = {
    "SUP": {
        "EHC": "EHC",
        "EGARA 1935": "EGARA 1935 B",
        "ATLETIC TERRASSA HOCKEY CLUB": "ATLÈTIC TERRASSA B",
        "FC BARCELONA": "FC BARCELONA B",
        "CLUB ESPORTIU PEDRALBES 1991": "CE PEDRALBES 1991",
        "VALLÈS ESPORTIU": "VALLÈS ESPORTIU B",
        "CD TERRASSA HOCKEY": "CD TERRASSA B",
        "DIAGONAL HC": "DIAGONAL HC",
    },
    "CAT1": {
        "ATLETIC 1952": "ATLETIC 1952",
        "MATADEPERA 88 HOQUEI": "MATADEPERA 88 HOQUEI",
        "HC SANT CUGAT": "HC SANT CUGAT B",
        "CAN SALAS": "CAN SALAS",
        "CHC": "CHC",
        "RC POLO": "RC POLO B",
        "BARCELONA HOCKEY CLUB": "BARCELONA HOCKEY CLUB",
        "CLUB EGARA": "CLUB EGARA B",
    },
}


def norm(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^A-Z0-9]+", " ", text.upper()).strip()


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", "ignore")


def match_links(page: str) -> list[str]:
    soup = BeautifulSoup(page, "lxml")
    links = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if re.fullmatch(r"/partit/\d+", href) and href not in links:
            links.append(href)
    return links


def parse_match(page: str) -> list[tuple[str, list[str]]]:
    soup = BeautifulSoup(page, "lxml")
    result = []
    for wrapper in soup.select(".acta_team_wrapper"):
        title = wrapper.select_one(".content_box_title")
        if not title:
            continue
        team = title.get_text(" ", strip=True)
        section = None
        for candidate in wrapper.select(".acta_section"):
            heading = candidate.select_one("h2")
            if heading and heading.get_text(" ", strip=True).lower() == "jugadors":
                section = candidate
                break
        if section is None:
            continue
        names = []
        for row in section.select("tbody tr"):
            cells = row.select("td")
            if len(cells) < 2:
                continue
            name = cells[1].get_text(" ", strip=True)
            if name:
                names.append(name)
        result.append((team, names))
    return result


def main() -> None:
    rows = list(csv.DictReader(LOWER.open(encoding="utf-8-sig")))
    fieldnames = list(rows[0].keys())
    used_names = set()
    with PLAYERS.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            name = norm(row.get("jugador", ""))
            if name:
                used_names.add(name)
    metadata = json.loads(REGIONAL.read_text(encoding="utf-8"))
    by_name = {norm(item["name"]): item for item in metadata}
    added: list[dict] = []
    maps = {
        code: {norm(source): target for source, target in mapping.items()}
        for code, mapping in TEAM_MAP.items()
    }
    for code, page_path in PAGES.items():
        page = fetch(BASE + page_path)
        links = match_links(page)
        print(f"{code}: {len(links)} partidos")
        team_rosters: dict[str, set[str]] = {}
        for index, link in enumerate(links, 1):
            try:
                match_page = fetch(BASE + link)
                for source_team, names in parse_match(match_page):
                    internal = maps[code].get(norm(source_team))
                    if not internal:
                        print(f"  equipo sin mapa: {source_team!r}")
                        continue
                    team_rosters.setdefault(internal, set()).update(names)
            except Exception as exc:
                print(f"  ERROR {link}: {exc}")
            if index % 10 == 0:
                time.sleep(0.1)
        print(f"  equipos con acta: {len(team_rosters)}")
        for team_name, names in sorted(team_rosters.items()):
            meta = by_name.get(norm(team_name))
            if not meta:
                print(f"  sin metadata: {team_name}")
                continue
            meta["source"] = "FCH"
            meta["source_url"] = BASE + page_path
            for name in sorted(names):
                key = norm(name)
                if not key or key in used_names:
                    continue
                used_names.add(key)
                row = {column: "" for column in fieldnames}
                row.update(
                    {
                        "liga": meta["league_text"],
                        "liga_code": code,
                        "equipo": meta["name"],
                        "club": meta.get("club", ""),
                        "perfil": "",
                        "jugador": name,
                        "edad": "",
                        "goles": "",
                        "goles_num": "",
                        "imagen_url": "",
                        "team_url": BASE + page_path,
                        "imagen_ok": "False",
                        "pos": "",
                        "src": "Estimada",
                        "conf": "Baja",
                        "pos_fecha": "2026-10-27",
                        "pos_nota": "Convocatoria oficial FCH; posición estimada.",
                        "source_team_id": team_name,
                    }
                )
                added.append(row)
            print(f"  {team_name}: {len(names)} en actas")
    REGIONAL.write_text(json.dumps(metadata, ensure_ascii=False, indent=1), encoding="utf-8")
    with LOWER.open("a", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writerows(added)
    print(f"\nJugadores añadidos: {len(added)}")


if __name__ == "__main__":
    main()
