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
| Junta y visión de club | `src/board.py`, `/api/board`, `Board.tsx`: confianza, presión, paciencia, visión a corto/medio/largo plazo | `test_board_overview_has_vision_facilities_and_requests`, E2E `boardRequest` | PASS |
| Peticiones de inversión | `/api/board/request`: entrenamiento, cantera, médico, video, ojeo, estadio y presupuesto; aprobación según confianza y caja | `test_board_request_approved_updates_facility_and_budget`, `test_board_request_rejected_keeps_facility_and_records_history` | PASS |
| Instalaciones y estadio | Ratings de instalaciones, aforo, academia y presupuesto persistidos en `TeamState` | `test_board_facilities_and_requests_persist_in_team_state` | PASS |
| Cesiones entrantes | `src/loans.py`, `/api/loans/in`, `Loans.tsx`: jugador sale del club de origen y entra en el usuario con contribución salarial y promesa de minutos | `test_loan_in_moves_player_and_returns_to_parent`, `test_api_loans_in_and_active_list`, E2E `loans` | PASS |
| Cesiones salientes | `/api/loans/out`: oferta a clubes interesados, tasa de cesión y contribución salarial | `test_loan_out_moves_player_to_borrower_and_returns` | PASS |
| Retorno al club de origen | `return_loans()` en `advance_to_next_season`: devuelve a todos los cedidos y registra el historial | `test_loan_in_moves_player_and_returns_to_parent` | PASS |
| Persistencia de cesiones | `GameState.loans`, `GameState.loan_history` y `PlayerState.loan` serializados | `test_loan_validation_and_persistence` | PASS |
| Data hub del rival | `src/datahub.py`, `/api/datahub`, `DataHub.tsx`: forma, estadísticas, táctica, bajas, jugadores clave, historial directo y comparativa | `test_datahub_has_opponent_analysis_key_players_and_options`, E2E `datahub` | PASS |
| Instrucciones al rival | `/api/datahub/instructions`, `GameState.opposition_instructions`: marcaje, presión, doblar por banda y forzar lado débil | `test_set_instructions_validates_players_and_saves`, `test_opposition_instructions_persist_in_game_state` | PASS |
| Efecto de las instrucciones en el motor | `MatchEngine.opposition_effect` reduce ataque/defensa del rival según los jugadores marcados | `test_opposition_instructions_reduce_opponent_strength` | PASS |
| Clubes afiliados | `src/affiliates.py`, `/api/affiliates`, `Affiliates.tsx`: candidatos, cuota, beneficios de ojeo/cantera y prioridad en cesiones | `test_affiliate_request_accepts_and_applies_benefits`, E2E `affiliates` | PASS |
| Mentoring de jóvenes | `/api/mentoring`, `TeamState.mentoring`: mentor veterano, joven, plan y progreso semanal | `test_mentoring_assigns_and_develops_young_player`, E2E `mentoring` | PASS |
| Persistencia de afiliados y mentorías | `GameState.affiliates`, `GameState.affiliate_history`, `TeamState.mentoring` y `mentoring_history` | `test_mentoring_validation_and_persistence` | PASS |
| Archivo de partidos | `archive_season_matches`, `GameState.match_history`: temporada, competición, ronda, marcador, estadísticas y goleadores | `test_history_current_matches_and_archive` | PASS |
| Archivo de jugadores | `archive_season_players`, `GameState.player_history`: partidos, goles, asistencias, rating y equipo por temporada | `test_history_current_matches_and_archive` | PASS |
| Consulta y filtros | `GET /api/history`, `History.tsx`: temporada, competición, equipo y jugador; pestañas de temporadas, competiciones, partidos, jugadores y récords | `test_history_filters_and_records`, E2E `history` | PASS |
| Récords históricos | Máximo goleador, más partidos, mejor rating, mayor victoria, club con más títulos y mejor posición | `test_history_filters_and_records` | PASS |
| Persistencia del historial | `GameState.match_history` y `GameState.player_history` serializados y compatibles con partidas antiguas | `test_history_archive_is_idempotent_and_persists` | PASS |
| Asignaciones de ojeo | `src/scouting.py`, `/api/scouting/assignments`, `Scouting.tsx`: ojeador, competición, posición, edad y enfoque | `test_create_assignment_and_complete_report`, E2E `scouting` | PASS |
| Progreso e informes de ojeo | `advance_scouting` avanza con las jornadas y genera informes con objetivos reales de la competición asignada | `test_create_assignment_and_complete_report` | PASS |
| Persistencia del ojeo | `GameState.scouting_assignments` y `GameState.scouting_reports` serializados | `test_scouting_assignments_persist` | PASS |
| Finanzas detalladas | `src/finance.py`, `/api/finance`, `Finance.tsx`: caja, presupuesto, salarios, ingresos, gastos, proyección y taquilla | `test_finance_overview_has_breakdown_projection_and_earners`, E2E `finance` | PASS |
| Control de taquilla | `/api/finance/ticket` y escenarios de precio/asistencia/ingresos | `test_finance_ticket_price_updates_and_persists` | PASS |
| Análisis de partido | `src/analysis.py`, `/api/analysis`, `Analysis.tsx`: eficiencia, comparativa, cronología, ratings y archivo | `test_analysis_overview_has_metrics_timeline_and_players`, E2E `analysis` | PASS |
| Responsabilidades del staff | `src/responsibilities.py`, `/api/responsibilities`, `Responsibilities.tsx`: 10 áreas, responsable y bonus de entrenamiento/ojeo | `test_responsibility_assignment_and_bonus`, E2E `responsibilities` | PASS |
| Desarrollo individual | `src/development.py`, `/api/development`, `Development.tsx`: foco, intensidad, progreso semanal, cantera y primer equipo | `test_development_plan_progresses_and_gains_attributes`, E2E `development` | PASS |
| Premios y galardones | `src/awards.py`, `/api/awards`, `Awards.tsx`: MVP, goleador, joven, portero, defensa, once ideal, premios de partido e historial | `test_season_awards_and_best_xi`, E2E `awards` | PASS |
| Centro de contratos | `src/contracts.py`, `/api/contracts`, `Contracts.tsx`: vencimientos, salarios, años restantes, masa salarial y renovaciones | `test_contracts_overview_has_summary_and_candidates`, E2E `contracts` | PASS |
| Instalaciones del club | `src/facilities.py`, `/api/facilities`, `Facilities.tsx`: estadio, entrenamiento, cantera, médico, vídeo, ojeo y mejoras | `test_facilities_overview_has_levels_and_upgrades`, E2E `facilities` | PASS |
| Cláusulas y primas | `src/clauses.py`, `/api/clauses`, `Clauses.tsx`: cláusula de rescisión, prima de renovación, coste y protección | `test_set_clause_deducts_bonus_and_persists`, E2E `clauses` | PASS |
| Lista de seguimiento | `src/shortlist.py`, `/api/shortlist`, `Shortlist.tsx`: búsqueda, prioridad, notas, valor, contrato y petición del objetivo | `test_add_update_and_remove_shortlist_entry`, E2E `shortlist` | PASS |
| Reunión de equipo | `src/team_meeting.py`, `/api/team-meeting`, `TeamMeeting.tsx`: tipo, tono, temas, dinámica y efectos | `test_team_meeting_applies_effects_and_history`, E2E `teamMeeting` | PASS |
| Promesas de la reunión | Promesas de minutos o renovación persistentes en `PlayerState.promises` y comprobadas por `check_promises` | `test_team_meeting_creates_persistent_promise` | PASS |
| Persistencia de reuniones | `TeamState.team_meetings` serializado con efectos, temas y promesas | `test_team_meeting_creates_persistent_promise` | PASS |

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
| 22 jugadores con locomoción | 11 locales y 11 visitantes, piernas/brazos animados, desplazamiento y separación | E2E `players=22`, `frames=64` | PASS |
| Esqueleto jerárquico | Cadera, torso, cabeza, cuello, brazos, antebrazos, manos, muslos, espinillas y pies; 17 huesos por jugador | E2E `bones=374` | PASS |
| IK de brazos | IK analítico de dos huesos para llevar ambas manos a las agarraderas del stick en cada frame | E2E `ikSolutions=2816` | PASS |
| Sticks | 22 sticks con mango y pala; colisión segmento-bola | E2E `sticks=22`, `stickCollisions=33` | PASS |
| Balón con física | Velocidad, gravedad, rebote, fricción, límites y detección de gol | E2E `ballSpeed=7.66` | PASS |
| Colisiones de cuerpo | Colisión cuerpo-bola con rebote y separación jugador-jugador | E2E `bodyCollisions=50` | PASS |
| UI 3D | Marcador, cuarto, minuto, estado, último evento y cámara táctica superpuestos al canvas | E2E `match-viewer-ui` + captura | PASS |
| Conexión con MatchEngine | El visor consume `LivePayload`: `score`, `quarter`, `minute`, `line`, `events`, formación y equipo atacante | `/api/match/live` y `/api/match/live/advance` | PASS |
| Respuesta de materiales | Restitución de 0,62, fricción, deformación de la bola al impactar y flexión del stick | E2E `viewerMaterials.materialBounces=39`, `stickFlexes=48` | PASS |
| Colisión stick-cuerpo | Segmento del stick contra puntos del cuerpo rival, empuje y flexión; escenario de contacto determinista | E2E `viewerMaterials.stickBodyCollisions=16` | PASS |
| Biomecánica procedural | Equilibrio, inclinación del tronco, zancada, flexión de rodilla, contrapeso de brazos y límites articulares | E2E `viewerBiomechanics.biomechSolutions=2464` | PASS |
| Tejido procedural | Paneles de camiseta con movimiento secundario ligado a velocidad, inclinación y fase del jugador | E2E `viewerBiomechanics.clothUpdates=1232` | PASS |
| Física 3D AAA / mocap real | No hay captura de movimiento, simulación textil real, colisiones de tejido ni biomecánica de producción | Matriz lo declara fuera de alcance | FAIL / fuera de alcance |

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
| Revisión de vídeo de gol, PC y stroke | `MatchEngine.review_decision`, `/api/match/live/review`, tarjeta “Revisión de vídeo” en `LiveMatch.tsx` | `test_video_review_overturns_goal_and_retains_referral`, `test_penalty_corner_and_stroke_are_reviewable`, `test_api_video_review_flow`, E2E `videoReview` | PASS |
| Referencia por equipo y retención si prospera | `REFERRALS_PER_TEAM=1`; una revisión acertada conserva la referencia y una fallida la consume | `test_video_review_overturns_goal_and_retains_referral`, `test_video_review_upheld_consumes_referral` | PASS |
| Corrección de marcador y estadísticas | El gol anulado resta marcador, stats de equipo y stats individuales | `test_video_review_overturns_goal_and_retains_referral` | PASS |
| Ventaja | `_foul` deja jugar la ventaja si no hay juego peligroso y el ataque conserva la posesión | `test_advantage_keeps_possession_and_is_recorded` | PASS |
| Juego peligroso | `FOUL_TYPES` distingue golpe de stick y juego peligroso; puede derivar en tarjeta | `test_dangerous_play_is_recorded_and_can_award_pc` | PASS |
| Distancia de 5 metros | `distance_5m` y aviso arbitral en el libre directo | `test_five_meters_is_enforced_on_free_hit` | PASS |
| Decisión de PC/stroke | `pc_decision` permite PC, denegarlo o convertirlo en stroke | `test_pc_can_be_denied_by_referee`, `test_dangerous_play_can_upgrade_pc_to_stroke` | PASS |
| Decisiones en el parte | `Report.tsx` muestra ventajas, juego peligroso, 5 m, PC denegados y strokes concedidos | E2E `refereeDiscretion` | PASS |
| Protestas y conducta antideportiva | `_protest` y `_unsportsmanlike`: aviso, tarjeta, retraso, simulación y conducta antideportiva | `test_protest_warning_records_dissent_without_card`, `test_unsportsmanlike_delay_and_simulation` | PASS |
| Tiempo añadido | `compute_added_time` por cuarto según lesiones, tarjetas, revisiones, protestas y PC; visible en el parte | `test_added_time_is_computed_and_in_result`, `test_api_report_has_added_time_and_discipline_stats`, E2E `refereeDiscipline` | PASS |
| Protesta en directo | `/api/match/live/protest`, `protest_decision`: una por equipo, respetuosa o vehemente, con riesgo de tarjeta | `test_live_protest_respectful_is_one_per_team`, `test_api_live_protest_once_per_match`, E2E `liveProtest` | PASS |
| Arbitraje discrecional completo | Quedan interpretaciones subjetivas no modeladas (criterios finos de peligrosidad, ventaja en cada zona, gestión de protestas en directo, etc.) | Matriz lo declara fuera de alcance | FAIL / fuera de alcance |


