"""Importa plantillas reales del Torneo Metropolitano masculino A.

Fuente: API oficial de la AAHBA (TournamentTracker) y planillas PDF de cada
partido. Los nombres son reales. La posición individual se estima cuando la
planilla no la publica; los porteros y el resto de roles quedan marcados como
estimados.
"""

from __future__ import annotations

import base64
import io
import json
import re
import subprocess
import tempfile
import unicodedata
import urllib.request
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
INTL = ROOT / "manager" / "data" / "international.json"
REAL = ROOT / "manager" / "data" / "international_real.json"
CRESTS = ROOT / "manager" / "web" / "static" / "crests"
CACHE = Path("/tmp/opencode/arg")
API = "https://api.tournamenttracker.buenosaireshockey.ar"
KEY = base64.b64decode("uweoEVNeycw7CFBXtHNCy3nbJZmUPl0EosXGRrNDgdU=")
UA = "Mozilla/5.0 (X11; Linux x86_64) HockeyManager/1.0"
TOURNAMENT = "00000401"

TEAM_MAP = {
    "SAN FERNANDO": "arg-san-fernando",
    "BANCO PROVINCIA": "arg-banco-provincia",
    "BCO. PROVINCIA": "arg-banco-provincia",
    "BCO PROVINCIA": "arg-banco-provincia",
    "CIUDAD A": "arg-ciudad",
    "CIUDAD": "arg-ciudad",
    "CIUDAD B": "arg-ciudad-b",
    "MITRE": "arg-mitre",
    "G. Y ESGRIMA": "arg-geba",
    "G Y ESGRIMA": "arg-geba",
    "GEBA": "arg-geba",
    "DUCILO": "arg-ducilo",
    "SANTA BARBARA": "arg-santa-barbara",
    "S. BARBARA": "arg-santa-barbara",
    "S BARBARA": "arg-santa-barbara",
    "S.A.G.": "arg-sag-lomas",
    "SAG": "arg-sag-lomas",
    "S A G": "arg-sag-lomas",
    "LOMAS": "arg-lomas-athletic",
    "U. LA PLATA": "arg-universitario-la-plata",
    "U LA PLATA": "arg-universitario-la-plata",
    "UNIVERSITARIO LA PLATA": "arg-universitario-la-plata",
    "SAN MARTIN": "arg-san-martin",
    "SAN MARTÍN": "arg-san-martin",
    "QUILMES": "arg-quilmes",
    "HURLING": "arg-hurling",
}


def norm(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^A-Z0-9]+", " ", text.upper()).strip()


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", norm(value).lower()).strip("-")


def get(path: str):
    raw = urllib.request.urlopen(
        urllib.request.Request(API + path, headers={"User-Agent": UA}), timeout=40
    ).read().decode("utf-8")
    iv_hex, cipher_hex = json.loads(raw).split(":", 1)
    decryptor = Cipher(algorithms.AES(KEY), modes.CTR(bytes.fromhex(iv_hex))).decryptor()
    plain = decryptor.update(bytes.fromhex(cipher_hex)) + decryptor.finalize()
    return json.loads(plain)


def download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60).read()
    path.write_bytes(data)


