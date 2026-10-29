"""Descarga el escudo real de los 59 equipos regionales.

Fuentes, en este orden:
1. iSquad (ficha del equipo).
2. FHCV (escudos de la competición valenciana).
3. FCH (logos de club de las actas catalanas).
4. Escudo del club matriz ya descargado, si no hay URL directa.
"""

from __future__ import annotations

import csv
import io
import json
import re
import shutil
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
REGIONAL = ROOT / "manager" / "data" / "regional_teams.json"
LOWER = ROOT / "tools" / "lower_divisions_players.csv"
OUT = ROOT / "manager" / "web" / "static" / "crests"
UA = "Mozilla/5.0 (X11; Linux x86_64) HockeyManager/1.0"
FHCV = "https://fhcv.es/competiciones/1a-division-masculina-hockey-hierba-2026-2027/"
FCH_PAGES = {
    "SUP": "https://www.fchockey.cat/temporada/10/competicio/1356/grup/2992/resultats",
    "CAT1": "https://www.fchockey.cat/temporada/10/competicio/1359/grup/2994/resultats",
}
FCH_MAP = {
    "EHC": "EHC",
    "EGARA 1935": "EGARA 1935 B",
    "ATLETIC TERRASSA HOCKEY CLUB": "ATLÈTIC TERRASSA B",
    "FC BARCELONA": "FC BARCELONA B",
    "CLUB ESPORTIU PEDRALBES 1991": "CE PEDRALBES 1991",
    "VALLÈS ESPORTIU": "VALLÈS ESPORTIU B",
    "CD TERRASSA HOCKEY": "CD TERRASSA B",
    "DIAGONAL HC": "DIAGONAL HC",
    "ATLETIC 1952": "ATLETIC 1952",
    "MATADEPERA 88 HOQUEI": "MATADEPERA 88 HOQUEI",
    "HC SANT CUGAT": "HC SANT CUGAT B",
    "CAN SALAS": "CAN SALAS",
    "CHC": "CHC",
    "RC POLO": "RC POLO B",
    "BARCELONA HOCKEY CLUB": "BARCELONA HOCKEY CLUB",
    "CLUB EGARA": "CLUB EGARA B",
}
FHCV_MAP = {
    "CH XALOC": "CH XALOC",
    "VALENCIA CH": "VALENCIA CH",
    "HONIGVÖGEL HH'79": "HONIGVÖGEL HH'79",
    "HOCKEY SALDUIE ' 78": "HOCKEY SALDUIE '78",
    "SANTOMERA HC": "SANTOMERA HC",
    "CH CARPESA": "CH CARPESA B",
    "VALENCIA CH 1924": "VALENCIA CH 1924",
}


def norm(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^A-Z0-9]+", " ", text.upper()).strip()


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=40) as response:
        return response.read()


def png(raw: bytes) -> Image.Image:
    image = Image.open(io.BytesIO(raw)).convert("RGBA")
    width, height = image.size
    for point in ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)):
        ImageDraw.floodfill(image, point, (255, 255, 255, 0), thresh=42)
    bbox = image.getbbox()
    if bbox:
        image = image.crop(bbox)
    image.thumbnail((320, 320), Image.LANCZOS)
    return image


def isquad_crest(url: str) -> str:
    html = fetch(url).decode("utf-8", "ignore")
    parsed = urllib.parse.urlparse(url)
    team_id = urllib.parse.parse_qs(parsed.query).get("id_equipo", [""])[0]
    pattern = re.compile(
        rf"<a\s+href='equipo\.php\?[^']*id_equipo={re.escape(team_id)}(?:&|&amp;)[^']*'[^>]*>\s*"
        rf"<img[^>]*src='([^']+)'",
        re.IGNORECASE,
    )
    match = pattern.search(html)
    if not match:
        raise ValueError("escudo iSquad no encontrado")
    image_url = match.group(1).replace("&amp;", "&")
    if image_url.startswith("//"):
        image_url = "https:" + image_url
    return image_url.replace("http://", "https://", 1)


