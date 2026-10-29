"""Descarga plantillas de divisiones autonómicas desde iSquad.

Genera tools/lower_divisions_players.csv con las plantillas de los equipos del
Excel inicial que no son DHA/DHB. No crea equipos jugables: esos jugadores se
usan como agentes libres.
"""

from __future__ import annotations

import csv
import json
import re
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

import openpyxl
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / "equipos_hockey_hierba_espana_masculino_2026_27.xlsx"
OUT = ROOT / "tools" / "lower_divisions_players.csv"
TOKEN = "2b74e0252be9011a15e5ae1197ca7d0d"
SEARCH = "https://hockey.isquad.es/json/api/call.php/resultados/busquedaGlobal?token=" + TOKEN
UA = "Mozilla/5.0 (X11; Linux x86_64) HockeyManager/1.0"

LEAGUE_CODES = {
    "Primera División Masculina - Liga Norte": "1N",
    "Campeonato de Andalucía - Primera División Masculina": "1A",
    "Primera División Masculina Hierba - Liga Madrid": "1M",
    "Liga 1ª División Masculina (Galicia)": "1G",
    "Campeonato de Canarias - 1ª División Masculina": "1C",
    "1ª División Masculina Hockey Hierba (FHCV)": "1V",
    "Superlliga Catalana Masculina": "SUP",
    "Campionat de Catalunya 1ª Masculina (Primera Catalana)": "CAT1",
}


def norm(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^A-Z0-9]+", " ", text.upper()).strip()


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", "ignore")


