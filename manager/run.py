#!/usr/bin/env python3
"""Lanzador del Hockey Manager desde manager/."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.main import main

if __name__ == "__main__":
    raise SystemExit(main())
