import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

df = pd.read_csv(Path(__file__).resolve().parent / "todos_manifest_positions.csv", encoding="utf-8-sig").fillna("")
df["edad"] = pd.to_numeric(df["edad"], errors="coerce").fillna(22).astype(int)
df["goles_num"] = pd.to_numeric(df["goles"], errors="coerce").fillna(0).astype(int)

# Añade las plantillas de divisiones autonómicas que no son jugables. Sus
# jugadores se usarán como agentes libres, nunca como equipos del calendario.
LOWER = Path(__file__).resolve().parent / "lower_divisions_players.csv"
if LOWER.exists():
    lower = pd.read_csv(LOWER, encoding="utf-8-sig").fillna("")
    lower["liga"] = lower["liga_code"].fillna(lower.get("liga", "1A"))
    for column in df.columns:
        if column not in lower.columns:
            lower[column] = ""
    df = pd.concat([df, lower[df.columns]], ignore_index=True)

ATTRS = [
    # Técnica base
    "control",
    "pase",
    "conduccion",
    "golpeo",
    "flick",
    "regate_3d",
    "definicion",
    # 3D y set pieces
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
    # Táctica
    "posicionamiento",
    "pressing",
    "cobertura",
    "transicion",
    "desmarque",
    # Física
    "velocidad",
    "resistencia",
    "fuerza",
    "agilidad",
    "coordinacion",
    # Mental
    "decisiones",
    "concentracion",
    "competitividad",
    "liderazgo",
    # Portero
    "reflejos",
    "blocaje",
    "distribucion",
    "uno_vs_uno",
    "alto",
    "rebote_gk",
]
ATTR_LABEL = {
    "control": "Control",
    "pase": "Pase",
    "conduccion": "Conducción",
    "golpeo": "Golpeo (hit/slap/sweep)",
    "flick": "Flick / scoop",
    "regate_3d": "Regate 3D",
    "definicion": "Definición",
    "aerial": "Aerial / scoop",
    "pc_injection": "Saque de PC (inyección)",
    "pc_trap": "Parada de PC (stopper)",
    "pc_flick": "Tiro de PC / drag flick",
    "pc_deflection": "Desvío en PC",
    "pc_first_runner": "Primer runner / defensa PC",
    "pc_gk_save": "Parada de PC (portero)",
    "stroke_shot": "Tiro de stroke",
    "stroke_save": "Parada de stroke",
    "free_hit": "Faltas, 16 yardas y córners",
    "posicionamiento": "Posicionamiento",
    "pressing": "Pressing",
    "cobertura": "Cobertura",
    "transicion": "Transición",
    "desmarque": "Desmarque",
    "velocidad": "Velocidad",
    "resistencia": "Resistencia",
    "fuerza": "Fuerza",
    "agilidad": "Agilidad",
    "coordinacion": "Coordinación",
    "decisiones": "Decisiones",
    "concentracion": "Concentración",
    "competitividad": "Competitividad",
    "liderazgo": "Liderazgo",
    "reflejos": "Reflejos",
    "blocaje": "Blocaje",
    "distribucion": "Distribución",
    "uno_vs_uno": "1 contra 1",
    "alto": "Paradas altas",
    "rebote_gk": "Control de rebotes",
}
GROUPS = {
    "Técnica": ["control", "pase", "conduccion", "golpeo", "flick", "regate_3d", "definicion"],
    "3D y set pieces": [
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
    ],
    "Táctica": ["posicionamiento", "pressing", "cobertura", "transicion", "desmarque"],
    "Física": ["velocidad", "resistencia", "fuerza", "agilidad", "coordinacion"],
    "Mental": ["decisiones", "concentracion", "competitividad", "liderazgo"],
    "Portero": ["reflejos", "blocaje", "distribucion", "uno_vs_uno", "alto", "rebote_gk"],
}
BIAS = {
    "Portero": {
        "posicionamiento": 5,
        "decisiones": 4,
        "concentracion": 5,
        "competitividad": 4,
        "liderazgo": 5,
        "reflejos": 16,
        "blocaje": 16,
        "distribucion": 9,
        "uno_vs_uno": 10,
        "alto": 12,
        "rebote_gk": 8,
        "pc_gk_save": 15,
        "stroke_save": 12,
        "control": -16,
        "pase": -10,
        "conduccion": -22,
        "golpeo": -20,
        "flick": -22,
        "regate_3d": -24,
        "definicion": -24,
        "aerial": -18,
        "pc_injection": -22,
        "pc_trap": -20,
        "pc_flick": -24,
        "pc_deflection": -24,
        "pc_first_runner": -20,
        "stroke_shot": -24,
        "free_hit": -18,
        "pressing": -18,
        "transicion": -14,
        "velocidad": -8,
        "resistencia": -5,
        "fuerza": -6,
        "agilidad": 2,
    },
    "Central": {
        "cobertura": 12,
        "posicionamiento": 9,
        "fuerza": 7,
        "pase": 3,
        "transicion": 4,
        "pressing": 4,
        "decisiones": 4,
        "liderazgo": 3,
        "pc_first_runner": 8,
        "pc_trap": 7,
        "pc_flick": 5,
        "aerial": 4,
        "free_hit": 3,
        "definicion": -10,
        "velocidad": -4,
        "regate_3d": -8,
        "flick": -6,
        "golpeo": 2,
        "control": 2,
        "conduccion": -2,
    },
    "Lateral": {
        "velocidad": 10,
        "resistencia": 7,
        "cobertura": 5,
        "pase": 4,
        "transicion": 5,
        "conduccion": 3,
        "pressing": 5,
        "agilidad": 4,
        "pc_first_runner": 7,
        "free_hit": 4,
        "aerial": 3,
        "definicion": -4,
        "fuerza": -2,
        "regate_3d": 2,
    },
    "Medio": {
        "pase": 9,
        "posicionamiento": 6,
        "resistencia": 7,
        "pressing": 6,
        "cobertura": 3,
        "transicion": 5,
        "decisiones": 3,
        "control": 3,
        "pc_injection": 7,
        "pc_trap": 5,
        "free_hit": 7,
        "aerial": 5,
        "definicion": -2,
        "velocidad": 2,
        "conduccion": 3,
    },
    "Delantero": {
        "definicion": 11,
        "velocidad": 7,
        "regate_3d": 7,
        "flick": 5,
        "posicionamiento": 2,
        "pressing": 2,
        "conduccion": 3,
        "pc_flick": 6,
        "pc_deflection": 9,
        "stroke_shot": 8,
        "aerial": 5,
        "cobertura": -7,
        "fuerza": -2,
        "transicion": -2,
    },
    "Polivalente": {
        "pase": 2,
        "posicionamiento": 3,
        "resistencia": 3,
        "velocidad": 2,
        "control": 2,
        "conduccion": 2,
        "cobertura": 2,
    },
}
W = {
    "POR": {
        "reflejos": 0.22,
        "blocaje": 0.20,
        "distribucion": 0.12,
        "pc_gk_save": 0.12,
        "stroke_save": 0.10,
        "uno_vs_uno": 0.08,
        "alto": 0.06,
        "posicionamiento": 0.05,
        "liderazgo": 0.05,
    },
    "CEN": {
        "cobertura": 0.18,
        "posicionamiento": 0.12,
        "pc_first_runner": 0.10,
        "pc_trap": 0.08,
        "fuerza": 0.10,
        "pase": 0.08,
        "decisiones": 0.08,
        "agilidad": 0.06,
        "velocidad": 0.05,
        "liderazgo": 0.05,
        "transicion": 0.05,
        "control": 0.05,
    },
    "LAT": {
        "velocidad": 0.16,
        "cobertura": 0.14,
        "resistencia": 0.12,
        "pase": 0.10,
        "conduccion": 0.08,
        "transicion": 0.08,
        "posicionamiento": 0.07,
        "pressing": 0.07,
        "agilidad": 0.06,
        "decisiones": 0.06,
        "pc_first_runner": 0.06,
    },
    "MED": {
        "pase": 0.16,
        "posicionamiento": 0.12,
        "resistencia": 0.12,
        "pressing": 0.08,
        "transicion": 0.08,
        "cobertura": 0.07,
        "conduccion": 0.07,
        "decisiones": 0.07,
        "pc_injection": 0.06,
        "free_hit": 0.05,
        "control": 0.05,
        "desmarque": 0.04,
        "pc_trap": 0.03,
    },
    "DEL": {
        "definicion": 0.20,
        "velocidad": 0.13,
        "regate_3d": 0.12,
        "posicionamiento": 0.08,
        "conduccion": 0.08,
        "aerial": 0.06,
        "pc_flick": 0.06,
        "pc_deflection": 0.06,
        "decisiones": 0.06,
        "resistencia": 0.05,
        "desmarque": 0.05,
        "flick": 0.05,
    },
}


