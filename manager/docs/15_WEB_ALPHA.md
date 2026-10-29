# Alpha web local

**Estado:** primera versión funcional (2026-10-21).

La alpha web es una capa Flask + Jinja sobre el motor existente. No reescribe la lógica: usa `GameState`, `MatchEngine`, mercado, entrenamiento, Copa, EHL, cantera y persistencia.

Para la investigación de color, usabilidad, escudos y componentes, ver [`16_DISENO_UI.md`](16_DISENO_UI.md).

---

## 1. Arrancar

```bash
cd /home/daniel/hockey_espana/manager
python3 run_web.py
```

Abrir:

```text
http://127.0.0.1:5000
```

También se puede usar otra base de datos:

```bash
HOCKEY_WEB_DB=/ruta/web.db python3 run_web.py
```

---

## 2. Qué incluye

- Nueva partida con club DHA o DHB.
- Carga y guardado de partidas en SQLite, con nombre de guardado amigable y menú de juego.
- **Simulación diaria** con avance de 1 día, hasta una fecha o hasta el próximo partido, incluyendo Copa del Rey y EHL.
- **Diario del club** con entrenamientos, lesiones, mercado, noticias de DHA/DHB y conversaciones.
- **Vestuario** con chat y respuestas que afectan a moral, forma o cohesión.
- **Mercado abierto por fechas** (verano hasta el 30/09 e invierno en enero) y listado visible incluso cerrado.
- **Perfiles de equipo** con once probable, banquillo con fotos reales e histórico de jugadores.
- **Estrellas relativas por categoría**: el mismo overall vale distinto en DHA, DHB o 1ª Andaluza.
- **Menú de juego global** en todas las pantallas: continuar, guardar, cargar, volver, menú principal, nueva partida y salida con guardado automático.
- **Opciones**: tamaño de texto normal/grande, modo compacto y confirmación al salir.
- **Menú principal** con partida en curso, guardado rápido y partidas recientes.
- Dashboard con ticker de última hora, próximo partido, clasificación, caja, entrenamiento, Copa e inbox.
- **Escudos oficiales de club** descargados de iSquad en `web/static/crests/` (29/29), con SVG estilizado como respaldo.
- **Noticias generadas** desde el estado: previa, resultado, liga, mercado, enfermería, cantera, scouting, afición, junta y Copa.
- **Fotos de los jugadores** servidas desde `jugadores/` con fallback a avatar.
- Plantilla en fichas por posición, con foto, posición y arquetipo destacados.
- Ficha de jugador con foto grande, badges y barras de atributos.
- Táctica y once: pizarrón de slots con foto, posición, arquetipo, OVR y selector por puesto.
- Mercado en fichas de jugador con foto, club, posición, arquetipo y escudo del propietario.
- Entrenamiento semanal: automático, recuperación o plan editado.
- Mercado: búsqueda por jugador/club/posición/valor, agentes libres, ofertas, ofertas recibidas y renovaciones; siempre muestra jugadores del resto de clubes.
- Staff: contratar y despedir; junta directiva.
- Cantera: categorías Sub-16, Sub-18 y Sub-21; promover y liberar juveniles.
- Prensa.
- Copa del Rey de 8 equipos DHA integrada en el calendario diario (simulación rápida).
- EHL con fechas propias y resolución automática.
- Clasificación y calendario con acceso al perfil de cada equipo.
- Partido rápido.
- Partido en directo: marcador con escudos, cuartos, momento a momento, estadísticas, cambios y táctica.
- Fin de temporada y multi-temporada.

---

## 3. Estructura

```text
manager/
  web/
    app.py
    templates/
    static/style.css
    static/app.js
    static/crests/*.svg
    static/avatar.svg
  src/news.py
  run_web.py
```

- `app.py` mantiene `GameState` en memoria por sesión y guarda en SQLite.
- Las plantillas son HTML server-rendered.
- El partido en directo vive en memoria mientras se juega.
- Al terminar el partido se actualiza el estado y se guarda.

---

## 4. Persistencia

- Base por defecto: `manager/saves/web.db`.
- Cada partida se guarda como un blob JSON dentro de SQLite.
- El nombre de guardado se puede cambiar desde la barra superior.
- La alpha no guarda en mitad de un partido: si se reinicia el servidor, ese partido en directo se pierde.

---

## 5. Limitaciones

- Es una alpha local, sin login ni multiusuario.
- No hay guardado en mitad del partido.
- El partido en directo no tiene animación; es texto y tablas.
- Algunas pantallas son más simples que la CLI.
- El servidor de desarrollo de Flask no debe exponerse a Internet.
- La DHB no desciende a 1ª Andaluza porque esa liga no se simula.

---

## 6. Pruebas

```bash
cd manager
python3 -m pytest src/tests -q
```

Incluye pruebas de rutas web, nueva partida, fotos, escudos, noticias, entrenamiento, partido rápido, partido en directo y guardado/carga.

Resultado actual: **80 tests superados**.