> Los contadores de frames, IK y colisiones varían entre ejecuciones; el E2E exige que sean mayores que cero y que el esqueleto y los sticks estén completos.

## 8. E2E de la beta

Script: `manager/web/frontend/e2e_beta.mjs` (Playwright contra Flask).

Salida verificada:

```json
{"newGame":true,"calendar":true,"monthNavigation":true,"quickMatch":true,"refereeAndSetPieces":true,"refereeDiscretion":true,"refereeDiscipline":true,"analysis":true,"postPress":true,"viewerBiomechanics":{"biomechSolutions":2772,"clothUpdates":1386},"liveProtest":true,"viewer3d":true,"viewerMaterials":{"stickBodyCollisions":16,"materialBounces":60,"stickFlexes":69},"viewerSkeleton":{"bones":374,"sticks":22,"ikSolutions":2772},"viewerPhysics":{"frames":63,"playerCollisions":0,"bodyCollisions":51,"stickCollisions":36,"ballSpeed":2.39},"videoReview":true,"videoReviewType":"penalty_corner","boardRequest":true,"loans":true,"datahub":true,"affiliates":true,"mentoring":true,"history":true,"scouting":true,"teamMeeting":true,"finance":true,"responsibilities":true,"development":true,"awards":true,"contracts":true,"facilities":true,"clauses":true,"shortlist":true,"playerBrands":true}
```