def age_curve(a):
    if a <= 20:
        return max(0.5, min(1, 0.55 + (a - 16) * 0.06))
    if a <= 24:
        return min(1, 0.80 + (a - 21) * 0.05)
    if a <= 29:
        return 1.0
    if a <= 32:
        return 0.92
    return 0.78


def pct_rank(v, arr):
    if not arr:
        return 0.5
    below = sum(1 for x in arr if x < v)
    equal = sum(1 for x in arr if x == v)
    return (below + 0.5 * equal) / len(arr)


def rng_for(key):
    h = hashlib.md5(key.encode("utf-8")).hexdigest()
    return np.random.default_rng(int(h[:8], 16))


def clamp(x, a=25, b=99):
    return int(round(max(a, min(b, x))))


# Fuerza de equipo basada en clasificaciones reales 2025-26 / 2026-27.
# No se usan los goles de una categoría inferior para inflar a un recién
# ascendido: Pozuelo y San Fernando se miden por lo que hacen en DHB.
TEAM_STRENGTH = {
    ("DHA", "CD TERRASSA HOCKEY"): 0.61,
    ("DHA", "RC POLO"): 0.83,
    ("DHA", "JUNIOR FC"): 0.72,
    ("DHA", "REAL CLUB DE CAMPO VILLA DE MADRID"): 0.74,
    ("DHA", "RS TENIS"): 0.42,
    ("DHA", "SANSE COMPLUTENSE"): 0.61,
    ("DHA", "CLUB EGARA"): 0.50,
    ("DHA", "ATLÈTIC TERRASSA HC"): 0.58,
    ("DHA", "CH CARPESA"): 0.33,
    ("DHA", "FC BARCELONA"): 0.35,
    ("DHA", "UD TABURIENTE"): 0.09,
    ("DHA", "SARDINERO HOCKEY CLUB"): 0.07,
    ("DHB", "RC JOLASETA"): 0.48,
    ("DHB", "VALLES ESPORTIU"): 0.83,
    ("DHB", "REAL SOCIEDAD 1927"): 0.54,
    ("DHB", "PEDRALBES HC"): 0.63,
    ("DHB", "SPV"): 0.33,
    ("DHB", "UNIVERSITAT D'ALACANT - SAN VICENTE"): 0.21,
    ("DHB", "ILURO HC"): 0.17,
    ("DHB", "ATICOS INMOBILIARIA CH SAN FERNANDO"): 0.04,
    ("DHB", "HC SANT CUGAT"): 0.79,
    ("DHB", "EGARA 1935"): 0.63,
    ("DHB", "CLUB HOCKEY MADRID - LAS ROZAS"): 0.54,
    ("DHB", "POZUELO"): 0.54,
    ("DHB", "CASTELLDEFELS HC"): 0.50,
    ("DHB", "AD RIMAS"): 0.46,
    ("DHB", "CD GINER DE LOS RÍOS"): 0.25,
    ("DHB", "LINIA 22 STERN MOTOR"): 0.13,
    ("1ª Andaluza", "CLUB DE HOCKEY SAN FERNANDO"): 0.45,
    ("1A", "RH PRIVÉ BENALMÁDENA"): 0.55,
    ("1A", "CARRANQUE ARCHIDONA CANDELARIA"): 0.52,
    ("1A", "CH ALCALÁ"): 0.50,
    ("1A", "ESTUDIANTES 87 PGS ILUMINACIÓN CODIMAR CLIDECEM"): 0.48,
    ("1A", "UNIVERSIDAD DE SEVILLA"): 0.48,
    ("1A", "C.D. MÁLAGA 91"): 0.45,
}
LEAGUE_BASE = {
    "DHA": 56,
    "DHB": 46,
    "1ª Andaluza": 36,
    "1A": 36,
    "1N": 35,
    "1M": 35,
    "1G": 35,
    "1C": 35,
    "1V": 35,
    "SUP": 41,
    "CAT1": 33,
}
# Equipos autonómicos que sí han competido en DHB en las últimas temporadas.
# El resto no recibe el plus de contexto DHB y baja su media.
DHB_HISTORY = {
    "RH PRIVÉ BENALMÁDENA",
    "ATLÉTICO SAN SEBASTIÁN",
    "CH BARROCAS",
}
LEAGUE_VALUE_FACTOR = {
    "DHA": 1.0,
    "DHB": 0.55,
    "1ª Andaluza": 0.22,
    "1A": 0.22,
    "1N": 0.22,
    "1M": 0.22,
    "1G": 0.22,
    "1C": 0.22,
    "1V": 0.22,
    "SUP": 0.30,
    "CAT1": 0.18,
}
team_strength = {
    (liga, team): TEAM_STRENGTH.get((liga, team), 0.50)
    for liga, team in df[["liga", "equipo"]].drop_duplicates().itertuples(index=False, name=None)
}
goal_pct = {}
for liga, g in df.groupby("liga"):
    vals = g["goles_num"].tolist()
    for idx, r in g.iterrows():
        goal_pct[idx] = pct_rank(r["goles_num"], vals)

