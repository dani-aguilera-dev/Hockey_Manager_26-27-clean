# Interfaz web React

La interfaz pública del juego es una SPA React servida por Flask en `/app`.
Flask sigue siendo la fuente de verdad: conserva el estado de la partida, las
reglas de `manager/src`, SQLite y el motor de partido. React solo consume la API
JSON y presenta la experiencia visual.

## Arranque

```bash
cd /home/daniel/hockey_espana/manager
./build_web.sh          # npm install + vite build
python3 run_web.py      # Flask en http://127.0.0.1:5000
```

Abre `http://127.0.0.1:5000/app`.

En desarrollo:

```bash
cd web/frontend
npm run dev
```

Vite proxifica `/api`, `/static/crests` y `/photo` contra Flask en el puerto
5000. La SPA usa `basename="/app"`.

## Estructura

```text
web/
  api.py                 API JSON: estado, acciones, mercado, partido, prensa...
  app.py                 Flask, persistencia y rutas legacy compatibles
  frontend/
    src/
      App.tsx            Rutas React
      components/        Shell, componentes UI y pizarra
      context/           Estado de partida y toasts
      lib/               Cliente API y formato
      pages/             Dashboard, plantilla, táctica, mercado, partido...
      styles.css         Tokens y sistema visual
    vite.config.ts       Build a web/static/react
  static/react/          Build servido por Flask
```

## Rutas React

- `/app/` — menú principal.
- `/app/new` — nueva partida.
- `/app/load` — cargar partida.
- `/app/game` — Club HQ / dashboard.
- `/app/game/squad`, `/app/game/player/:id`, `/app/game/team/:id`.
- `/app/game/tactics`, `/app/game/training`.
- `/app/game/market`, `/app/game/market/player/:id`, `/app/game/market/offers`, `/app/game/market/renew`.
- `/app/game/staff`, `/app/game/youth`, `/app/game/press`.
- `/app/game/table`, `/app/game/cup`, `/app/game/ehl`.
- `/app/game/match`, `/app/game/live`, `/app/game/report`.
- `/app/game/news`, `/app/game/chat`, `/app/game/season-end`.
- `/app/game/options`, `/app/options`.

Las rutas antiguas de Flask (`/dashboard`, `/squad`, etc.) siguen existiendo
para compatibilidad y tests del backend. Si un navegador las solicita con
`Accept: text/html`, se redirigen a su equivalente React.

## API

Todas las respuestas usan:

```json
{ "ok": true, "data": {}, "message": "opcional" }
```

o:

```json
{ "ok": false, "error": "Mensaje", "code": "codigo" }
```

Endpoints principales:

- `GET /api/menu`, `GET /api/new-game`, `POST /api/new-game`, `GET/POST /api/load`.
- `GET /api/state`, `POST /api/save`, `POST /api/exit`, `POST /api/simulate`.
- `GET /api/squad`, `/api/player/:id`, `/api/team/:id`.
- `GET/POST /api/tactics`, `/api/training`, `/api/press`.
- `GET /api/market`, `POST /api/market/offer/:id`, ofertas y renovaciones.
- `GET /api/staff`, candidatos, contratación y despido.
- `GET /api/youth`, promoción y liberación.
- `GET /api/table`, `/api/cup`, `/api/ehl`.
- `GET /api/match`, `POST /api/match/quick`, `POST /api/match/live/start`,
  `GET /api/match/live`, avance, táctica, cambios y final.
- `GET /api/news`, `/api/chat`, acciones de conversación.
- `GET /api/season/end`, `POST /api/season/continue`.

## Sistema visual

Tokens en `src/styles.css`:

- Fondo `#0B1220`, superficies `#121D31` / `#17243B`, borde `#263650`.
- Texto `#E8EEF8`, secundario `#A4B6D2`.
- Acción `#FFB020`; información `#5AA9FF`; éxito `#43D17C`; peligro `#FF6B6B`.
- Tipografía Inter, escala 52/40/32/20/14/10.
- Shell de 224 px + topbar de 64 px; responsive con bottom navigation a 900 px.
- Componentes compartidos: botón, badge, card, tabla, avatar, escudo, pizarra,
  progreso, modal, tabs y toasts.

## Estado de la migración

La interfaz pública ya es React. Los templates Jinja antiguos se conservan como
referencia y compatibilidad, pero no son la ruta principal. El ejecutable de
escritorio no se actualiza desde este cambio: la distribución recomendada es la
web.

Pendiente de una siguiente iteración:

- empaquetado de producción con Gunicorn/Postgres y autenticación;
- descarga de assets oficiales de federaciones con permiso de uso;
- auditoría de accesibilidad con lector de pantalla;
- tests E2E automatizados en CI.
