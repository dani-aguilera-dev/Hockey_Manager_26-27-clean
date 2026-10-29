#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v pyinstaller >/dev/null 2>&1; then
  echo "Instala PyInstaller: python3 -m pip install pyinstaller"
  exit 1
fi

rm -rf build dist HockeyManager.spec
pyinstaller \
  --noconfirm \
  --clean \
  --onefile \
  --windowed \
  --name HockeyManager \
  --icon assets/logo.png \
  --paths . \
  --add-data "web:manager/web" \
  --add-data "data:manager/data" \
  --add-data "src:manager/src" \
  --add-data "../jugadores:jugadores" \
  --add-data "../tools/player_attributes_v2.csv:tools" \
  desktop.py

echo
echo "Ejecutable: $(pwd)/dist/HockeyManager"
echo "Para abrirlo: doble clic en HockeyManager.desktop o en dist/HockeyManager"
