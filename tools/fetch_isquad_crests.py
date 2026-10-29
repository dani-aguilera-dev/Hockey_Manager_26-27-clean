"""Descarga los escudos oficiales de iSquad y los deja listos para la web.

Uso:
    python3 tools/fetch_isquad_crests.py

- Lee los clubes de manager/data/clubs.json.
- Localiza su equipo en iSquad usando tools/player_attributes_v2.csv.
- Descarga el escudo de la cabecera del equipo.
- Recorta el fondo blanco a transparente y guarda un PNG de 320 px.
- La web prioriza PNG sobre el SVG estilizado de respaldo.
"""

from __future__ import annotations

import csv
import io
import json
import re
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
CLUBS = ROOT / "manager" / "data" / "clubs.json"
PLAYERS = ROOT / "tools" / "player_attributes_v2.csv"
OUT = ROOT / "manager" / "web" / "static" / "crests"
UA = "Mozilla/5.0 (X11; Linux x86_64) HockeyManager/1.0"


def normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    text = text.encode("ascii", "ignore").decode().upper()
    return re.sub(r"[^A-Z0-9]+", " ", text).strip()


def team_urls() -> dict[str, str]:
    found: dict[str, str] = {}
    with PLAYERS.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            found.setdefault(normalize(row["equipo"]), row["team_url"])
    return found


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def crest_url(html: str, team_id: str) -> str:
    pattern = re.compile(
        rf"<a\s+href='equipo\.php\?[^']*id_equipo={re.escape(team_id)}(?:&|&amp;)[^']*'[^>]*>\s*"
        rf"<img[^>]*src='([^']+)'",
        re.IGNORECASE,
    )
    match = pattern.search(html)
    if match:
        return match.group(1).replace("&amp;", "&")
    raise ValueError(f"No se encontró escudo para id_equipo={team_id}")


def transparent_png(raw: bytes) -> Image.Image:
    image = Image.open(io.BytesIO(raw)).convert("RGBA")
    width, height = image.size
    for point in ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)):
        ImageDraw.floodfill(image, point, (255, 255, 255, 0), thresh=42)
    bbox = image.getbbox()
    if bbox:
        image = image.crop(bbox)
    image.thumbnail((320, 320), Image.LANCZOS)
    return image


def main() -> None:
    clubs = json.loads(CLUBS.read_text(encoding="utf-8"))
    urls = team_urls()
    OUT.mkdir(parents=True, exist_ok=True)
    ok = 0
    failed: list[str] = []
    for club in clubs:
        url = urls.get(normalize(club["name"]))
        if not url:
            failed.append(f"{club['id']}: sin URL")
            continue
        parsed = urllib.parse.urlparse(url)
        team_id = urllib.parse.parse_qs(parsed.query).get("id_equipo", [""])[0]
        try:
            html = fetch(url).decode("utf-8", "ignore")
            image_url = crest_url(html, team_id)
            if image_url.startswith("//"):
                image_url = "https:" + image_url
            elif image_url.startswith("http://"):
                image_url = "https://" + image_url[len("http://") :]
            raw = fetch(image_url)
            image = transparent_png(raw)
            image.save(OUT / f"{club['id']}.png", optimize=True)
            print(f"OK  {club['id']:<24} {image.size[0]}x{image.size[1]}")
            ok += 1
            time.sleep(0.25)
        except Exception as exc:
            failed.append(f"{club['id']}: {exc}")
            print(f"ERR {club['id']}: {exc}")
    print(f"\nEscudos oficiales: {ok}/{len(clubs)}")
    if failed:
        print("Fallos:")
        for item in failed:
            print(" -", item)


if __name__ == "__main__":
    main()