def parse_planilla(path: Path) -> tuple[list[str], list[str]]:
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as handle:
        text_path = Path(handle.name)
    try:
        subprocess.run(["pdftotext", "-layout", str(path), str(text_path)], check=True, timeout=30)
        lines = text_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    finally:
        text_path.unlink(missing_ok=True)
    left_names, right_names = [], []
    for line in lines:
        if len(line) < 80:
            continue
        left, right = line[:115], line[115:]
        match = re.match(r"^\s*(\d+)\s+(.+?)\s{2,}\d{5,}", left)
        if match:
            name = re.sub(r"\s+\((?:C|P|A|T|GK)\)\s*$", "", match.group(2)).strip()
            if name and len(name) > 3:
                left_names.append(name)
        match = re.search(r"\s(\d+)\s+(.+?)\s{2,}\d{5,}", right)
        if match:
            name = re.sub(r"\s+\((?:C|P|A|T|GK)\)\s*$", "", match.group(2)).strip()
            if name and len(name) > 3:
                right_names.append(name)
    return left_names, right_names


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    intl = json.loads(INTL.read_text(encoding="utf-8"))
    real = json.loads(REAL.read_text(encoding="utf-8")) if REAL.exists() else {}
    clubs = {c["id"]: c for c in intl["clubs"] if c["league"] == "ARG"}
    club_by_name = {norm(c["name"]): c["id"] for c in clubs.values()}
    # Alias por nombre corto.
    for alias, cid in TEAM_MAP.items():
        club_by_name.setdefault(alias, cid)
    torneo = get(f"/torneos/{TOURNAMENT}")
    matches = []
    for phase in torneo.get("fases", []):
        for zone in phase.get("zonas", []):
            matches.extend(zone.get("partidos", []))
    print("Partidos:", len(matches))
    rosters: dict[str, set[str]] = {}
    sources: dict[str, str] = {}
    for match in matches:
        planillas = match.get("planillas") or []
        if not planillas:
            continue
        local_id = club_by_name.get(norm(match.get("nombreLocal", "")))
        away_id = club_by_name.get(norm(match.get("nombreVisitante", "")))
        if not local_id or not away_id:
            continue
        pdf_url = planillas[0].get("pdf", "")
        if not pdf_url:
            continue
        pdf = CACHE / f"{match.get('id', 'match')}.pdf"
        try:
            download(pdf_url, pdf)
            left, right = parse_planilla(pdf)
        except Exception as exc:
            print("ERROR planilla", match.get("id"), exc)
            continue
        if left:
            rosters.setdefault(local_id, set()).update(left)
            sources[local_id] = pdf_url
        if right:
            rosters.setdefault(away_id, set()).update(right)
            sources[away_id] = pdf_url
    payload = {}
    used = set()
    for club_id, names in sorted(rosters.items()):
        ordered = sorted(names)
        players = []
        n = len(ordered)
        def_count = max(4, round(n * 0.28))
        mid_count = max(4, round(n * 0.28))
        for index, name in enumerate(ordered):
            key = norm(name)
            if key in used:
                continue
            used.add(key)
            if index < 2:
                position = "Portero"
            elif index < 2 + def_count:
                position = "Defensa"
            elif index < 2 + def_count + mid_count:
                position = "Medio"
            else:
                position = "Delantero"
            players.append(
                {
                    "id": f"{club_id}-{slug(name)}",
                    "name": name,
                    "position": position,
                    "dob": "",
                    "nationality": "Argentina",
                    "shirt": "",
                    "overall": 77.0,
                    "source": sources.get(club_id, ""),
                    "photo_remote": "",
                    "photo": "",
                    "position_source": "Planilla oficial AAHBA; posición estimada",
                }
            )
        if players:
            payload[club_id] = {"players": players}
            print(club_id, len(players), "jugadores")
    real["ARG"] = {"clubs": payload}
    REAL.write_text(json.dumps(real, ensure_ascii=False, indent=1), encoding="utf-8")

    # Escudos desde el catálogo oficial de clubes.
    try:
        club_rows = get("/clubes")
        crest_by_name = {norm(row.get("club", "")): row.get("clubEscudo", "") for row in club_rows}
        for club_id, club in clubs.items():
            url = crest_by_name.get(norm(club["name"]), "")
            if not url:
                # El catálogo usa nombres cortos; prueba por alias.
                url = next((crest_by_name[norm(alias)] for alias, cid in TEAM_MAP.items() if cid == club_id and crest_by_name.get(norm(alias))), "")
            if not url and club_id == "arg-ciudad-b":
                url = crest_by_name.get("CIUDAD", "")
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
    except Exception as exc:
        print("ERROR catálogo escudos", exc)
    print("Equipos ARG:", len(payload))


if __name__ == "__main__":
    main()
