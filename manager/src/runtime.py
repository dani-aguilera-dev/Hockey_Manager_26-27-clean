"""Rutas compartidas entre ejecución normal y ejecutable empaquetado."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def project_root() -> Path:
    """Devuelve la raíz del proyecto o el directorio extraído por PyInstaller."""
    env_root = os.environ.get("HOCKEY_ROOT")
    if env_root:
        return Path(env_root).resolve()
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parents[2]
