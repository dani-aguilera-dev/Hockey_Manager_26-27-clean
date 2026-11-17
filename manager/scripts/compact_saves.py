#!/usr/bin/env python3
"""Comprime saves antiguos y compacta SQLite."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.persistence import DEFAULT_DB, compact_saves


def main() -> None:
    parser = argparse.ArgumentParser(description="Comprime y compacta los saves.")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Ruta de la base de datos.")
    args = parser.parse_args()
    report = compact_saves(args.db)
    print(
        f"Convertidas: {report['converted']} · "
        f"antes: {report['bytes_before'] / 1024 / 1024:.1f} MB · "
        f"después: {report['bytes_after'] / 1024 / 1024:.1f} MB"
    )


if __name__ == "__main__":
    main()
