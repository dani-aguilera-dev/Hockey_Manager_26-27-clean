#!/usr/bin/env python3
"""Limpia partidas antiguas de la base de datos SQLite.

Uso:
    python3 scripts/prune_saves.py --keep 50
    python3 scripts/prune_saves.py --keep 50 --apply
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.persistence import DEFAULT_DB, list_saves, prune_saves


def main() -> None:
    parser = argparse.ArgumentParser(description="Conserva las N partidas más recientes.")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Ruta de la base de datos.")
    parser.add_argument("--keep", type=int, default=50, help="Partidas que se conservan.")
    parser.add_argument("--apply", action="store_true", help="Ejecuta la limpieza; sin esto solo muestra el plan.")
    args = parser.parse_args()
    saves = list_saves(args.db)
    print(f"Partidas actuales: {len(saves)} · se conservarán: {min(args.keep, len(saves))}")
    if not args.apply:
        print("Modo simulación. Añade --apply para borrar las antiguas.")
        return
    report = prune_saves(args.db, args.keep)
    print(f"Borradas: {report['deleted']} · conservadas: {report['kept']}")


if __name__ == "__main__":
    main()
