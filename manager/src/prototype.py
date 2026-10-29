#!/usr/bin/env python3
"""Prototipo de texto de Hockey Manager España 2026-27.

No es el juego completo: es un vertical slice para validar el bucle
club -> logística -> partido -> clasificación.

Uso:
  python3 prototype.py --demo
  python3 prototype.py --club "CD TERRASSA HOCKEY" --auto
  python3 prototype.py            # interactivo
"""

import argparse
import csv
import json
import math
import random
import unicodedata
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
DATA = BASE / "manager" / "data"
SAVES = BASE / "manager" / "saves"
TOOLS = BASE / "tools"


def norm(s):
    s = str(s or "").upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = "".join(c if c.isalnum() or c == " " else " " for c in s)
    return " ".join(s.split())


def load_json(name):
    return json.load(open(DATA / name, encoding="utf-8"))


def load_players():
    rows = list(csv.DictReader(open(TOOLS / "player_attributes_v2.csv", encoding="utf-8-sig")))
    for r in rows:
        for k in ("edad", "goles"):
            try:
                r[k] = int(float(r.get(k) or 0))
            except:
                r[k] = 0
        for k, v in list(r.items()):
            if k.startswith("attr_"):
                try:
                    r[k] = int(float(v or 50))
                except:
                    r[k] = 50
        try:
            r["overall"] = float(r.get("overall") or 0)
        except:
            r["overall"] = 0.0
    return rows


def haversine(a, b):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [a["lat"], a["lon"], b["lat"], b["lon"]])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def travel_plan(club, rival, city_by_id):
    a = (
        city_by_id[club["city"].lower().replace(" ", "-")]
        if club["city"].lower().replace(" ", "-") in city_by_id
        else None
    )
    # fallback: match by name
    if a is None:
        for c in city_by_id.values():
            if norm(c["name"]) == norm(club["city"]):
                a = c
                break
    b = None
    for c in city_by_id.values():
        if norm(c["name"]) == norm(rival["city"]):
            b = c
            break
    if a is None or b is None:
        return {
            "distance_km": 0,
            "mode": "bus",
            "hours": 1,
            "cost": 200,
            "fatigue": 0.02,
            "notes": "Distancia no calculada",
        }
    d = haversine(a, b)
    island = a.get("airport") == "LPA" or b.get("airport") == "LPA"
    if island or d > 700:
        mode = "avión"
    elif d > 350 and a.get("train") not in (None, "", "No") and b.get("train") not in (None, "", "No"):
        mode = "tren"
    else:
        mode = "bus"
    if mode == "avión":
        hours = 4.5 + d / 800
        cost = 150 * 18 + 2 * 70 * 18 + 25 * 3 * 18 + 300
        fatigue = 0.18 + (0.06 if d > 1500 else 0)
        notes = "Vuelo + traslado; hotel recomendado."
    elif mode == "tren":
        hours = 1.2 + d / 120
        cost = 45 * 18 + 70 * 18 + 25 * 2 * 18
        fatigue = 0.08 + (0.04 if d > 500 else 0)
        notes = "Tren; hotel si el viaje es largo."
    else:
        hours = 0.8 + d / 80
        if d < 100:
            cost = 1.2 * d + 150
            fatigue = 0.01
            notes = "Bus; desplazamiento corto, sin hotel."
        elif d < 250:
            cost = 1.2 * d + 25 * 18 + 200
            fatigue = 0.03
            notes = "Bus; comida de viaje y vuelta el mismo día."
        else:
            cost = 1.2 * d + 70 * 18 + 25 * 2 * 18 + 300
            fatigue = 0.08
            notes = "Bus; hotel y dos comidas."
    if mode == "tren":
        cost = 45 * 18 + (70 * 18 if d > 350 else 0) + 25 * (2 if d > 250 else 1) * 18
        fatigue = 0.08 + (0.04 if d > 500 else 0)
        notes = "Tren; hotel si el viaje es largo."

    return {
        "distance_km": round(d),
        "mode": mode,
        "hours": round(hours, 1),
        "cost": int(cost),
        "fatigue": round(fatigue, 2),
        "notes": notes,
    }


def team_profile(team_name, players):
    squad = [p for p in players if norm(p["equipo"]) == norm(team_name) and p.get("perfil") == "Jugador"]
    if not squad:
        squad = [p for p in players if norm(p["equipo"]) == norm(team_name)]
    top = sorted(squad, key=lambda p: p["overall"], reverse=True)[:11]

    def m(keys):
        vals = []
        for p in top:
            vals.append(sum(p.get(k, 50) for k in keys) / len(keys))
        return sum(vals) / len(vals) if vals else 50

    attack = m(["attr_definicion", "attr_pc_flick", "attr_regate_3d", "attr_pase", "attr_velocidad"])
    defense = m(["attr_cobertura", "attr_posicionamiento", "attr_pc_first_runner", "attr_pressing", "attr_fuerza"])
    return {
        "squad": squad,
        "overall": sum(p["overall"] for p in top) / len(top) if top else 50,
        "attack": attack,
        "defense": defense,
        "top": top,
        "goals": sum(p["goles"] for p in squad),
    }