Flujo:

1. Crear partida desde la API.
2. Abrir `/app/game/calendar` y comprobar la vista mensual.
3. Navegar al mes siguiente.
4. Simular un partido rápido.
5. Abrir el parte y comprobar árbitro y estadísticas de PC/strokes.
6. Abrir `/app/game/live`, comprobar el canvas, el esqueleto, los sticks, el IK y las colisiones de cuerpo/stick.
7. Avanzar hasta una decisión contra el usuario y solicitar la revisión de vídeo desde la pantalla en directo.
8. Abrir `/app/game/board`, comprobar la visión de club y presentar una petición de mejora de entrenamiento.
9. Abrir `/app/game/loans`, comprobar las cesiones entrantes y solicitar una cesión.
10. Abrir `/app/game/datahub`, revisar el análisis del rival y guardar instrucciones.
11. Abrir `/app/game/affiliates`, solicitar una afiliación y crear una mentoría.
12. Abrir `/app/game/history`, consultar partidos, jugadores y récords.
13. Abrir `/app/game/scouting`, crear una asignación de ojeo y comprobar la pantalla dedicada.
14. Abrir `/app/game/team-meeting`, convocar una reunión y comprobar el resultado y el historial.
15. Abrir `/app/game/finance`, cambiar el precio de taquilla y comprobar la proyección.
16. Abrir `/app/game/analysis`, revisar eficiencia, cronología y rendimiento individual.
17. Abrir `/app/game/responsibilities`, asignar un responsable y comprobar el guardado.
18. Abrir `/app/game/development`, asignar un plan individual y comprobar el guardado.
19. Abrir `/app/game/awards`, revisar premios, once ideal e historial.
20. Abrir `/app/game/contracts`, revisar vencimientos y masa salarial.
21. Abrir `/app/game/facilities`, solicitar una mejora y comprobar el historial.
22. Abrir `/app/game/clauses`, registrar una cláusula y una prima de renovación.
23. Abrir `/app/game/shortlist`, añadir un objetivo, cambiar su prioridad y guardar.
24. Abrir `/app/game/press/post`, responder las cuatro preguntas y completar la rueda.
25. Abrir `/app/game/commercial` y comprobar los contratos individuales de imagen.