# Estimación de posiciones para plantillas autonómicas sin posición publicada.
for (liga, team), g in df.groupby(["liga", "equipo"]):
    if not g["pos"].astype(str).str.strip().eq("").all():
        continue
    ordered = sorted(g.index, key=lambda i: (float(g.loc[i, "goles_num"]), hashlib.md5((str(g.loc[i, "jugador"]) + team).encode()).hexdigest()))
    n = len(ordered)
    gk_count = 2 if n >= 16 else 1
    def_count = max(3, round(n * 0.28))
    mid_count = max(3, round(n * 0.28))
    for position, index in enumerate(ordered):
        if position < gk_count:
            pos = "Portero"
        elif position < gk_count + def_count:
            digest = int(hashlib.md5((str(df.loc[index, "jugador"]) + team).encode()).hexdigest()[:2], 16)
            pos = "Defensa Central" if digest % 100 < 55 else "Defensa Lateral"
        elif position < gk_count + def_count + mid_count:
            pos = "Medio"
        else:
            pos = "Delantero"
        df.loc[index, "pos"] = pos
        df.loc[index, "src"] = "Estimada"
        df.loc[index, "conf"] = "Baja"


def group_for(pos, name):
    p = str(pos)
    if "Portero" in p:
        return "Portero", "Portero"
    if "Defensa/Medio" in p or "Medio/Delantero" in p:
        return "Polivalente", "Polivalente"
    if "Defensa" in p:
        pl = p.lower()
        if "central" in pl:
            return "Defensa", "Central"
        if "lateral" in pl or "izquierd" in pl or "derech" in pl:
            return "Defensa", "Lateral"
        h = int(hashlib.md5(name.encode("utf-8")).hexdigest()[:2], 16)
        return "Defensa", ("Central" if h % 100 < 55 else "Lateral")
    if "Medio" in p:
        return "Medio", "Medio"
    if "Delantero" in p:
        return "Delantero", "Delantero"
    return "Polivalente", "Polivalente"


