#!/usr/bin/env python3
"""Lanzador de escritorio de Hockey Manager.

Abre el servidor local y el navegador. En el ejecutable empaquetado guarda la
base de datos en el directorio de datos del usuario, no dentro del binario.
"""

from __future__ import annotations

import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path


def app_data_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
        return base / "HockeyManager"
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/HockeyManager"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "hockey-manager"


def main() -> None:
    frozen = bool(getattr(sys, "frozen", False))
    root = (
        Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
        if frozen
        else Path(__file__).resolve().parents[1]
    )
    manager = root / "manager"
    sys.path.insert(0, str(manager))
    os.environ.setdefault("HOCKEY_ROOT", str(root))
    os.environ["HOCKEY_DESKTOP"] = "1"
    data_dir = app_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HOCKEY_WEB_DB", str(data_dir / "web.db"))

    log_path = data_dir / "launcher.log"
    import logging

    logging.basicConfig(
        filename=str(log_path),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    def port_open(port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.settimeout(0.4)
            return probe.connect_ex(("127.0.0.1", port)) == 0

    port = int(os.environ.get("HOCKEY_PORT", "5000"))
    if port_open(port):
        webbrowser.open(f"http://127.0.0.1:{port}")
        return

    try:
        from web.app import app
    except Exception:
        logging.exception("No se pudo importar la aplicación")
        raise

    def run_server() -> None:
        try:
            app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False, threaded=True)
        except Exception:
            logging.exception("El servidor se detuvo")

    thread = threading.Thread(target=run_server, name="hockey-manager-server", daemon=True)
    thread.start()
    for _ in range(50):
        if port_open(port):
            break
        time.sleep(0.2)
    if os.environ.get("HOCKEY_NO_BROWSER") != "1":
        webbrowser.open(f"http://127.0.0.1:{port}")
    while thread.is_alive():
        time.sleep(1)


if __name__ == "__main__":
    main()