def poisson(lam, rng):
    # Knuth
    L = math.exp(-max(0.01, lam))
    k = 0
    p = 1.0
    while True:
        k += 1
        p *= rng.random()
        if p <= L:
            return k - 1


def sim_match(home, away, hp, ap, rng, detailed=False):
    home_adv = 1.12
    lam_h = max(0.3, min(6.0, 2.4 * (hp["attack"] / max(30, ap["defense"])) ** 2.0 * home_adv))
    lam_a = max(0.3, min(6.0, 2.4 * (ap["attack"] / max(30, hp["defense"])) ** 2.0))
    gh, ga = poisson(lam_h, rng), poisson(lam_a, rng)
    events = []

    def add(minute, text):
        events.append((minute, text))

    for side, goals, prof, opp in (("home", gh, hp, ap), ("away", ga, ap, hp)):
        for _ in range(goals):
            minute = rng.randint(1, 70)
            scorer = rng.choices(
                prof["top"], weights=[max(1, p["attr_definicion"] + p["attr_pc_flick"]) for p in prof["top"]], k=1
            )[0]
            kind = rng.choices(["open", "pc", "stroke", "deflection"], weights=[0.60, 0.28, 0.05, 0.07], k=1)[0]
            team_name = home["name"] if side == "home" else away["name"]
            if kind == "pc":
                add(minute, f"PC para {team_name}. {scorer['jugador']} transforma con un drag flick.")
            elif kind == "stroke":
                add(minute, f"Stroke para {team_name}. {scorer['jugador']} no falla desde el punto de penalty.")
            elif kind == "deflection":
                add(minute, f"{scorer['jugador']} desvía un disparo y bate al portero. Gol de {team_name}.")
            else:
                add(minute, f"{scorer['jugador']} define dentro del área. Gol de {team_name}.")
    # add some non-goal events
    for _ in range(4):
        minute = rng.randint(1, 70)
        side = rng.choice([home, away])
        prof = hp if side is home else ap
        p = rng.choice(prof["top"])
        kind = rng.choice(["save", "pc", "card", "chance"])
        if kind == "save":
            add(minute, f"Paradón del portero rival al disparo de {p['jugador']}.")
        elif kind == "pc":
            add(minute, f"PC para {side['name']}. El saque de {p['jugador']} no encuentra rematador.")
        elif kind == "card":
            add(minute, f"Tarjeta verde para {p['jugador']} ({side['name']}).")
        else:
            add(minute, f"{p['jugador']} prueba desde el borde del círculo, pero se marcha alto.")
    events.sort(key=lambda x: x[0])
    return gh, ga, events