rows = []
for idx, r in df.iterrows():
    rng = rng_for(r["jugador"] + "|" + r["equipo"] + "|v2")
    grupo, sub = group_for(r["pos"], r["jugador"])
    lower_division = r["liga"] not in ("DHA", "DHB")
    history_bonus = 0.0
    if lower_division:
        history_bonus = 2.0 if r["equipo"] in DHB_HISTORY else -2.0
    base = (
        LEAGUE_BASE.get(r["liga"], 36)
        + 12 * team_strength.get((r["liga"], r["equipo"]), 0.50)
        + 5 * goal_pct[idx]
        + 5 * age_curve(r["edad"])
        + history_bonus
        + rng.normal(0, 2.5)
    )
    if r["perfil"] == "Invitado":
        base -= 4
    base = max(36, min(88, base))
    fuerza_proxy = clamp(base + BIAS.get(sub, {}).get("fuerza", 0) + rng.normal(0, 7))
    attrs = {}
    for a in ATTRS:
        bias = BIAS.get(sub, {}).get(a, 0)
        if sub == "Portero" and a in [
            "reflejos",
            "blocaje",
            "distribucion",
            "uno_vs_uno",
            "alto",
            "rebote_gk",
            "pc_gk_save",
            "stroke_save",
        ]:
            val = base + bias + rng.normal(0, 6)
        elif sub == "Portero":
            val = 32 + 0.28 * base + bias * 0.4 + rng.normal(0, 6)
        elif a in [
            "reflejos",
            "blocaje",
            "distribucion",
            "uno_vs_uno",
            "alto",
            "rebote_gk",
            "pc_gk_save",
            "stroke_save",
        ]:
            val = 19 + 0.22 * base + rng.normal(0, 5)
        else:
            val = base + bias + rng.normal(0, 7)
        # goals boost finishing/PC for field players
        if sub != "Portero" and a in ["definicion", "flick", "pc_flick", "pc_deflection", "stroke_shot"]:
            boost = min(15, r["goles_num"] * 0.15) if a == "definicion" else min(10, r["goles_num"] * 0.10)
            val += boost
        # central defenders as drag-flick specialists: strength/height proxy
        if sub == "Central" and a == "pc_flick":
            val += min(8, fuerza_proxy / 12)
        attrs[a] = clamp(val)

    def ov(w):
        return round(sum(attrs[a] * wt for a, wt in w.items()), 1)

    ovs = {
        "Portero": ov(W["POR"]),
        "Central": ov(W["CEN"]),
        "Lateral": ov(W["LAT"]),
        "Medio": ov(W["MED"]),
        "Delantero": ov(W["DEL"]),
    }
    if sub == "Portero":
        pos_group = "Portero"
        subpos = "Portero"
        primary = ovs["Portero"]
    elif sub == "Central":
        pos_group = "Defensa"
        subpos = "Central"
        primary = ovs["Central"]
    elif sub == "Lateral":
        pos_group = "Defensa"
        subpos = "Lateral"
        primary = ovs["Lateral"]
    elif sub == "Medio":
        pos_group = "Medio"
        subpos = "Medio"
        primary = ovs["Medio"]
    elif sub == "Delantero":
        pos_group = "Delantero"
        subpos = "Delantero"
        primary = ovs["Delantero"]
    else:
        pos_group = "Polivalente"
        subpos = "Polivalente"
        primary = max(ovs.values())
    primary = min(95, max(40, primary))
    # archetype
    if subpos == "Central":
        arch = (
            "Muro"
            if attrs["cobertura"] >= 80 and attrs["fuerza"] >= 75
            else "Central constructor"
            if attrs["pase"] >= 75
            else "Central sólido"
        )
    elif subpos == "Lateral":
        arch = "Lateral ofensivo" if attrs["velocidad"] >= 80 and attrs["pase"] >= 70 else "Lateral defensivo"
    elif subpos == "Medio":
        arch = (
            "Medio creativo"
            if attrs["pase"] >= 80 and attrs["posicionamiento"] >= 75
            else "Medio box-to-box"
            if attrs["resistencia"] >= 80
            else "Medio de equilibrio"
        )
    elif subpos == "Delantero":
        arch = (
            "Finalizador"
            if attrs["definicion"] >= 82
            else "Delantero de espacio"
            if attrs["velocidad"] >= 80
            else "Delantero de área"
        )
    elif subpos == "Portero":
        arch = "Portero moderno" if attrs["distribucion"] >= 75 else "Portero clásico"
    else:
        arch = "Jugador polivalente"
    natural = ovs.get(subpos, primary) if subpos in ovs else primary
    alts = [v for k, v in ovs.items() if k != subpos]
    best_alt = max(alts) if alts else natural
    poly = max(0, min(20, best_alt - natural))
    youth = (24 - r["edad"]) * 1.5 + 2 if r["edad"] <= 23 else (2 if r["edad"] <= 27 else -(r["edad"] - 27) * 1.0)
    potential = max(40, min(99, primary + youth))
    age_mult = (
        1.4
        if r["edad"] <= 21
        else 1.3
        if r["edad"] <= 24
        else 1.0
        if r["edad"] <= 27
        else 0.6
        if r["edad"] <= 30
        else 0.3
    )
    pos_mult = {"Portero": 0.9, "Defensa": 0.95, "Medio": 1.0, "Delantero": 1.1, "Polivalente": 1.05}.get(
        pos_group, 1.0
    )
    value = round(((primary / 100) ** 4 * 2000000 * age_mult * pos_mult * LEAGUE_VALUE_FACTOR.get(r["liga"], 0.22)) / 10000) * 10000
    rows.append(
        {
            **r.to_dict(),
            "position_group": pos_group,
            "subposicion": subpos,
            "sub_estimada": subpos in ["Central", "Lateral"]
            and not any(k in str(r["pos"]).lower() for k in ["central", "lateral", "izquierd", "derech"]),
            "archetype": arch,
            "overall": round(primary, 1),
            "potential": round(potential, 1),
            "value": value,
            "polivalencia": round(poly, 1),
            "overall_portero": ovs["Portero"],
            "overall_central": ovs["Central"],
            "overall_lateral": ovs["Lateral"],
            "overall_medio": ovs["Medio"],
            "overall_delantero": ovs["Delantero"],
            **{f"attr_{a}": attrs[a] for a in ATTRS},
        }
    )
