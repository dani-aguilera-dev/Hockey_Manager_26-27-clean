# Ligas internacionales (primera fase)

**Estado:** implementado (2026-10-22).

## 1. Qué se puede jugar ya

Además de DHA, DHB y 1ª Andaluza (no simulada), la pantalla de nueva partida
permite elegir clubes de seis competiciones:

| Código | Competición | País | Equipos | Jornadas |
|---|---|---|---:|---:|
| `NED` | Tulp Hoofdklasse Heren | Países Bajos | 12 | 22 |
| `BEL` | Men's Belgian Hockey League | Bélgica | 12 | 22 |
| `GER` | 1. Feldhockey Bundesliga Herren | Alemania | 12 | 22 |
| `ENG` | England Hockey Premier Division | Inglaterra | 12 | 22 |
| `ARG` | Torneo Metropolitano Masculino | Argentina | 14 | 26 |
| `IND` | Hockey India League | India | 8 | 14 |

Todas usan liga regular a doble vuelta. Los play-offs, el formato de dos fases
alemán y el calendario corto de la HIL se implementarán en la siguiente fase;
de momento el campeón es el primero de la tabla.

## 2. Niveles y estrellas

El `overall` sigue siendo absoluto. Las estrellas son relativas a la liga:

| Liga | Nivel de referencia |
|---|---:|
| EHL | 86 |
| Hoofdklasse | 84 |
| Belgian League | 82 |
| Bundesliga | 81 |
| Premier Division | 79 |
| Metropolitano | 77 |
| Hockey India League | 76 |
| DHA | 74,8 |

Esto permite que un jugador de 80 sea una estrella en la India y un jugador
importante, pero no excepcional, en la Hoofdklasse.

## 3. Datos de esta fase

- Clubes, ciudades, estadios y expectativas: datos reales de referencia.
- Plantillas reales: **Países Bajos, Bélgica, Alemania, Inglaterra, Argentina e India**.
- Fotos: locales para NED, BEL, GER e IND; avatares en ENG y ARG.
- Escudos: oficiales para las seis ligas.
- Staff: entrenador y cuerpo técnico generados.
- Posiciones: publicadas por NED/BEL/GER/IND; estimadas en ENG y ARG a partir de la convocatoria oficial, con porteros confirmados cuando el acta los identifica.
- Moneda: todos los presupuestos se muestran en euros para evitar tipos de
  cambio inconsistentes en el MVP.

La UI marca estas ligas como internacionales y mantiene las plantillas
reales separadas de los datos de iSquad.

## 4. Fuentes oficiales previstas para el importador

Estas son las fuentes usadas para las plantillas reales. La prioridad es
siempre la API o el HTML oficial; Flashscore, Sofascore y agregadores similares
no se usan como fuente principal por sus condiciones de uso y su fragilidad.

| País | Fuente principal | Datos esperables | Dificultad |
|---|---|---|---|
| Países Bajos | `hockey.nl` y su Match Center (KNHB) | calendario, resultados, clasificación, equipos | media: aplicación Nuxt con datos dinámicos |
| Bélgica | `carlsberg00hockeyleague.be` (RBHA) | ranking, jornadas, resultados | baja-media: tablas HTML |
| Alemania | `hockey.de`, `hockeybundesliga.de` y servicios de resultados regionales | tabla, jornadas, actas | media-alta: datos repartidos por federaciones regionales |
| Inglaterra | `englandhockey.co.uk` y API GMS | tabla, calendario, resultados, clubes, plantillas | baja-media: API JSON con clave pública |
| Argentina | `buenosaireshockey.ar` y API TournamentTracker | agenda, resultados, planillas, clubes | media: API cifrada y planillas PDF |
| India | `hockeyindialeague.com` | franquicias, calendario, estadísticas | media: liga corta y plantillas por temporada |

Fuentes complementarias:

- **FIH TMS / Altius RT** (`tms.fih.ch`) para competiciones internacionales,
  selecciones y datos de contexto.
- **EHL** (`ehlhockey.org` / `eurohockey.org`) para calibrar el nivel europeo
  y construir la clasificación continental.
- **Wikipedia/Wikidata** para metadatos de clubes, ciudades y historial; no
  para resultados en directo.
- **Webs de clubes** para plantillas, fotos y escudos, siempre revisando
  licencia y condiciones.

## 5. Estrategia de scraping recomendada

No se debe scrapear en tiempo de ejecución del juego. El ejecutable debe ser
autocontenido. El flujo correcto es:

1. Un proceso externo de ingestión descarga una instantánea.
2. Se guarda el HTML/JSON original para auditoría.
3. Un adaptador normaliza clubes, jugadores, partidos y clasificaciones.
4. Se generan los JSON/SQLite que viajan con el juego.
5. El juego solo lee datos locales.

Cada fuente debe tener su propio adaptador con este contrato lógico:

```text
competiciones()
equipos()
plantillas()
calendario()
resultados()
clasificacion()
estadisticas()
```

Reglas técnicas:

- Respetar `robots.txt`, términos de uso y límites de peticiones.
- Identificar el cliente con un `User-Agent` claro y un contacto.
- Cachear y no repetir descargas.
- Preferir JSON/API oficial; usar Playwright solo cuando el HTML dependa de
  JavaScript y esté permitido.
- Validar esquemas, detectar duplicados y conservar la fecha de captura.
- Resolver identidades de jugadores con nombre, fecha de nacimiento, club y
  nacionalidad; nunca fusionar solo por nombre.
- No usar datos personales sensibles ni fotos sin licencia.

## 6. Qué falta para completar el salto internacional

### Fase 2A · Datos reales

- Importadores de las seis ligas: completados.
- Plantillas reales en NED, BEL, GER, ENG, ARG e IND.
- Escudos oficiales en las seis ligas.
- Pendiente: fotos locales de ENG/ARG, contratos, salarios y monedas locales.

### Fase 2B · Formatos

- Play-offs de Bélgica, Alemania, Inglaterra y Países Bajos.
- Fase de grupos y play-downs alemanes.
- Formato corto y franquicias de la HIL.
- Playoffs del Metropolitano argentino.
- Ascensos y descensos nacionales.

### Fase 2C · Mundo

- Selecciones nacionales y FIH Pro League.
- Clasificación EHL por país y campeones continentales.
- Copa de Europa, Pan American Club Championship y competiciones asiáticas.
- Mercado internacional con divisas, visados y límites de extranjeros.
- Scouting por país y calendarios de temporada cruzados.

## 7. Archivos

```text
manager/src/competitions.py       registro de competiciones
manager/src/international.py      carga y generación de ligas
manager/data/international.json   clubes, ciudades y metadatos
manager/src/ratings.py            niveles y estrellas por liga
manager/src/season.py             calendario y cierre de temporada
manager/web/app.py                selección de club y escudos de respaldo
manager/web/templates/new_game.html
manager/src/tests/test_international.py
```

## 8. Pruebas

- Las seis ligas crean su calendario y son jugables.
- El mercado incluye jugadores de la liga seleccionada.
- La persistencia conserva país y competición.
- La temporada internacional termina y permite avanzar a la siguiente.
- Los 70 clubes internacionales tienen plantilla, estadio y staff.
- Los tests españoles siguen pasando.

Resultado actual: **149 tests superados** en la suite completa del proyecto.
