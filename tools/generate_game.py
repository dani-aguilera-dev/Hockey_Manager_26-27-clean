import json
import os
import re
import unicodedata
from pathlib import Path

import pandas as pd

TOOLS = Path(__file__).resolve().parent
BASE = str(TOOLS.parent)
ATTRS = [
    "control",
    "pase",
    "conduccion",
    "golpeo",
    "flick",
    "regate_3d",
    "definicion",
    "aerial",
    "pc_injection",
    "pc_trap",
    "pc_flick",
    "pc_deflection",
    "pc_first_runner",
    "pc_gk_save",
    "stroke_shot",
    "stroke_save",
    "free_hit",
    "posicionamiento",
    "pressing",
    "cobertura",
    "transicion",
    "desmarque",
    "velocidad",
    "resistencia",
    "fuerza",
    "agilidad",
    "coordinacion",
    "decisiones",
    "concentracion",
    "competitividad",
    "liderazgo",
    "reflejos",
    "blocaje",
    "distribucion",
    "uno_vs_uno",
    "alto",
    "rebote_gk",
]
df = pd.read_csv(TOOLS / "player_attributes_v2.csv", encoding="utf-8-sig").fillna("")
df = df[df["perfil"].isin(["Jugador", "Invitado"])].copy()
df["edad"] = pd.to_numeric(df["edad"], errors="coerce").fillna(22).astype(int)
df["goles"] = pd.to_numeric(df["goles"], errors="coerce").fillna(0).astype(int)
df["estado"] = df["fecha_baja"].apply(lambda x: f"Baja ({x})" if str(x).strip() else "En plantilla")


def slug(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s or "equipo"


league_map = {"DHA": "DHA", "DHB": "DHB", "1ª Andaluza": "1A"}
df["league"] = df["liga"].map(league_map)
df["team_id"] = df.apply(lambda r: slug(f"{r['league']}-{r['equipo']}"), axis=1)

teams = []
for (league, team_id, equipo, club), g in df.groupby(["league", "team_id", "equipo", "club"], sort=False):
    spec = {}
    try:
        spec = json.loads(str(g.iloc[0].get("team_specialists", "") or "{}"))
    except Exception:
        spec = {}
    teams.append({"id": team_id, "name": equipo, "club": club, "league": league, "specialists": spec})
teams.sort(key=lambda t: (["DHA", "DHB", "1A"].index(t["league"]), t["name"]))
linked = {
    "EGARA 1935": "CLUB EGARA",
    "VALLES ESPORTIU": "ATLÈTIC TERRASSA HC",
    "PEDRALBES HC": "RC POLO",
    "REAL SOCIEDAD 1927": "REAL CLUB DE CAMPO VILLA DE MADRID",
    "SPV": "SANSE COMPLUTENSE",
    "AD RIMAS": "CD TERRASSA HOCKEY",
}
for t in teams:
    t["linkedTo"] = linked.get(t["name"], "")

players = []
for _, r in df.iterrows():
    players.append(
        {
            "teamId": r["team_id"],
            "teamName": r["equipo"],
            "club": r["club"],
            "league": r["league"],
            "name": r["jugador"],
            "age": int(r["edad"]),
            "goals": int(r["goles"]),
            "perfil": r["perfil"],
            "estado": r["estado"] if str(r["estado"]).strip() else "En plantilla",
            "posicion": r.get("pos", ""),
            "posicion_fuente": r.get("src", ""),
            "posicion_confianza": r.get("conf", ""),
            "posicion_url": r.get("pos_url", ""),
            "posicion_fecha": r.get("pos_fecha", ""),
            "position_group": r.get("position_group", ""),
            "subposicion": r.get("subposicion", ""),
            "sub_estimada": bool(r.get("sub_estimada", False)),
            "archetype": r.get("archetype", ""),
            "overall": float(r.get("overall", 0) or 0),
            "potential": float(r.get("potential", 0) or 0),
            "value": int(float(r.get("value", 0) or 0)),
            "polivalencia": float(r.get("polivalencia", 0) or 0),
            "attributes": {a: int(float(r.get(f"attr_{a}", 0) or 0)) for a in ATTRS},
            "overalls": {
                "Portero": float(r.get("overall_portero", 0) or 0),
                "Central": float(r.get("overall_central", 0) or 0),
                "Lateral": float(r.get("overall_lateral", 0) or 0),
                "Medio": float(r.get("overall_medio", 0) or 0),
                "Delantero": float(r.get("overall_delantero", 0) or 0),
            },
            "img": "../jugadores/thumbs/" + str(r["archivo_thumb"]).replace("\\", "/"),
        }
    )

data = {"generated": "2026-10-19", "season": "2026-27", "teams": teams, "players": players}
js = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

tpl = open(TOOLS / "hockey_template.html", encoding="utf-8").read()
html = tpl.replace("__DATA_JSON__", js)
os.makedirs(os.path.join(BASE, "juego_hockey"), exist_ok=True)
out = os.path.join(BASE, "juego_hockey", "index.html")
open(out, "w", encoding="utf-8").write(html)
print("HTML:", out, "size", len(html), "teams", len(teams), "players", len(players))
print("Leagues:", {l: sum(1 for t in teams if t["league"] == l) for l in ["DHA", "DHB", "1A"]})
print("Players by league:", {l: sum(1 for p in players if p["league"] == l) for l in ["DHA", "DHB", "1A"]})
