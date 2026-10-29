# Matriz de aceptación FM24 / FIH · Beta avanzada

Esta matriz convierte el objetivo amplio en criterios verificables. No afirma que el juego sea una réplica completa de Football Manager 24; define qué está cubierto por la beta y qué queda fuera.

## 1. Gestión y calendario

| Criterio | Implementación | Evidencia | Estado |
| --- | --- | --- | --- |
| Calendario oficial | `Calendar.tsx`, `/api/calendar`, `state.fixtures` | `test_dha_calendar_structure_is_complete` | PASS |
| Vista mensual | Rejilla de 42 celdas, navegación de mes y eventos oficiales/amistosos | E2E `calendar` + `monthNavigation` | PASS |
| Amistosos | `friendlies.py`, fechas libres, local/visitante, jugar/cancelar | `test_friendlies_are_scheduled_and_do_not_touch_league_table` | PASS |
| Amistosos sin puntos | `play_friendly` no llama a `recompute_table` | Test de tabla antes/después | PASS |
| Calendario global | `league_fixtures` de DHA, DHB, regionales e internacionales | `test_competition_catalog_and_world_calendar` | PASS |
| Competiciones declaradas | `competitions.json` y `league_rules.json` | `test_spanish_competition_boundaries_are_declared` | PASS |

## 2. Plantillas y datos

| Criterio | Implementación | Evidencia | Estado |
| --- | --- | --- | --- |
| Staff no jugador | `STAFF_PROFILES` en `data_loader.py` | `test_staff_are_not_loaded_as_players` | PASS |
| Sin mujeres del staff como jugadoras | Filtro de perfiles y migración de partidas antiguas | Test anterior | PASS |
| Editar jugadores | `/api/player/<id>/edit` y modal en `Player.tsx` | `test_player_editor_can_fix_position_and_attributes` | PASS |
| Clubes españoles con fuente | 29/29 `source_url` y `description_verified` | `test_clubs_have_verified_location_and_description` | PASS |
| Clubes internacionales con fuente | 70/70 `source_url`, historia específica mínima 171 caracteres | Test anterior | PASS |
| Giner de los Ríos | Valencia, 1993, Campanar, Beteró | Test y `docs/46_AUDITORIA_CLUBES.md` | PASS |

## 3. Prensa y comunicación

| Criterio | Implementación | Evidencia | Estado |
| --- | --- | --- | --- |
| Prensa previa con medios | Periodista, outlet, seis temas, confianza mediática | `test_press_has_journalist_media_and_six_topics` | PASS |
| Prensa posterior | `/api/press/post`, `PostPress.tsx`, cuatro preguntas | E2E `postPress` | PASS |
| Efectos en vestuario/junta/afición | `answer_press` y `answer_post_press` | Tests de API y E2E | PASS |
| Historial con medio y periodista | `press_history` enriquecido | API state | PASS |

## 4. Marcas y negocio

| Criterio | Implementación | Evidencia | Estado |
| --- | --- | --- | --- |
| Marcas reales de hockey | `brands.json`: Osaka, Ritual, Gryphon, Grays, TK, Mercian, STX, Adidas, Kookaburra, JDH, Malik, Dita, Voodoo, Byte, Princess, Harrow, OBO, Fat Pipe, Monkey, Tempest, Rage | `test_brand_offers_and_equipment_bonus` | PASS |
| Contrato de equipación del club | `/api/brands/<id>`, `equipment_bonus` aplicado en partido | Test de bonus | PASS |
| Contrato individual de imagen | `/api/brands/players/<id>`, `PlayerState.brand_deal`, `Commercial.tsx` | `test_player_brand_contract_is_individual` + E2E `playerBrands` | PASS |
| Ingresos y marca | Prima, anualidad, presupuesto y `brand_rating` | Tests y API | PASS |

## 5. Reglas FIH

| Regla | Constante / comportamiento | Evidencia | Estado |
| --- | --- | --- | --- |
| Cuatro cuartos de 15 minutos | `QUARTERS=4`, `QUARTER_MINUTES=15` | `test_fih_match_structure_and_discipline` | PASS |
| Once jugadores | `PLAYERS_ON_FIELD=11` | Test | PASS |
| Cinco suplentes | `MAX_SUBSTITUTES=5` | Test | PASS |
| Verde: 2 minutos | `GREEN_CARD_MINUTES=2` | Test | PASS |
| Amarilla: 5 o 10 minutos | `suspension_minutes("yellow", serious)` | Test | PASS |
| Roja: resto del partido + sanción | `next_match_suspension("red") == 1` | Test | PASS |
| Escalada de tarjetas | `next_card_for_player` | Test | PASS |
| PC, strokes y shootout | Motor existente y pruebas de partido | Suite de tests | PASS |

## 6. Simulación 3D conectada a MatchEngine

