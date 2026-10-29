#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/web/frontend"

if ! command -v npm >/dev/null 2>&1; then
  echo "Instala Node.js 20+ y npm para compilar la interfaz React."
  exit 1
fi

npm install
npm run build

echo
echo "Interfaz React compilada en manager/web/static/react"
echo "Arranca el juego con: python3 run_web.py"
