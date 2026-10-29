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

## 6. E2E de la beta

Script: `manager/web/frontend/e2e_beta.mjs` (Playwright contra Flask).

Salida verificada:

```json
{"newGame":true,"calendar":true,"monthNavigation":true,"quickMatch":true,"postPress":true,"playerBrands":true}
```

Flujo:

1. Crear partida desde la API.
2. Abrir `/app/game/calendar` y comprobar la vista mensual.
3. Navegar al mes siguiente.
4. Simular un partido rápido.
5. Abrir `/app/game/press/post`, responder las cuatro preguntas y completar la rueda.
6. Abrir `/app/game/commercial` y comprobar los contratos individuales de imagen.

## 7. Límites declarados

- No hay motor 3D ni captura de vídeo de partido.
- La fidelidad FIH cubre reglas operativas del motor, no cada interpretación arbitral.
- La beta no replica todas las pantallas, bases de datos ni licencias de FM24.
- La prensa es textual; no hay comparecencia con vídeo ni preguntas en tiempo real.
- Los contratos de marca son una capa de gestión; no cambian la simulación física del material.

## 8. Resultado

La beta avanzada pasa la matriz para los flujos solicitados: calendario, amistosos, prensa previa y posterior, marcas de club e individuales, editor de jugadores, plantillas limpias, clubes auditados y reglas FIH operativas. La paridad total con FM24 queda fuera del alcance de esta iteración y se documenta como límite, no como funcionalidad oculta.