| Criterio | Implementación | Evidencia | Estado |
| --- | --- | --- | --- |
| Campo 3D | `MatchViewer3D.tsx` con Three.js: césped, líneas, círculo, áreas y porterías | E2E `viewer3d` + captura `e2e_3d.png` | PASS |
| 22 jugadores con locomoción | 11 locales y 11 visitantes, piernas/brazos animados, desplazamiento y separación | E2E `players=22`, `frames=60` | PASS |
| Balón con física | Velocidad, gravedad, rebote, fricción, límites y detección de gol | E2E `ballSpeed=9.04` | PASS |
| Colisiones | Colisión jugador-jugador y jugador-balón con separación y rebote | E2E `collisions=55` | PASS |
| UI 3D | Marcador, cuarto, minuto, estado y último evento superpuestos al canvas | E2E `match-viewer-ui` + captura | PASS |
| Conexión con MatchEngine | El visor consume `LivePayload`: `score`, `quarter`, `minute`, `line`, `events`, formación y equipo atacante | `/api/match/live` y `/api/match/live/advance` | PASS |
| Física 3D de alta fidelidad | No hay colisiones de stick/cuerpo completas, tejido, IK ni física de material | Matriz lo declara fuera de alcance | FAIL / fuera de alcance |

## 7. Reglas FIH avanzadas y arbitraje

| Criterio | Prueba | Estado |
| --- | --- | --- |
| PC: inyección, parada, flick/desvío, portero y rebote | `test_penalty_corner_stroke_and_referee_are_exposed`; stats `pc`, `pc_goals` y eventos `pc` | PASS |
| Stroke: lanzador, portero, gol/parada/fallo | `test_penalty_corner_stroke_and_referee_are_exposed`; stats `strokes`, `stroke_goals` y eventos `stroke` | PASS |
| Shootout: cinco rondas, muerte súbita y ganador único | `test_shootout_resolves_draw_with_five_rounds_and_winner` | PASS |
| Sustituciones: máximo cinco y banquillo | `test_substitution_limit_and_red_card_suspension` | PASS |
| No sustituir sancionados/lesionados | `test_substitution_limit_and_red_card_suspension` y tests de tarjetas | PASS |
| Árbitro con nombre, estilo, exigencia y sesgo de tarjetas | `test_penalty_corner_stroke_and_referee_are_exposed`; `MatchResult.referee` | PASS |
| Tarjetas verde/amarilla/roja y suspensiones temporales | `test_rules_cards.py` | PASS |

## 8. E2E de la beta

Script: `manager/web/frontend/e2e_beta.mjs` (Playwright contra Flask).

Salida verificada:

```json
{"newGame":true,"calendar":true,"monthNavigation":true,"quickMatch":true,"refereeAndSetPieces":true,"postPress":true,"viewer3d":true,"viewerPhysics":{"frames":60,"collisions":55,"ballSpeed":9.04},"playerBrands":true}
```

Flujo:

1. Crear partida desde la API.
2. Abrir `/app/game/calendar` y comprobar la vista mensual.
3. Navegar al mes siguiente.
4. Simular un partido rápido.
5. Abrir el parte y comprobar árbitro y estadísticas de PC/strokes.
6. Abrir `/app/game/live` y comprobar el canvas del visor 3D.
7. Abrir `/app/game/press/post`, responder las cuatro preguntas y completar la rueda.
8. Abrir `/app/game/commercial` y comprobar los contratos individuales de imagen.

## 9. Límites convertidos en criterios pass/fail

| Límite anterior | Criterio verificable | Estado |
| --- | --- | --- |
| “No hay motor 3D” | Simulación 3D con campo, 22 jugadores animados, balón con física, colisiones y UI | PASS simulación 3D / FAIL física AAA |
| “FIH no cubre cada interpretación” | PC, stroke, shootout, tarjetas, sustituciones y árbitro tienen pruebas explícitas; el resto de interpretaciones discrecionales no se reclama | PASS para reglas implementadas / FAIL para arbitraje discrecional completo |
| “No replica todas las pantallas de FM24” | La matriz enumera los flujos cubiertos; la paridad total de pantallas no se declara | FAIL / fuera de alcance |
| “Prensa textual” | Prensa previa y posterior con medios, efectos e historial | PASS |
| “Marcas no cambian la física” | Contratos de club e individuales con efectos económicos, de marca y relación; no se promete física de material | PASS para gestión / FAIL para simulación física |
| “No hay vídeo de comparecencia” | La prensa es una pantalla textual interactiva | FAIL / fuera de alcance |

## 10. Resultado

La beta avanzada pasa los criterios de los flujos solicitados y de las reglas FIH operativas. La matriz distingue explícitamente **PASS** de **FAIL / fuera de alcance**; no se presenta como una réplica completa de FM24 ni como una simulación arbitral discrecional total.
