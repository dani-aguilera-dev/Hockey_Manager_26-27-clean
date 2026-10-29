"""Descarga el cuerpo técnico visible en las fichas de equipo de iSquad.

Uso:
    python3 tools/fetch_isquad_staff.py

Genera manager/data/staff_isquad.json. El primer rol "Entrenador" se
interpreta como primer entrenador; los siguientes como entrenadores adjuntos.
"""

from __future__ import annotations

import csv
import hashlib
import html as htmlmod
import json
import re
import time
import unicodedata
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAYERS = ROOT / "tools" / "player_attributes_v2.csv"
OUT = ROOT / "manager" / "data" / "staff_isquad.json"
UA = "Mozilla/5.0 (X11; Linux x86_64) HockeyManager/1.0"

ROLE_MAP = {
    "entrenador": "head_coach",
    "segundo entrenador": "assistant",
    "preparador fisico": "fitness_coach",
    "preparador físico": "fitness_coach",
    "entrenador porteros": "gk_coach",
    "entrenador de porteros": "gk_coach",
    "fisioterapeuta": "physio",
    "psicologo": "psychologist",
    "psicólogo": "psychologist",
    "delegado equipo": "delegate",
    "medico": "doctor",
    "médico": "doctor",
    "staff adicional": "additional",
    "analista": "performance_analyst",
    "analista de rendimiento": "performance_analyst",
    "director deportivo": "technical_director",
    "ojeador": "scout",
}
BASE_SALARY = {
    "head_coach": 60000,
    "assistant": 38000,
    "fitness_coach": 28000,
    "gk_coach": 22000,
    "performance_analyst": 24000,
    "scout": 18000,
    "physio": 25000,
    "technical_director": 40000,
    "doctor": 26000,
    "psychologist": 24000,
    "delegate": 12000,
    "additional": 15000,
}


def norm(value: str) -> str:
    text = unicodedata.normalize("NFKD", htmlmod.unescape(str(value)))
    text = text.encode("ascii", "ignore").decode().upper()
    return re.sub(r"[^A-Z0-9]+", " ", text).strip()


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", htmlmod.unescape(str(value))).strip()


def team_urls() -> dict[str, str]:
    found: dict[str, str] = {}
    with PLAYERS.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            found.setdefault(norm(row["equipo"]), row["team_url"])
    return found


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", "ignore")


def rows(html: str) -> list[tuple[str, str]]:
    pattern = re.compile(
        r'<div class="nombres-equipos">.*?<img[^>]*alt="([^"]*)"[^>]*>.*?</div>\s*([^<]*?)\s*</div>\s*</td>\s*'
        r"<td class='centrado'>\s*([^<]+?)\s*</td>",
        re.S | re.I,
    )
    found = []
    for match in pattern.finditer(html):
        name = clean(match.group(1) or match.group(2))
        role = clean(match.group(3))
        if name and role:
            found.append((name, role))
    return found


def main() -> None:
    clubs = json.loads((ROOT / "manager" / "data" / "clubs.json").read_text(encoding="utf-8"))
    urls = team_urls()
    result: dict[str, dict] = {}
    for club in clubs:
        url = urls.get(norm(club["name"]))
        if not url:
            print("SIN URL", club["id"])
            continue
        try:
            page = fetch(url)
            people = rows(page)
        except Exception as exc:
            print("ERROR", club["id"], exc)
            continue
        staff = []
        seen = set()
        head_seen = False
        for name, role in people:
            role_key = ROLE_MAP.get(norm(role).lower())
            if not role_key:
                continue
            if role_key == "head_coach":
                if head_seen:
                    role_key = "assistant"
                head_seen = True
            key = (role_key, norm(name))
            if key in seen:
                continue
            seen.add(key)
            digest = int(hashlib.sha1(f"{club['id']}:{name}:{role_key}".encode()).hexdigest()[:6], 16)
            if role_key == "head_coach":
                rating = 70 + digest % 16
            elif role_key == "assistant":
                rating = 64 + digest % 18
            elif role_key == "delegate":
                rating = 55 + digest % 12
            elif role_key == "additional":
                rating = 55 + digest % 15
            else:
                rating = 62 + digest % 20
            salary = int(BASE_SALARY.get(role_key, 20000) * (0.75 + rating / 180))
            staff.append(
                {
                    "role": role_key,
                    "name": name,
                    "rating": rating,
                    "salary": salary,
                    "contract_until": "2027-06-30",
                    "source": "iSquad",
                    "confidence": "media",
                }
            )
        if not any(item["role"] == "head_coach" for item in staff):
            print("SIN ENTRENADOR", club["id"])
        result[club["id"]] = {"staff": staff, "source_url": url}
        print(f"{club['id']:<24} {len(staff)} personas")
        time.sleep(0.15)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nGuardado {OUT} con {len(result)} clubes")


if __name__ == "__main__":
    main()