## 9. Límites convertidos en criterios pass/fail

| Límite anterior | Criterio verificable | Estado |
| --- | --- | --- |
| “No hay motor 3D” | Simulación 3D con campo, 22 jugadores con esqueleto, IK, biomecánica procedural, tejido estilizado, sticks, materiales, colisiones de cuerpo/stick-cuerpo y UI | PASS simulación 3D / FAIL física AAA y mocap |
| “FIH no cubre cada interpretación” | PC, stroke, shootout, tarjetas, sustituciones, árbitro, revisión de vídeo, ventaja, juego peligroso, 5 metros, decisión de PC, protestas, conducta antideportiva y tiempo añadido tienen pruebas explícitas; el resto de interpretaciones subjetivas no se reclama | PASS para reglas implementadas / FAIL para arbitraje discrecional completo |
| “No replica todas las pantallas de FM24” | La matriz enumera los flujos cubiertos; la paridad total de pantallas no se declara | FAIL / fuera de alcance |
| “Prensa textual” | Prensa previa y posterior con medios, efectos e historial | PASS |
| “Marcas no cambian la física” | Contratos de club e individuales con efectos económicos, de marca y relación; no se promete física de material | PASS para gestión / FAIL para simulación física |
| “No hay vídeo de comparecencia” | La prensa es una pantalla textual interactiva | FAIL / fuera de alcance |

