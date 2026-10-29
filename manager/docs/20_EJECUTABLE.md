# Ejecutable de escritorio

**Estado:** generado y probado (2026-10-21).

## 1. Ejecutar

Doble clic en:

```text
/home/daniel/hockey_espana/manager/dist/HockeyManager
```

o en el acceso directo:

```text
/home/daniel/Escritorio/HockeyManager.desktop
```

El lanzador abre el navegador en `http://127.0.0.1:5000`.

## 2. Logo

- `manager/assets/logo.svg`
- `manager/assets/logo.png`
- `manager/assets/logo.ico`
- `manager/web/static/logo.png`

El `.desktop` usa `assets/logo.png` como icono.

## 3. Datos y guardado

El ejecutable es autocontenido: incluye plantillas, datos, escudos y las 976 fotos de jugadores.

La base de datos se guarda fuera del binario, en:

```text
~/.local/share/hockey-manager/web.db
```

Así el ejecutable puede actualizarse sin perder partidas.

Log del lanzador:

```text
~/.local/share/hockey-manager/launcher.log
```

## 4. Cerrar

Desde el menú de juego:

```text
Menú → Aplicación → Cerrar Hockey Manager
```

También se puede cerrar desde el menú principal si no hay partida abierta.

## 5. Reconstruir

```bash
cd /home/daniel/hockey_espana/manager
./build_desktop.sh
```

Requiere PyInstaller. El resultado queda en `manager/dist/HockeyManager`.

El binario ocupa unos 222 MB porque incluye las fotos y los escudos. No debe subirse a GitHub; el repositorio solo guarda el script y los recursos fuente.

## 6. Acceso directo

El archivo de escritorio está en:

```text
manager/HockeyManager.desktop
```

y se copió a:

```text
/home/daniel/Escritorio/HockeyManager.desktop
```

Si el escritorio pide permiso, elige **Permitir lanzar** o marca el archivo como ejecutable.
