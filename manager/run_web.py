#!/usr/bin/env python3
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from web.app import app

if __name__ == "__main__":
    host = os.environ.get("HOCKEY_HOST", "127.0.0.1")
    port = int(os.environ.get("HOCKEY_PORT", os.environ.get("PORT", "5000")))
    app.run(host=host, port=port, debug=False, threaded=True, use_reloader=False)