def circle_fixtures(teams):
    # round-robin, ida y vuelta
    n = len(teams)
    if n % 2:
        teams = teams + ["BYE"]
    rounds = []
    arr = teams[:]
    for r in range(n - 1):
        pairs = []
        for i in range(n // 2):
            a, b = arr[i], arr[n - 1 - i]
            if a != "BYE" and b != "BYE":
                pairs.append((a, b) if r % 2 == 0 else (b, a))
        rounds.append(pairs)
        arr = [arr[0]] + [arr[-1]] + arr[1:-1]
    second = [[(b, a) for a, b in rd] for rd in rounds]
    return rounds + second


def show_dossier(club, city_by_id):
    st = club["stadium"]
    fin = club["finances"]
    board = club["board"]
    log = club["logistics"]
    print(f"\n{'=' * 72}\n{club['name']}\n{'=' * 72}")
    print(f"{club['full_name']} · Fundado en {club['founded'] or '—'} · {club['city']} ({club['province']})")
    print(f"Colores: {', '.join(club['colors'])} · Apodo: {club['nickname']} · Liga: {club['league']}")
    print(f"\nHISTORIA\n{club['history']}")
    print(
        f"\nESTADIO\n{st['name']}\n{st['address']}\nSuperficie: {st['surface']} · Capacidad: {st['capacity']} ({st['capacity_confidence']})"
    )
    print(
        f"Instalaciones: {club['facilities']['pitches']} campo(s), gimnasio {'sí' if club['facilities']['gym'] else 'no'}, cantera {club['facilities']['academy']}/5"
    )
    print(f"\nJUNTA\nObjetivo: {board['expectation']}\nPresión: {board['pressure']} · Paciencia: {board['patience']}/5")
    print(
        f"Presupuesto de fichajes: {fin['transfer_budget']:,} € · Masa salarial: {fin['wage_budget']:,} €".replace(
            ",", "."
        )
    )
    print(f"\nLOGÍSTICA\nAeropuerto: {log['airport']} · Tren: {log['train']} · Modo habitual: {log['preferred_mode']}")
    print(log["notes"])


def choose_club(clubs):
    dha = [c for c in clubs if c["league"] == "DHA"]
    print("\nCLUBES DHA")
    for i, c in enumerate(dha, 1):
        print(f"{i:2}. {c['name']:36} {c['city']:24} {c['stadium']['name']}")
    while True:
        try:
            n = int(input("\nElige club (número): "))
            if 1 <= n <= len(dha):
                return dha[n - 1]
        except Exception:
            pass
        print("Número no válido.")


def run(club_name=None, auto=False, demo=False, seed=20261019):
    clubs = load_json("clubs.json")
    cities = load_json("cities.json")
    city_by_id = {c["id"]: c for c in cities}
    players = load_players()
    if demo:
        club_name = "CD TERRASSA HOCKEY"
    if club_name:
        club = next(
            (c for c in clubs if norm(c["name"]) == norm(club_name) or norm(c["full_name"]) == norm(club_name)), None
        )
        if not club:
            print("Club no encontrado:", club_name)
            return
    else:
        club = choose_club(clubs)
    show_dossier(club, city_by_id)
    if club["league"] != "DHA":
        print("\nEl prototipo solo simula DHA. Para DHB se usará el mismo motor en la siguiente fase.")
        return
    dha = [c for c in clubs if c["league"] == "DHA"]
    teams = [c["name"] for c in dha]
    profiles = {c["name"]: team_profile(c["name"], players) for c in dha}
    fixtures = circle_fixtures(teams)
    rng = random.Random(seed)
    standings = {t: {"pj": 0, "g": 0, "e": 0, "p": 0, "gf": 0, "gc": 0, "pts": 0} for t in teams}
    results = []
    print(f"\nCALENDARIO DHA: {len(fixtures)} jornadas")

    # find first match of club
    def next_match():
        for r, rd in enumerate(fixtures):
            for h, a in rd:
                if club["name"] in (h, a) and not any(x["home"] == h and x["away"] == a for x in results):
                    return r, h, a
        return None

    if auto or demo:
        for r, rd in enumerate(fixtures):
            for h, a in rd:
                gh, ga, ev = sim_match(
                    next(c for c in dha if c["name"] == h),
                    next(c for c in dha if c["name"] == a),
                    profiles[h],
                    profiles[a],
                    rng,
                )
                results.append({"round": r + 1, "home": h, "away": a, "gh": gh, "ga": ga, "events": ev})
                for t, gf, gc in ((h, gh, ga), (a, ga, gh)):
                    s = standings[t]
                    s["pj"] += 1
                    s["gf"] += gf
                    s["gc"] += gc
                    if gf > gc:
                        s["g"] += 1
                        s["pts"] += 3
                    elif gf == gc:
                        s["e"] += 1
                        s["pts"] += 1
                    else:
                        s["p"] += 1
            # print club's match if it played
            for h, a in rd:
                if club["name"] in (h, a):
                    res = [x for x in results if x["home"] == h and x["away"] == a][-1]
                    print(f"\nJ{res['round']}: {h} {res['gh']}-{res['ga']} {a}")
                    for minute, text in res["events"][:8]:
                        print(f"  {minute:>2}' {text}")
                    break
            if demo and r >= 2:
                break
        print_standings(standings)
        return
    nm = next_match()
    if not nm:
        print("No hay más partidos.")
        return
    r, h, a = nm
    home = next(c for c in dha if c["name"] == h)
    away = next(c for c in dha if c["name"] == a)
    # logistics for club if away
    if club["name"] == a:
        tp = travel_plan(club, home, city_by_id)
        print(f"\nLOGÍSTICA: {h} vs {a}")
        print(f"  Distancia: {tp['distance_km']} km · Modo: {tp['mode']} · {tp['hours']} h")
        print(f"  Coste estimado: {tp['cost']:,} € · Fatiga: {tp['fatigue']} · {tp['notes']}".replace(",", "."))
    gh, ga, ev = sim_match(home, away, profiles[h], profiles[a], rng, detailed=True)
    print(f"\nJ{r + 1}: {h} {gh}-{ga} {a}")
    for minute, text in ev:
        print(f"  {minute:>2}' {text}")
    for t, gf, gc in ((h, gh, ga), (a, ga, gh)):
        s = standings[t]
        s["pj"] += 1
        s["gf"] += gf
        s["gc"] += gc
        if gf > gc:
            s["g"] += 1
            s["pts"] += 3
        elif gf == gc:
            s["e"] += 1
            s["pts"] += 1
        else:
            s["p"] += 1
    print_standings(standings)


def print_standings(standings):
    print(f"\n{'=' * 72}\nCLASIFICACIÓN\n{'=' * 72}")
    rows = sorted(standings.items(), key=lambda kv: (-kv[1]["pts"], -(kv[1]["gf"] - kv[1]["gc"]), -kv[1]["gf"]))
    print(f"{'#':>2} {'Equipo':36} {'PJ':>3} {'G':>3} {'E':>3} {'P':>3} {'GF':>3} {'GC':>3} {'PTS':>4}")
    for i, (t, s) in enumerate(rows, 1):
        print(f"{i:>2} {t:36} {s['pj']:>3} {s['g']:>3} {s['e']:>3} {s['p']:>3} {s['gf']:>3} {s['gc']:>3} {s['pts']:>4}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--club")
    ap.add_argument("--auto", action="store_true")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--seed", type=int, default=20261019)
    args = ap.parse_args()
    run(args.club, args.auto, args.demo, args.seed)