out = pd.DataFrame(rows)

# Escalera de niveles. Cada liga se desplaza en bloque para conservar su
# dispersión interna y fijar una frontera reconocible:
#   DHA 74,8 > DHB 64,0 > 1A 56,2
# El último de DHA queda al nivel del primero de DHB y el último de DHB al
# nivel del primero de 1A. Superlliga Catalana se coloca entre 1A y DHB.
LEAGUE_TARGET_MEAN = {
    "DHA": 74.8,
    "DHB": 64.0,
    "1ª Andaluza": 56.2,
    "1A": 56.2,
    "1N": 54.0,
    "1M": 54.0,
    "1G": 54.0,
    "1C": 53.0,
    "1V": 54.0,
    "SUP": 59.0,
    "CAT1": 53.0,
}
for league, target in LEAGUE_TARGET_MEAN.items():
    mask = out["liga"] == league
    if not mask.any():
        continue
    current = float(out.loc[mask, "overall"].mean())
    shift = target - current
    for column in [
        "overall",
        "overall_portero",
        "overall_central",
        "overall_lateral",
        "overall_medio",
        "overall_delantero",
        "potential",
    ]:
        out.loc[mask, column] = (out.loc[mask, column] + shift).clip(40, 99).round(2)
    out.loc[mask, "potential"] = out.loc[mask, ["potential", "overall"]].max(axis=1)