def search_teams(query: str) -> list[dict]:
    data = urllib.parse.urlencode(
        {"q": query, "id_temporada": "2627", "id_superficie": "1", "seleccion": "0", "limit": "30"}
    ).encode()
    request = urllib.request.Request(SEARCH, data=data, method="POST", headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload.get("data", {}).get("equipos", [])


def team_page_url(entry: dict) -> str:
    return (
        "https://resultadoshockey.isquad.es/equipo.php?seleccion=0&id_superficie=1"
        f"&id_equipo={entry['id_equipo']}&id={entry['id_torneo']}"
    )


def team_gender(html: str) -> str:
    """Devuelve M/F/? leyendo la categoría y competición seleccionadas.

    iSquad usa el mismo nombre de categoría para fichas masculinas y
    femeninas; la única fuente fiable es la ficha del equipo.
    """
    soup = BeautifulSoup(html, "lxml")
    category = soup.select_one("select#categorias option[selected]")
    competition = soup.select_one("select#competiciones option[selected]")
    text = " ".join(
        item.get_text(" ", strip=True) for item in (category, competition) if item is not None
    ).upper()
    if "FEM" in text or "FEMEN" in text:
        return "F"
    if "MASC" in text or " M " in f" {text} ":
        return "M"
    return "?"


def parse_roster(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    players = []
    for row in soup.select("table.tabla-plantilla tr"):
        cells = row.select("td")
        if len(cells) != 5:
            continue
        name = cells[0].get_text(" ", strip=True)
        profile = cells[1].get_text(" ", strip=True)
        age = cells[2].get_text(" ", strip=True)
        goals = cells[3].get_text(" ", strip=True)
        image = row.select_one("img")
        if not name:
            continue
        try:
            age_n = int(age)
        except ValueError:
            age_n = 22
        try:
            goals_n = int(goals)
        except ValueError:
            goals_n = 0
        players.append(
            {
                "name": name,
                "profile": profile,
                "age": age_n,
                "goals": goals_n,
                "photo_remote": "https:" + image["src"] if image and image.get("src", "").startswith("//") else (image.get("src", "") if image else ""),
            }
        )
    return players


def compact(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "", norm(value))


GENERIC_TOKENS = {
    "CLUB", "HOCKEY", "CH", "HC", "CD", "CE", "CP", "AD", "REAL", "DE", "DEL", "LA", "EL",
    "SENIOR", "MASCULINO", "FEMENINO", "HIERBA", "HOCKEY", "CLUB", "SOCIEDAD", "DEPORTIVO",
}


def team_matches(entry: dict, team_name: str, club: str) -> bool:
    category = str(entry.get("categoria", "")).upper()
    if "PRIMERA DIVISION" not in category and "SUPERLIGA" not in category and "PRIMERA CATALANA" not in category:
        return False
    haystack = compact(entry.get("nombre", "") + " " + entry.get("nombre_club", ""))
    for needle in (compact(team_name), compact(club)):
        if needle and (needle in haystack or haystack in needle):
            return True
    hay_tokens = set(norm(entry.get("nombre", "") + " " + entry.get("nombre_club", "")).split())
    hay_distinctive = hay_tokens - GENERIC_TOKENS
    for candidate in (team_name, club):
        tokens = set(norm(candidate).split())
        distinctive = tokens - GENERIC_TOKENS
        if distinctive & hay_distinctive and len(tokens & hay_tokens) >= 2:
            return True
    return False


def main() -> None:
    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    ws = wb["Equipos únicos"]
    rows = list(ws.iter_rows(values_only=True))
    headers = list(rows[0])
    output = []
    for raw in rows[1:]:
        row = dict(zip(headers, raw))
        category = str(row.get("Categoría", ""))
        if category in ("DHA", "DHB"):
            continue
        league_text = str(row.get("Liga / Competición", ""))
        code = LEAGUE_CODES.get(league_text, "1A")
        team_name = str(row.get("Nombre en competición", "")).strip()
        club = str(row.get("Club", "")).strip()
        # Evita duplicar el San Fernando 1ª que ya está en el CSV principal.
        if "SAN FERNANDO" in norm(team_name) and code == "1A":
            print("SKIP duplicado", team_name)
            continue
        print("\nBUSCAR", team_name, "|", league_text)
        queries = []
        for query in (team_name, club, " ".join(team_name.split()[:2]), " ".join(team_name.split()[-2:])):
            if query and query not in queries:
                queries.append(query)
        candidates = []
        for query in queries:
            try:
                found = search_teams(query)
            except Exception as exc:
                print("  ERROR búsqueda", query, exc)
                continue
            for item in found:
                if item.get("id_equipo") not in {row.get("id_equipo") for row in candidates}:
                    candidates.append(item)
            if any(team_matches(item, team_name, club) for item in candidates):
                break
        matches = [item for item in candidates if team_matches(item, team_name, club)]
        if not matches:
            print("  SIN EQUIPO", [(item.get("nombre"), item.get("categoria")) for item in candidates[:3]])
            continue
        best = None
        best_players = []
        for item in matches[:8]:
            try:
                html = fetch(team_page_url(item))
                gender = team_gender(html)
                players = parse_roster(html)
            except Exception as exc:
                print("  ERROR ficha", item.get("nombre"), exc)
                continue
            print(
                "  candidato",
                item.get("nombre"),
                item.get("categoria"),
                f"género={gender}",
                "jugadores",
                len(players),
            )
            if gender != "M":
                print("    descartado: no es una ficha masculina")
                continue
            if len(players) > len(best_players):
                best, best_players = item, players
            time.sleep(0.15)
        if not best or not best_players:
            print("  SIN PLANTILLA")
            continue
        print("  ELEGIDO", best.get("nombre"), "->", len(best_players), "jugadores")
        for player in best_players:
            output.append(
                {
                    "liga": league_text,
                    "liga_code": code,
                    "equipo": team_name,
                    "club": club,
                    "perfil": player["profile"],
                    "jugador": player["name"],
                    "edad": player["age"],
                    "goles": player["goals"],
                    "goles_num": player["goals"],
                    "fecha_baja": "",
                    "imagen_url": player["photo_remote"],
                    "team_url": team_page_url(best),
                    "archivo_original": "",
                    "archivo_thumb": "",
                    "imagen_ok": bool(player["photo_remote"]),
                    "imagen_error": "",
                    "pos": "",
                    "src": "Estimada",
                    "conf": "Baja",
                    "pos_url": "",
                    "pos_fecha": "2026-10-27",
                    "pos_nota": "Posición estimada por distribución media de plantilla; iSquad no publica posición individual.",
                    "source_team_id": best.get("id_equipo"),
                }
            )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output[0]) if output else ["liga"])
        writer.writeheader()
        writer.writerows(output)
    print("\nGuardado", OUT, "con", len(output), "jugadores")


if __name__ == "__main__":
    main()
