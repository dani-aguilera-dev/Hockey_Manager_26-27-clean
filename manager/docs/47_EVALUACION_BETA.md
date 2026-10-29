# Evaluación de la beta avanzada

**Fecha:** 2026-10-29  
**Rama:** `main`  

## Criterios y resultado

| Criterio | Evidencia | Estado |
| --- | --- | --- |
| Plantillas sin cuerpo técnico | `STAFF_PROFILES` filtra Entrenador, Delegado, Fisioterapeuta, Staff Adicional, Preparador Físico, Médico y Psicólogo; test `test_staff_are_not_loaded_as_players` | PASS |
| Sin mujeres del staff como jugadoras | Berta Puente, Nuria Álvarez, Maria Laura Perrone y Sara Betancor ya no aparecen en `team.players` | PASS |
| Club Giner de los Ríos corregido | Valencia / Comunidad Valenciana / fundado en 1993 / Campanar / Beteró; test `test_clubs_have_verified_location_and_description` | PASS |
| Calendario y amistosos | `src/friendlies.py`, `/api/calendar`, `/api/friendlies`, pantalla `Calendar.tsx`; amistosos sin puntos | PASS |
| Prensa con medios y periodistas | `src/press.py` con periodista, medio, seis temas y confianza mediática; `Press.tsx` renovada | PASS |
| Marcas reales de hockey | `data/brands.json` con Osaka, Ritual, Gryphon, Grays, TK, Mercian, STX, Adidas, Kookaburra, JDH, Malik, Dita, Voodoo, Byte, Princess, Harrow, OBO, Fat Pipe, Monkey, Tempest y Rage | PASS |
| Firma de marcas | `/api/brands`, ofertas, prima, anualidad, bonus de equipación aplicado al motor | PASS |
| Editor de jugadores | `/api/player/<id>/edit`, modal en `Player.tsx`, edición de posición, overall, potencial y atributos | PASS |
| Clubes internacionales descritos | 70 clubes con ciudad, país, historia y fuente en `data/international.json` | PASS |
| Backend | `python3 -m pytest src/tests -q` → **210 passed** | PASS |
| Frontend | `npm run build` → SPA compilada sin errores TypeScript | PASS |
| Servidor web | `/api/health` 200; `/app` 200; asset React 200 | PASS |
| Revisión de vídeo | `/api/match/live/review`, gol/PC/stroke revisables, referencia por equipo y corrección de marcador | PASS |
| Junta y visión de club | `/api/board`, `/api/board/request`, `Board.tsx`: confianza, visión, instalaciones, peticiones e historial | PASS |
| Cesiones y préstamos | `/api/loans`, `/api/loans/in`, `/api/loans/out`, `Loans.tsx`: entrantes, salientes, tasas, salario, minutos y retorno | PASS |
| Data hub e instrucciones al rival | `/api/datahub`, `/api/datahub/instructions`, `DataHub.tsx`: análisis, jugadores clave e instrucciones aplicadas al motor | PASS |
| Afiliados y mentoring | `/api/affiliates`, `/api/mentoring`, `Affiliates.tsx`: red de clubes, beneficios, planes de desarrollo y progreso | PASS |
| Historial completo | `/api/history`, `History.tsx`: temporadas, competiciones, partidos, jugadores, filtros y récords | PASS |
| Ojeo con pantalla dedicada | `/api/scouting`, `/api/scouting/assignments`, `Scouting.tsx`: asignaciones, progreso e informes | PASS |
| E2E Playwright | calendario mensual, amistoso/partido, visor 3D, revisión de vídeo, junta, cesiones, data hub, afiliados, mentoring, historial, ojeo, prensa posterior y marcas individuales | PASS |
| Persistencia | `GameState` serializa amistosos, marcas, media y equipación; `persistence` limpia staff de partidas antiguas | PASS |

## Pruebas específicas

`src/tests/test_beta_features.py`:

1. `test_staff_are_not_loaded_as_players`
2. `test_clubs_have_verified_location_and_description`
3. `test_friendlies_are_scheduled_and_do_not_touch_league_table`
4. `test_brand_offers_and_equipment_bonus`
5. `test_player_editor_can_fix_position_and_attributes`
6. `test_press_has_journalist_media_and_six_topics`
7. `test_api_calendar_brands_editor_and_press`
8. `test_api_video_review_flow`
9. `test_api_board_overview_and_request`
10. `test_api_loans_in_and_active_list`
11. `test_api_datahub_and_opposition_instructions`
12. `test_api_affiliates_and_mentoring`
13. `test_api_history_and_filters`
14. `test_api_scouting_assignments`

`src/tests/test_acceptance_beta.py` incluye además:

- `test_video_review_overturns_goal_and_retains_referral`
- `test_video_review_upheld_consumes_referral`
- `test_penalty_corner_and_stroke_are_reviewable`
- `test_video_review_rejects_own_decision_and_unknown_play`

`src/tests/test_board.py`:

- `test_board_overview_has_vision_facilities_and_requests`
- `test_board_request_approved_updates_facility_and_budget`
- `test_board_request_rejected_keeps_facility_and_records_history`
- `test_board_request_requires_funds_and_valid_id`
- `test_board_facilities_and_requests_persist_in_team_state`

`src/tests/test_loans.py`:

- `test_loan_overview_lists_targets_outgoing_and_terms`
- `test_loan_in_moves_player_and_returns_to_parent`
- `test_loan_out_moves_player_to_borrower_and_returns`
- `test_rejected_loan_keeps_player_and_records_history`
- `test_loan_validation_and_persistence`

`src/tests/test_datahub.py`:

- `test_datahub_has_opponent_analysis_key_players_and_options`
- `test_set_instructions_validates_players_and_saves`
- `test_opposition_instructions_reduce_opponent_strength`
- `test_opposition_instructions_persist_in_game_state`

`src/tests/test_affiliates.py`:

- `test_affiliate_overview_has_candidates_and_benefits`
- `test_affiliate_request_accepts_and_applies_benefits`
- `test_affiliate_request_can_be_rejected`
- `test_mentoring_assigns_and_develops_young_player`
- `test_mentoring_validation_and_persistence`

`src/tests/test_history.py`:

- `test_history_current_matches_and_archive`
- `test_history_filters_and_records`
- `test_history_archive_is_idempotent_and_persists`

`src/tests/test_scouting_assignments.py`:

- `test_scouting_overview_has_assignment_options`
- `test_create_assignment_and_complete_report`
- `test_assignment_limit_and_validation`
- `test_scouting_assignments_persist`

## Comandos ejecutados

```text
python3 -m pytest src/tests -q
210 passed in 320.23s

cd manager/web/frontend && npm run build
✓ built in 4.99s

curl /api/health → 200
curl /app → 200
curl /static/react/assets/index-BjuZE3SH.js → 200

node web/frontend/e2e_beta.mjs
{"newGame":true,"calendar":true,"monthNavigation":true,"quickMatch":true,"refereeAndSetPieces":true,"postPress":true,"viewer3d":true,"viewerSkeleton":{"bones":374,"sticks":22,"ikSolutions":2816},"viewerPhysics":{"frames":64,"playerCollisions":0,"bodyCollisions":50,"stickCollisions":33,"ballSpeed":7.61},"videoReview":true,"videoReviewType":"penalty_corner","boardRequest":true,"loans":true,"datahub":true,"affiliates":true,"mentoring":true,"history":true,"scouting":true,"playerBrands":true}
```

## Límites conscientes

La beta ya tiene una capa de gestión mucho más amplia, pero no se presenta como una réplica completa de Football Manager 24. Las siguientes piezas de mayor valor serían:

- revisión de vídeo con interpretación arbitral completa (solo están modeladas las decisiones revisables);
- física 3D AAA (tejido, materiales, captura de movimiento);
- paridad total de pantallas y bases de datos de FM24;
- auditoría visual de fotos de jugadores (la incidencia principal era el staff cargado como plantilla).