# Comprobación de la frontera principal: el mejor equipo de una liga no
# debe superar al peor de la liga inmediatamente superior. Si ocurre, se
# rebaja el bloque del equipo infractor sin cambiar su plantilla.
def _team_means(code):
    return (
        out[out["liga"] == code]
        .groupby("equipo")["overall"]
        .mean()
        .sort_values()
    )


def _cap_team_means(code: str, cap: float) -> None:
    for _, group in out[out["liga"] == code].groupby("equipo"):
        mean = float(group["overall"].mean())
        if mean <= cap:
            continue
        shift = cap - mean
        for column in [
            "overall",
            "overall_portero",
            "overall_central",
            "overall_lateral",
            "overall_medio",
            "overall_delantero",
            "potential",
        ]:
            out.loc[group.index, column] = (out.loc[group.index, column] + shift).clip(40, 99).round(2)
        out.loc[group.index, "potential"] = out.loc[group.index, ["potential", "overall"]].max(axis=1)

dha_means = _team_means("DHA")
dhb_means = _team_means("DHB")
if not dha_means.empty and not dhb_means.empty:
    _cap_team_means("DHB", float(dha_means.min()) - 0.01)

dhb_means = _team_means("DHB")
primera_means = _team_means("1A")
if not dhb_means.empty and not primera_means.empty:
    _cap_team_means("1A", float(dhb_means.min()) - 0.01)