def fhcv_crests() -> dict[str, str]:
    html = fetch(FHCV).decode("utf-8", "ignore")
    soup = BeautifulSoup(html, "lxml")
    found = {}
    for cell in soup.select("td.equipos_competi, td.equipos_competi_last"):
        image = cell.select_one("img")
        if not image or not image.get("src"):
            continue
        source = image["src"]
        if source.startswith("//"):
            source = "https:" + source
        target = FHCV_MAP.get(norm(cell.get("title", "")))
        if target:
            found[target] = source
    return found


def fch_crests() -> dict[str, str]:
    found: dict[str, str] = {}
    for page in FCH_PAGES.values():
        html = fetch(page).decode("utf-8", "ignore")
        links = sorted({a["href"] for a in BeautifulSoup(html, "lxml").find_all("a", href=True) if re.fullmatch(r"/partit/\d+", a["href"])})
        for link in links:
            if len(found) >= 16:
                break
            try:
                match = BeautifulSoup(fetch("https://www.fchockey.cat" + link).decode("utf-8", "ignore"), "lxml")
                for div in match.find_all("div", attrs={"flex": True}):
                    image = div.find("img")
                    text = div.get_text(" ", strip=True)
                    if not image or "CLUB_LOGO" not in image.get("src", ""):
                        continue
                    target = FCH_MAP.get(norm(text))
                    if target:
                        found.setdefault(target, image["src"])
            except Exception:
                continue
    return found


def main() -> None:
    teams = json.loads(REGIONAL.read_text(encoding="utf-8"))
    by_name = {norm(team["name"]): team for team in teams}
    urls = {}
    with LOWER.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            urls.setdefault(norm(row.get("equipo", "")), row.get("team_url", ""))
    extra = {**fhcv_crests(), **fch_crests()}
    extra.setdefault("HONIGVÖGEL HH'79", "https://fhcv.es/fhcvbackend/escudos/50/honigvogel.png")
    extra.setdefault("HOCKEY SALDUIE '78", "https://hockey.isquad.es/images/afiliacion_clubs/49/square_65653879753368763837.jpg")
    extra.setdefault("VALLÈS ESPORTIU B", "https://storage.googleapis.com/fchockey/static/img/fch/ATHC-01-128x128.png")
    print("Escudos FHCV/FCH:", len(extra))
    OUT.mkdir(parents=True, exist_ok=True)
    ok = 0
    failed = []
    for team in teams:
        team_id = team["id"]
        name = team["name"]
        url = team.get("crest_url") or extra.get(name) or urls.get(norm(name)) or team.get("team_url")
        try:
            if (OUT / f"{team_id}.png").exists() and not url:
                ok += 1
                continue
            if url and "equipo.php" in url:
                image_url = isquad_crest(url)
                raw = fetch(image_url)
                png(raw).save(OUT / f"{team_id}.png", optimize=True)
            elif url:
                raw = fetch(url)
                png(raw).save(OUT / f"{team_id}.png", optimize=True)
            else:
                raise ValueError("sin URL")
            team["crest_url"] = url
            ok += 1
            print("OK ", team_id)
        except Exception as exc:
            if (OUT / f"{team_id}.png").exists():
                ok += 1
                print("KEEP", team_id)
                continue
            # Fallback: reutiliza el escudo del club matriz ya descargado.
            parent = norm(team.get("parent_club", ""))
            candidates = [t for t in teams if norm(t.get("club", "")) == parent and (OUT / f"{t['id']}.png").exists()]
            if candidates:
                shutil.copyfile(OUT / f"{candidates[0]['id']}.png", OUT / f"{team_id}.png")
                ok += 1
                print("COPY", team_id, "<-", candidates[0]["id"])
            else:
                failed.append(f"{team_id}: {exc}")
                print("ERR", team_id, exc)
    REGIONAL.write_text(json.dumps(teams, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nEscudos: {ok}/{len(teams)}")
    for item in failed:
        print(" -", item)


if __name__ == "__main__":
    main()
