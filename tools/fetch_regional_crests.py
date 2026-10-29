"""Descarga escudos reales de iSquad para los equipos regionales."""

from __future__ import annotations

import csv
import json
import urllib.parse
from pathlib import Path

from fetch_isquad_crests import crest_url, fetch, transparent_png

ROOT = Path(__file__).resolve().parents[1]
REGIONAL = ROOT / "manager" / "data" / "regional_teams.json"
LOWER = ROOT / "tools" / "lower_divisions_players.csv"
PLAYERS = ROOT / "tools" / "player_attributes_v2.csv"
OUT = ROOT / "manager" / "web" / "static" / "crests"


def main() -> None:
    teams = json.loads(REGIONAL.read_text(encoding="utf-8"))
    urls: dict[str, str] = {}
    with LOWER.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            urls.setdefault(str(row.get("equipo", "")).strip(), str(row.get("team_url", "")).strip())
    with PLAYERS.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            urls.setdefault(str(row.get("equipo", "")).strip(), str(row.get("team_url", "")).strip())
    ok = 0
    failed = []
    for team in teams:
        name = team["name"]
        url = urls.get(name, "")
        if not url:
            failed.append(f"{team['id']}: sin URL")
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
            image.save(OUT / f"{team['id']}.png", optimize=True)
            print("OK ", team["id"], image.size)
            ok += 1
        except Exception as exc:
            failed.append(f"{team['id']}: {exc}")
            print("ERR", team["id"], exc)
    print(f"\nEscudos regionales: {ok}/{len(teams)}")
    for item in failed:
        print(" -", item)


if __name__ == "__main__":
    main()