primera_means = _team_means("1A")
if not primera_means.empty:
    regional_cap = float(primera_means.min()) - 0.01
    for code in ("1N", "1M", "1G", "1C", "1V", "CAT1"):
        _cap_team_means(code, regional_cap)
    _cap_team_means("SUP", float(dhb_means.min()) - 0.01)

dha_means = _team_means("DHA")
dhb_means = _team_means("DHB")
primera_means = _team_means("1A")
if not dha_means.empty and not dhb_means.empty:
    print(f"Frontera DHA/DHB: DHA min {dha_means.min():.2f} · DHB max {dhb_means.max():.2f}")
if not dhb_means.empty and not primera_means.empty:
    print(f"Frontera DHB/1A: DHB min {dhb_means.min():.2f} · 1A max {primera_means.max():.2f}")

# Specialists per team
for team, g in out.groupby("equipo"):
    specs = {}
    squad = g[g["perfil"] == "Jugador"]
    base = squad if len(squad) else g
    for key, attr in [
        ("pc_flicker", "pc_flick"),
        ("pc_injector", "pc_injection"),
        ("pc_stopper", "pc_trap"),
        ("pc_deflector", "pc_deflection"),
        ("pc_first_runner", "pc_first_runner"),
        ("pc_goalkeeper", "pc_gk_save"),
        ("stroke_taker", "stroke_shot"),
        ("stroke_goalkeeper", "stroke_save"),
        ("aerial_specialist", "aerial"),
        ("free_hit_taker", "free_hit"),
    ]:
        candidates = base
        if key in ("pc_goalkeeper", "stroke_goalkeeper"):
            gks = base[base["subposicion"] == "Portero"]
            if len(gks):
                candidates = gks
        best = candidates.nlargest(1, f"attr_{attr}").iloc[0]
        specs[key] = best["jugador"]
    out.loc[g.index, "team_specialists"] = json.dumps(specs, ensure_ascii=False)

out.to_csv(Path(__file__).resolve().parent / "player_attributes_v2.csv", index=False, encoding="utf-8-sig")
print("rows", len(out))
print(out.groupby(["position_group", "subposicion"]).size().to_string())
print("\nTop overall:")
print(
    out.nlargest(10, "overall")[
        ["jugador", "equipo", "position_group", "subposicion", "archetype", "overall", "potential", "value"]
    ].to_string(index=False)
)
print("\nDefenders with most goals:")
print(
    out[out["position_group"] == "Defensa"]
    .nlargest(8, "goles_num")[
        [
            "jugador",
            "equipo",
            "subposicion",
            "goles_num",
            "overall_central",
            "overall_lateral",
            "attr_pc_flick",
            "archetype",
        ]
    ]
    .to_string(index=False)
)
print("\nIain:")
print(
    out[out["jugador"] == "IAIN MARTIN MCFADDEN"][
        [
            "jugador",
            "equipo",
            "pos",
            "subposicion",
            "archetype",
            "overall",
            "overall_central",
            "overall_lateral",
            "attr_pc_first_runner",
            "attr_pc_trap",
            "attr_pc_flick",
        ]
    ].to_string(index=False)
)