## 10. Inventario de pantallas y flujos FM24

| Pantalla / flujo | Estado | Evidencia o hueco |
| --- | --- | --- |
| Dashboard y centro de decisiones | PASS | `Dashboard.tsx`, `Decisions.tsx`, `/api/state`, `/api/events` |
| Plantilla y ficha de jugador | PASS | `Squad.tsx`, `Player.tsx`, `/api/squad`, `/api/player/<id>` |
| Editor de jugadores | PASS | Modal de `Player.tsx`, `/api/player/<id>/edit` |
| Club y estadio | PASS | `Team.tsx`, `/api/team/<id>`, auditoría de 99 clubes |
| Táctica y planes de partido | PASS | `Tactics.tsx`, `/api/tactics`, táctica en directo |
| Entrenamiento semanal | PASS | `Training.tsx`, `/api/training` |
| Médico y disponibilidad | PASS | `Medical.tsx`, `/api/medical` |
| Mercado, negociaciones y ofertas | PASS | `Market.tsx`, `Offers.tsx`, `/api/market/*` |
| Renovaciones de contrato | PASS | `Renew.tsx`, `/api/market/renew*` |
| Comercial, patrocinios y marcas | PASS | `Commercial.tsx`, `/api/commercial`, `/api/brands*` |
| Staff y cuerpo técnico | PASS | `Staff.tsx`, `/api/staff*` |
| Responsabilidades del staff | PASS | `Responsibilities.tsx`, `/api/responsibilities`, áreas, responsables y bonus de entrenamiento/ojeo |
| Desarrollo individual | PASS | `Development.tsx`, `/api/development`, foco, intensidad, progreso, cantera y primer equipo |
| Premios y galardones | PASS | `Awards.tsx`, `/api/awards`, MVP, goleador, joven, portero, defensa, once ideal e historial |
| Centro de contratos | PASS | `Contracts.tsx`, `/api/contracts`, vencimientos, salarios, años, masa salarial y renovaciones |
| Instalaciones del club | PASS | `Facilities.tsx`, `/api/facilities`, estado, aforo, cantera, médico, vídeo, ojeo y mejoras |
| Cláusulas y primas | PASS | `Clauses.tsx`, `/api/clauses`, cláusula de rescisión, prima, coste y protección |
| Lista de seguimiento | PASS | `Shortlist.tsx`, `/api/shortlist`, búsqueda, prioridad, notas, valor, contrato y petición |
| Cantera | PASS | `Youth.tsx`, `/api/youth*` |
| Calendario, amistosos y vista mensual | PASS | `Calendar.tsx`, `/api/calendar`, `/api/friendlies*` |
| Prensa previa y posterior | PASS | `Press.tsx`, `PostPress.tsx`, `/api/press*` |
| Clasificación, Copa, EHL y ascenso | PASS | `Table.tsx`, `Cup.tsx`, `Ehl.tsx`, `Promotion.tsx`, `Objectives.tsx` |
| Previa, directo y parte de partido | PASS | `MatchPreview.tsx`, `LiveMatch.tsx`, `Report.tsx` |
| Análisis de partido | PASS | `Analysis.tsx`, `/api/analysis`, eficiencia, comparativa, cronología, ratings y archivo |
| Revisión de vídeo | PASS | `LiveMatch.tsx`, `/api/match/live/review`, `MatchEngine.review_decision` |
| Fin de temporada y multi-temporada | PASS | `SeasonEnd.tsx`, `/api/season/*` |
| Ojeo con pantalla dedicada | PASS | `Scouting.tsx`, `/api/scouting`, `/api/scouting/assignments`, asignaciones, progreso e informes |
| Charlas de equipo y dinámica de vestuario | PASS | `TeamMeeting.tsx`, `/api/team-meeting`, tipos, tonos, temas, promesas y efectos persistentes |
| Cesiones y préstamos | PASS | `Loans.tsx`, `/api/loans`, `/api/loans/in`, `/api/loans/out`, retorno al club de origen al cerrar la temporada |
| Junta, visión de club e instalaciones | PASS | `Board.tsx`, `/api/board`, `/api/board/request`, visión a corto/medio/largo plazo, instalaciones y peticiones con historial |
| Instrucciones al rival y data hub | PASS | `DataHub.tsx`, `/api/datahub`, `/api/datahub/instructions`, análisis del rival e instrucciones aplicadas al motor |
| Clubes afiliados y mentoring | PASS | `Affiliates.tsx`, `/api/affiliates`, `/api/mentoring`, red de clubes, beneficios y planes de desarrollo |
| Historial/base de datos consultable | PASS | `History.tsx`, `/api/history`, archivo de partidos y jugadores, filtros y récords |
| Finanzas detalladas | PASS | `Finance.tsx`, `/api/finance`, `/api/finance/ticket`, cuenta de resultados, proyección, salarios y taquilla |
| Arbitraje discrecional completo | FAIL / parcial | Ventaja, juego peligroso, 5 m, PC, protestas, conducta antideportiva, tiempo añadido y protesta en directo están modelados; el resto de interpretaciones subjetivas sigue fuera de alcance |

La lista permite priorizar la siguiente iteración sin confundir “flujo cubierto” con “paridad total”. Las pantallas marcadas FAIL no se presentan como terminadas.

## 11. Resultado

La beta avanzada pasa los criterios de los flujos solicitados, de las reglas FIH operativas, de la revisión de vídeo, de la junta/visión de club, de las cesiones, del data hub con instrucciones al rival, de afiliados/mentoring, del historial completo, del ojeo con pantalla dedicada, de la reunión de equipo, de las decisiones arbitrales implementadas (incluidas protestas, tiempo añadido y protesta en directo), de la respuesta de materiales/colisiones stick-cuerpo, de la biomecánica procedural/tejido estilizado del visor, del centro financiero, del análisis de partido, de las responsabilidades del staff, del desarrollo individual, de los premios, del centro de contratos, de las instalaciones del club, de las cláusulas/primas y de la lista de seguimiento. La matriz distingue explícitamente **PASS** de **FAIL / fuera de alcance**; no se presenta como una réplica completa de FM24 ni como una simulación arbitral discrecional total. El inventario de la sección 10 deja identificados los huecos de paridad que quedan: mocap/física textil real, paridad total de pantallas y el resto de interpretaciones arbitrales subjetivas.
