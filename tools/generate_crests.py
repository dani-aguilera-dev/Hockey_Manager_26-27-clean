"""Genera escudos SVG estilizados a partir de los colores de cada club.

Uso:
    python3 tools/generate_crests.py

Los escudos resultantes se guardan en manager/web/static/crests/.
Para usar un escudo oficial, coloca un PNG con el mismo id del club
(p. ej. cd-terrassa.png) en esa carpeta: la web le dará prioridad.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLUBS = ROOT / "manager" / "data" / "clubs.json"
OUT = ROOT / "manager" / "web" / "static" / "crests"

COLORS = {
    "amarillo": "#f4c542",
    "negro": "#111827",
    "rojo": "#d92d20",
    "blanco": "#eef4ff",
    "azul": "#2563eb",
    "grana": "#7b1e3a",
    "verde": "#16a34a",
    "naranja": "#f97316",
    "gris": "#6b7280",
    "celeste": "#38bdf8",
    "morado": "#7c3aed",
    "dorado": "#d4af37",
    "azulgrana": "#004d98",
    "burdeos": "#7f1d1d",
    "rosa": "#ec4899",
    "marron": "#92400e",
    "plata": "#94a3b8",
    "turquesa": "#14b8a6",
    "lima": "#84cc16",
    "beige": "#d6c7a1",
}
ACRONYMS = {"CD", "CH", "FC", "RC", "HC", "UD", "AD", "CF", "SD", "BM"}
STOPWORDS = {
    "DE",
    "DEL",
    "LA",
    "EL",
    "LOS",
    "LAS",
}


def normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    text = text.encode("ascii", "ignore").decode().upper()
    return re.sub(r"[^A-Z0-9]+", " ", text).strip()


def initials(name: str) -> str:
    words = normalize(name).split()
    if not words:
        return "HC"
    if words[0] in ACRONYMS and len(words) > 1:
        return (words[0] + words[1][0])[:3]
    significant = [word for word in words if word not in STOPWORDS] or words
    letters = [word for word in significant if word[0].isalpha()] or significant
    if len(letters) == 1:
        return letters[0][:3].upper()
    return "".join(word[0] for word in letters[:3])[:3] or "HC"


def luminance(hex_color: str) -> float:
    raw = hex_color.lstrip("#")
    channels = [int(raw[i : i + 2], 16) / 255 for i in (0, 2, 4)]

    def linear(channel: float) -> float:
        return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4

    r, g, b = (linear(channel) for channel in channels)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def crest_svg(club: dict) -> str:
    colors = [COLORS.get(str(color).lower(), "#64748b") for color in club.get("colors", [])]
    primary = colors[0] if colors else "#2563eb"
    secondary = colors[1] if len(colors) > 1 else "#ffb020"
    if secondary == primary:
        secondary = "#ffb020"
    foreground = "#07111f" if luminance(primary) > 0.55 else "#f8fbff"
    abbr = initials(club["name"])
    year = str(club.get("founded", ""))[-4:] if club.get("founded") else ""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96" role="img" aria-label="Escudo {club["name"]}">
<path d="M10 7h76v38c0 25-21 39-38 47C31 84 10 70 10 45Z" fill="{primary}" stroke="#0b1220" stroke-width="3"/>
<path d="M10 7h15v57l-15-8Z" fill="{secondary}" opacity=".62"/>
<path d="M83 7h3v38c0 12-5 21-12 28V7Z" fill="{secondary}" opacity=".45"/>
<path d="M16 13h64v31c0 20-17 32-32 39-15-7-32-19-32-39Z" fill="none" stroke="rgba(255,255,255,.58)" stroke-width="2"/>
<circle cx="48" cy="25" r="5.5" fill="rgba(255,255,255,.18)" stroke="rgba(255,255,255,.72)" stroke-width="1.3"/>
<circle cx="48" cy="25" r="1.8" fill="rgba(255,255,255,.7)"/>
<text x="48" y="59" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="23" font-weight="800" letter-spacing=".5" fill="{foreground}">{abbr}</text>
<text x="48" y="73" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="7" font-weight="700" letter-spacing="1.4" fill="{foreground}" opacity=".85">{year or "HC"}</text>
</svg>'''


def main() -> None:
    clubs = json.loads(CLUBS.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    for club in clubs:
        path = OUT / f"{club['id']}.svg"
        path.write_text(crest_svg(club), encoding="utf-8")
    print(f"Escudos generados: {len(clubs)} en {OUT}")


if __name__ == "__main__":
    main()
