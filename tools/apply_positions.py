#!/usr/bin/env python3
"""Aplica posiciones nuevas al manifiesto de jugadores.

Entrada: tools/new_positions.csv con columnas:
  equipo,jugador,posicion,subposicion,fuente,url,fecha,confianza,nota

Salida: tools/todos_manifest_positions.csv actualizado + backup.
No regenera atributos, juego ni Excel: ejecutar el pipeline después.
"""

import csv
import re
import shutil
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
MANIFEST = TOOLS / "todos_manifest_positions.csv"
NEW = TOOLS / "new_positions.csv"
BACKUP = TOOLS / "todos_manifest_positions_backup.csv"

POS_MAP = {
    "portero": "Portero",
    "arquero": "Portero",
    "goalkeeper": "Portero",
    "gk": "Portero",
    "defensa central": "Defensa central",
    "central": "Defensa central",
    "centre back": "Defensa central",
    "defensa lateral": "Defensa lateral",
    "lateral": "Defensa lateral",
    "lateral derecho": "Defensa lateral",
    "lateral izquierdo": "Defensa lateral",
    "right back": "Defensa lateral",
    "left back": "Defensa lateral",
    "defensa": "Defensa",
    "defender": "Defensa",
    "back": "Defensa",
    "medio": "Medio",
    "centrocampista": "Medio",
    "midfielder": "Medio",
    "medio centro": "Medio",
    "medio defensivo": "Medio",
    "medio ofensivo": "Medio",
    "interior": "Medio",
    "delantero": "Delantero",
    "atacante": "Delantero",
    "forward": "Delantero",
    "extremo": "Delantero",
    "winger": "Delantero",
    "delantero centro": "Delantero",
    "medio/delantero": "Medio/Delantero",
    "delantero/medio": "Medio/Delantero",
    "defensa/medio": "Defensa/Medio",
    "medio/defensa": "Defensa/Medio",
}


def norm(s):
    s = str(s or "").strip().upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^A-Z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def pos_norm(p):
    k = norm(p).lower()
    return POS_MAP.get(k, p.strip() if p.strip() else "Defensa")


def main():
    if not NEW.exists():
        raise SystemExit(f"No existe {NEW}. Crea el CSV de posiciones nuevas primero.")
    dry = "--dry-run" in sys.argv
    rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8-sig")))
    new = list(csv.DictReader(NEW.open(encoding="utf-8-sig")))
    print(f"Manifiesto: {len(rows)} filas. Nuevas posiciones: {len(new)} filas.")
    # índice por equipo + nombre normalizado
    index = {}
    for r in rows:
        index.setdefault((norm(r["equipo"]), norm(r["jugador"])), []).append(r)
    applied = 0
    unmatched = []
    for n in new:
        team = norm(n["equipo"])
        name = norm(n["jugador"])
        matches = index.get((team, name), [])
        if not matches:
            # fuzzy dentro del equipo
            candidates = [(k, v) for k, v in index.items() if k[0] == team]
            best = None
            best_score = 0
            for (t, p), v in candidates:
                score = SequenceMatcher(None, name, p).ratio()
                if score > best_score:
                    best_score = score
                    best = (t, p, v)
            if best and best_score >= 0.90:
                matches = best[2]
            else:
                unmatched.append((n, best_score))
                continue
        # preferir Jugador
        matches = sorted(matches, key=lambda r: 0 if r["perfil"] == "Jugador" else 1)
        r = matches[0]
        pos = pos_norm(n["posicion"])
        # Si la fuente dice defensa central/lateral, conservar el matiz.
        sub = n.get("subposicion", "").strip()
        if sub and pos == "Defensa":
            pos = "Defensa " + sub.lower()
        r["pos"] = pos
        r["src"] = n["fuente"].strip() or r.get("src", "Estimada")
        r["conf"] = n["confianza"].strip() or r.get("conf", "Media")
        r["pos_url"] = n.get("url", "").strip()
        r["pos_fecha"] = n.get("fecha", "").strip()
        r["pos_nota"] = n.get("nota", "").strip()
        applied += 1
    if dry:
        print("DRY RUN: no se escribe el manifiesto.")
        print(f"Aplicadas (simuladas): {applied}. Sin coincidencia: {len(unmatched)}.")
        for n, score in unmatched[:40]:
            print(f"  NO MATCH: {n['equipo']} | {n['jugador']} | {n['posicion']} | score={score:.2f}")
        return
    shutil.copy2(MANIFEST, BACKUP)
    # escribir con las columnas originales + nuevas si no existen
    fieldnames = list(rows[0].keys())
    for extra in ["pos_url", "pos_fecha", "pos_nota"]:
        if extra not in fieldnames:
            fieldnames.append(extra)
    with MANIFEST.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})
    print(f"Aplicadas: {applied}. Sin coincidencia: {len(unmatched)}.")
    for n, score in unmatched[:40]:
        print(f"  NO MATCH: {n['equipo']} | {n['jugador']} | {n['posicion']} | score={score:.2f}")
    print(f"Backup: {BACKUP}")
    print(
        "Ahora ejecuta: python3 build_attributes_v2.py && python3 generate_game.py && python3 build_excel_attributes.py"
    )


if __name__ == "__main__":
    main()
