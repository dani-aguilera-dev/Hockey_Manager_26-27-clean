"""Descarga convocatorias masculinas de la FHCV desde las actas oficiales.

La FHCV publica las actas en PDF con los dos equipos y sus jugadores. Se usan
la temporada actual y la anterior para completar las plantillas de la 1ª
División Valenciana. No se inventan jugadores.
"""

from __future__ import annotations

import csv
import json
import re
import subprocess
import tempfile
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
PAGES = [
    "https://fhcv.es/competiciones/1a-division-masculina-hockey-hierba-2026-2027/",
    "https://fhcv.es/competiciones/1a-division-masculina-hockey-hierba-2025-2026/",
]
TEAM_MAP = {
    "CH CARPESA": "CH CARPESA B",
    "CH XALOC": "CH XALOC",
    "VALENCIA CH": "VALENCIA CH",
    "VALENCIA CH 1924": "VALENCIA CH 1924",
    "HONIGVOGEL HH 79": "HONIGVÖGEL HH'79",
    "HOCKEY SALDUIE 78": "HOCKEY SALDUIE '78",
    "CH SANTOMERA": "SANTOMERA HC",
    "SANTOMERA HC": "SANTOMERA HC",
}


def norm(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^A-Z0-9]+", " ", text.upper()).strip()


def fetch(url: str) -> bytes:
    last = None
    for attempt in range(4):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(request, timeout=40) as response:
                return response.read()
        except Exception as exc:
            last = exc
            time.sleep(0.6 + attempt * 0.8)
    raise last  # type: ignore[misc]


def acta_links(html: str) -> list[str]:
    return sorted(
        {
            match.group(0)
            for match in re.finditer(r"https://appweb\.rfeh\.es/descargar_acta_fhcv\.php\?[^\"']+", html)
        }
    )


def parse_acta(pdf: Path) -> tuple[str, list[str], str, list[str]]:
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as handle:
        text_path = Path(handle.name)
    try:
        subprocess.run(["pdftotext", "-layout", str(pdf), str(text_path)], check=True, timeout=30)
        lines = text_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    finally:
        text_path.unlink(missing_ok=True)
    left_team = right_team = ""
    for line in lines:
        if "SHOOT OUT" in line and ":" in line:
            before, after = line.split("SHOOT OUT", 1)
            left_team = before.strip()
            right_team = after.split(":", 1)[1].strip()
            break
    left_players: list[str] = []
    right_players: list[str] = []
    in_players = False
    for line in lines:
        if "JUGADOR/A" in line:
            in_players = True
            continue
        if not in_players:
            continue
        if line.startswith("DELEGAT/DA") or "ENTRENADOR/A" in line:
            break
        left = line[:100]
        right = line[100:]
        m = re.match(r"^\s*(\d{6})\s+(\d+)\s+(.+?)(?:\s{2,}|$)", left)
        if m:
            name = re.sub(r"\s+\((?:C|P|Juvenil|SL)\)\s*$", "", m.group(3)).strip()
            if name:
                left_players.append(name)
        m = re.search(r"\s(\d{6})\s+(\d+)\s+(.+?)(?:\s{2,}|$)", right)
        if m:
            name = re.sub(r"\s+\((?:C|P|Juvenil|SL)\)\s*$", "", m.group(3)).strip()
            if name:
                right_players.append(name)
    return left_team, left_players, right_team, right_players


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
    cache = Path("/tmp/opencode/fhcv")
    cache.mkdir(parents=True, exist_ok=True)
    rosters: dict[str, set[str]] = {}
    seen_actas: set[str] = set()
    for page_url in PAGES:
        html = fetch(page_url).decode("utf-8", "ignore")
        links = acta_links(html)
        print(f"{page_url}: {len(links)} actas")
        for url in links:
            if url in seen_actas:
                continue
            seen_actas.add(url)
            name = re.sub(r"[^0-9]", "", url)[-12:] + ".pdf"
            pdf = cache / name
            if not pdf.exists():
                pdf.write_bytes(fetch(url))
            try:
                left, left_players, right, right_players = parse_acta(pdf)
            except Exception as exc:
                print("  ERROR acta", url, exc)
                continue
            for source_team, players in ((left, left_players), (right, right_players)):
                internal = TEAM_MAP.get(norm(source_team))
                if not internal:
                    print("  equipo sin mapa:", repr(source_team))
                    continue
                rosters.setdefault(internal, set()).update(players)
            time.sleep(0.1)
    added: list[dict] = []
    for team_name, names in sorted(rosters.items()):
        meta = by_name.get(norm(team_name))
        if not meta:
            print("  sin metadata:", team_name)
            continue
        meta["source"] = "FHCV"
        meta["source_url"] = PAGES[0]
        for name in sorted(names):
            key = norm(name)
            if not key or key in used_names:
                continue
            used_names.add(key)
            row = {column: "" for column in fieldnames}
            row.update(
                {
                    "liga": meta["league_text"],
                    "liga_code": "1V",
                    "equipo": meta["name"],
                    "club": meta.get("club", ""),
                    "perfil": "",
                    "jugador": name,
                    "edad": "22",
                    "goles": "0",
                    "goles_num": "0",
                    "imagen_url": "",
                    "team_url": PAGES[0],
                    "imagen_ok": "False",
                    "pos": "",
                    "src": "Estimada",
                    "conf": "Baja",
                    "pos_fecha": "2026-10-27",
                    "pos_nota": "Convocatoria oficial FHCV; posición estimada.",
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
