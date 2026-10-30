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
| Limpieza de plantillas | Invitados al mercado con equipo de procedencia; DHA/DHB con 18 fichas reales, sin `Invitado` y presupuesto salarial recalculado | PASS |
| Pulido de UI y scouting | Mercado con carga y recuento real; calendario “Agosto de 2026”; tácticas sin lista duplicada; entrenamiento con etiquetas en español; score del ojeador normalizado 60-100 | PASS |
| Clubes internacionales descritos | 70 clubes con ciudad, país, historia y fuente en `data/international.json` | PASS |
| Backend | `python3 -m pytest src/tests -q` → **341 passed** | PASS |
| Frontend | `npm run build` → SPA compilada sin errores TypeScript | PASS |
| Servidor web | `/api/health` 200; `/app` 200; asset React 200 | PASS |
| Revisión de vídeo | `/api/match/live/review`, gol/gol anulado/PC/stroke revisables, referencia por equipo y corrección de marcador | PASS |
| Junta y visión de club | `/api/board`, `/api/board/request`, `Board.tsx`: confianza, visión, instalaciones, peticiones e historial | PASS |
| Cesiones y préstamos | `/api/loans`, `/api/loans/in`, `/api/loans/out`, `Loans.tsx`: entrantes, salientes, tasas, salario, minutos y retorno | PASS |
| Data hub e instrucciones al rival | `/api/datahub`, `/api/datahub/instructions`, `DataHub.tsx`: análisis, jugadores clave e instrucciones aplicadas al motor | PASS |
| Afiliados y mentoring | `/api/affiliates`, `/api/mentoring`, `Affiliates.tsx`: red de clubes, beneficios, planes de desarrollo y progreso | PASS |
| Historial completo | `/api/history`, `History.tsx`: temporadas, competiciones, partidos, jugadores, filtros y récords | PASS |
| Ojeo con pantalla dedicada | `/api/scouting`, `/api/scouting/assignments`, `Scouting.tsx`: asignaciones, progreso e informes | PASS |
| Reunión de equipo | `/api/team-meeting`, `TeamMeeting.tsx`: charla, dinámica, promesas y efectos persistentes | PASS |
| Arbitraje discrecional | Ventaja, juego peligroso, 5 m, PC/stroke, protestas, conducta antideportiva, tiempo añadido y protesta en directo | PASS |
| Arbitraje subjetivo | Severidad del juego peligroso, golpe franco +10 m y repetición de PC/stroke | PASS |
| Ventaja con retorno | Si la ventaja no se materializa, se vuelve a la falta original; en el círculo, PC | PASS |
| Gol anulado por pie o revés | `_disallowed_goal` en juego abierto, stats `goals_disallowed`, `foot_goals_disallowed` y `back_stick_goals_disallowed`; revisable por el equipo atacante | PASS |
| Gol solo desde el círculo | `_shot` anula el disparo directo desde fuera; el desvío dentro del círculo se concede | PASS |
| Gol anulado por mano/brazo | `_disallowed_goal` en juego abierto con motivo `hand`, stat `hand_goals_disallowed`, evento y revisión | PASS |
| Trabajo y seguridad | `/api/jobs`, `Jobs.tsx`: confianza, contrato, ofertas de misma liga y otras ligas, aceptar/rechazar e historial | PASS |
| Cambio entre ligas | Acuerdo diferido, cambio de club y reconstrucción de calendario al avanzar la temporada; incluye ligas internacionales | PASS |
| Vacantes de entrenador | `/api/vacancies`, `Vacancies.tsx`: clubes con banquillo disponible, candidaturas y ofertas | PASS |
| Despidos automáticos de clubes IA | `src/managers.py`: presión, destitución, nombramiento de sustituto del cuerpo técnico o interino y `state.manager_changes`; el usuario recibe ultimátum | PASS (clubes IA) |
| Despido automático del usuario | `process_user_sacking`, `sack_user`, `/api/jobs/resign`, `SackedScreen`: presión, destitución, dimisión y reincorporación | PASS |
| Pruebas de agentes libres | `/api/trials`, `Trials.tsx`: invitación, progreso, informes y recomendación | PASS |
| Finanzas detalladas | `/api/finance`, `/api/finance/ticket`, `Finance.tsx`: cuenta de resultados, salarios, proyección y taquilla | PASS |
| Análisis de partido | `/api/analysis`, `Analysis.tsx`: eficiencia, comparativa, cronología, ratings y archivo | PASS |
| Responsabilidades del staff | `/api/responsibilities`, `Responsibilities.tsx`: áreas, responsables y bonus de entrenamiento/ojeo | PASS |
| Desarrollo individual | `/api/development`, `Development.tsx`: foco, intensidad, progreso semanal y cantera | PASS |
| Premios y galardones | `/api/awards`, `Awards.tsx`: MVP, goleador, joven, portero, defensa, once ideal e historial | PASS |
| Centro de contratos | `/api/contracts`, `Contracts.tsx`: vencimientos, salarios, años, masa salarial y renovaciones | PASS |
| Instalaciones del club | `/api/facilities`, `Facilities.tsx`: estado, aforo, cantera, médico, vídeo, ojeo y mejoras | PASS |
| Cláusulas y primas | `/api/clauses`, `Clauses.tsx`: cláusula de rescisión, prima de renovación y protección | PASS |
| Lista de seguimiento | `/api/shortlist`, `Shortlist.tsx`: búsqueda, prioridad, notas, valor, contrato y petición | PASS |
| Planes de partido | `/api/match-plans`, `MatchPlans.tsx`: situación, minuto, instrucciones y efecto en el motor | PASS |
| Perfil y carrera del mánager | `/api/manager`, `ManagerProfile.tsx`: récord, palmarés, hitos, temporadas y situación actual | PASS |
| Mocap CMU | Clip de carrera CMU subject 9 trial 1, 74 frames a 60 fps, licencia y atribución en `assets/mocap`; aplicado a piernas/cadera | PASS |
| Comparación de jugadores | `/api/compare`, `Compare.tsx`: atributos, estadísticas, contrato, diferencias y resumen | PASS |
| E2E Playwright | calendario, amistosos, visor 3D con biomecánica/tejido/mocap CMU, revisión de vídeo, junta, cesiones, data hub, afiliados, mentoring, historial, ojeo, reunión, arbitraje subjetivo, ventaja con retorno, gol anulado por pie/revés/mano, gol solo desde el círculo, plantillas limpias, pulido de mercado/calendario/tácticas, finanzas, análisis, responsabilidades, desarrollo, premios, contratos, instalaciones, cláusulas, seguimiento, planes de partido, perfil del mánager, comparación, pruebas, trabajo y seguridad, cambio entre ligas e internacional, vacantes, cambios de entrenador, despido del usuario, prensa y marcas | PASS |
| Persistencia | `GameState` serializa amistosos, marcas, media, equipación, seguimiento y planes de partido; `persistence` limpia staff de partidas antiguas | PASS |

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
15. `test_api_team_meeting`
16. `test_api_finance_overview_and_ticket`
17. `test_api_analysis_overview_and_archive`
18. `test_api_report_has_added_time_and_discipline_stats`
19. `test_api_live_protest_once_per_match`
20. `test_api_responsibilities_assignment`
21. `test_api_development_plan`
22. `test_api_awards_overview`
23. `test_api_contracts_overview`
24. `test_api_facilities_overview_and_upgrade`
25. `test_api_clauses_update`
26. `test_api_shortlist_add_update_remove`
27. `test_api_match_plans_create_update_delete`
28. `test_api_manager_profile_and_career_record`
29. `test_api_compare_players`
30. `test_api_jobs_generate_accept_and_reject`
31. `test_api_trials_invite_and_end`
32. `test_api_cross_league_job_pending`
33. `test_api_international_job_pending`
34. `test_api_vacancies_apply`
35. `test_api_live_disallowed_goal_review`
36. `test_api_vacancies_include_manager_market`
37. `test_api_user_resign_and_rehire`

`src/tests/test_referee_discretion.py`:

- `test_advantage_keeps_possession_and_is_recorded`
- `test_dangerous_play_is_recorded_and_can_award_pc`
- `test_five_meters_is_enforced_on_free_hit`
- `test_pc_can_be_denied_by_referee`
- `test_dangerous_play_can_upgrade_pc_to_stroke`

`src/tests/test_referee_subjective.py`:

- `test_dangerous_play_severity_can_force_card`
- `test_dangerous_play_careless_can_avoid_card`
- `test_free_hit_can_be_advanced_ten_meters`
- `test_penalty_corner_can_be_retaken`
- `test_penalty_stroke_can_be_retaken`

`src/tests/test_referee_advantage.py`:

- `test_advantage_failure_brings_back_free_hit`
- `test_advantage_failure_in_circle_awards_penalty_corner`
- `test_advantage_success_clears_pending_without_failure`

`src/tests/test_goal_disallowed.py`:

- `test_goal_disallowed_for_foot_records_event_and_stats`
- `test_goal_disallowed_for_back_stick_via_shot`
- `test_disallowed_goal_only_reviewable_by_attacking_team`
- `test_review_overturns_disallowed_goal_and_awards_it`
- `test_review_upheld_disallowed_goal_consumes_referral`
- `test_disallowed_goal_stats_and_event_reach_match_result`
- `test_shot_from_outside_circle_cannot_score`
- `test_outside_circle_deflection_is_allowed`
- `test_goal_inside_circle_is_allowed`
- `test_review_overturns_outside_circle_disallowed_goal`
- `test_outside_circle_disallowed_goal_reaches_match_result`
- `test_goal_disallowed_for_hand_records_event_and_stats`
- `test_shot_can_disallow_goal_for_hand`
- `test_review_overturns_hand_disallowed_goal`
- `test_hand_disallowed_goal_reaches_match_result`

`src/tests/test_vacancies.py`:

- `test_vacancy_overview_has_candidates_and_summary`
- `test_apply_vacancy_accepted_creates_offer`
- `test_apply_vacancy_rejected_records_application`
- `test_vacancy_validation_duplicate_and_persistence`

`src/tests/test_managers.py`:

- `test_manager_names_initialized_from_staff_or_interim`
- `test_bottom_team_pressure_leads_to_sack`
- `test_sacked_team_appears_as_vacancy_and_history`
- `test_manager_changes_persist`
- `test_user_team_is_not_automatically_sacked`
- `test_job_acceptance_updates_manager_names`

`src/tests/test_squad_cleanup.py`:

- `test_first_teams_have_no_guest_players_and_minimum_roster`
- `test_guests_move_to_market_with_origin_team`
- `test_wage_budget_matches_cleaned_squad`

`src/tests/test_user_sacking.py`:

- `test_user_sacking_after_pressure`
- `test_user_sacking_requires_repeated_pressure`
- `test_user_sacking_persists`
- `test_resign_user_sets_sacked`
- `test_accept_job_after_sacking_clears_flag`
- `test_cross_league_offer_blocked_while_sacked`

`src/tests/test_jobs.py`:

- `test_job_security_overview_has_status_and_contract`
- `test_generate_job_offers_same_league_and_excludes_user`
- `test_accept_job_offer_switches_club_and_persists`
- `test_reject_job_offer_records_history`
- `test_job_offer_validation_and_same_league_guard`
- `test_generate_cross_league_offers`
- `test_accept_cross_league_offer_sets_pending_without_switching`
- `test_pending_job_applies_on_next_season_and_rebuilds_fixtures`
- `test_generate_international_offers`
- `test_accept_international_offer_sets_pending_without_switching`
- `test_pending_international_job_applies_on_next_season`

`src/tests/test_trials.py`:

- `test_trial_overview_has_candidates_and_empty_state`
- `test_invite_and_end_trial_generates_report`
- `test_trial_limits_and_validation`
- `test_advance_trials_completes_when_end_date_arrives`

`src/tests/test_finance_overview.py`:

- `test_finance_overview_has_breakdown_projection_and_earners`
- `test_finance_ticket_price_updates_and_persists`

`src/tests/test_analysis.py`:

- `test_analysis_overview_has_metrics_timeline_and_players`
- `test_analysis_can_open_archived_match`

`src/tests/test_referee_discipline.py`:

- `test_protest_warning_records_dissent_without_card`
- `test_protest_can_draw_card`
- `test_unsportsmanlike_delay_and_simulation`
- `test_added_time_is_computed_and_in_result`

`src/tests/test_live_protest.py`:

- `test_live_protest_respectful_is_one_per_team`
- `test_live_protest_vehement_can_draw_card`

`src/tests/test_responsibilities.py`:

- `test_responsibilities_overview_has_areas_and_staff`
- `test_responsibility_assignment_and_bonus`
- `test_responsibility_validation_and_persistence`

`src/tests/test_development.py`:

- `test_development_overview_has_players_and_focuses`
- `test_development_plan_progresses_and_gains_attributes`
- `test_development_validation_and_clear`

`src/tests/test_awards.py`:

- `test_season_awards_and_best_xi`
- `test_awards_overview_includes_last_match_and_history`

`src/tests/test_contracts.py`:

- `test_contracts_overview_has_summary_and_candidates`
- `test_contracts_persist_contract_dates`

`src/tests/test_facilities.py`:

- `test_facilities_overview_has_levels_and_upgrades`
- `test_facility_upgrade_and_persistence`

`src/tests/test_clauses.py`:

- `test_clauses_overview_has_suggestions_and_summary`
- `test_set_clause_deducts_bonus_and_persists`
- `test_clause_validation`

`src/tests/test_shortlist.py`:

- `test_shortlist_starts_empty_and_has_candidates`
- `test_add_update_and_remove_shortlist_entry`
- `test_shortlist_validation_and_persistence`

`src/tests/test_match_plans.py`:

- `test_match_plans_overview_has_options_and_empty_state`
- `test_create_update_delete_match_plan_and_persist`
- `test_match_plan_validation_and_limit`
- `test_engine_applies_plan_only_when_situation_and_minute_match`
- `test_engine_ignores_disabled_plan_and_other_side`

`src/tests/test_manager_profile.py`:

- `test_manager_profile_has_current_status_and_empty_record`
- `test_manager_profile_counts_played_matches`
- `test_manager_profile_trophies_milestones_and_persistence`

`src/tests/test_mocap_asset.py`:

- `test_mocap_asset_has_verified_license_and_source`
- `test_mocap_clip_has_frames_and_metadata`

`src/tests/test_compare.py`:

- `test_compare_candidates_returns_players_and_filters`
- `test_compare_players_has_attributes_categories_and_summary`
- `test_compare_validation`

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

`src/tests/test_scouting.py`:

- `test_scout_recommendations_respect_budget_quality_and_needs`
- `test_scout_recommendations_have_relative_scores`

`src/tests/test_scouting_assignments.py`:

- `test_scouting_overview_has_assignment_options`
- `test_create_assignment_and_complete_report`
- `test_assignment_limit_and_validation`
- `test_scouting_assignments_persist`

`src/tests/test_team_meeting.py`:

- `test_team_meeting_context_has_dynamics_and_options`
- `test_team_meeting_applies_effects_and_history`
- `test_team_meeting_creates_persistent_promise`
- `test_team_meeting_validation_and_failure`

## Comandos ejecutados

```text
python3 -m pytest src/tests -q
341 passed in 298.72s

cd manager/web/frontend && npm run build
✓ built in 3.48s

curl /api/health → 200
curl /app → 200
curl /static/react/assets/index-lWg4mnvP.js → 200

node web/frontend/e2e_beta.mjs
{"newGame":true,"calendar":true,"monthNavigation":true,"quickMatch":true,"refereeAndSetPieces":true,"refereeDiscretion":true,"refereeDiscipline":true,"refereeSubjective":true,"refereeAdvantage":true,"goalDisallowed":true,"goalOutsideCircle":true,"goalHand":true,"analysis":true,"postPress":true,"viewerBiomechanics":{"biomechSolutions":3696,"clothUpdates":1848},"viewerMocap":{"source":"CMU-09-01","frames":74,"applied":1848},"liveProtest":true,"viewer3d":true,"viewerMaterials":{"stickBodyCollisions":16,"materialBounces":93,"stickFlexes":51},"viewerSkeleton":{"bones":374,"sticks":22,"ikSolutions":3696},"viewerPhysics":{"frames":84,"playerCollisions":0,"bodyCollisions":10,"stickCollisions":12,"ballSpeed":1.45},"videoReview":true,"videoReviewType":"penalty_corner","boardRequest":true,"loans":true,"datahub":true,"affiliates":true,"mentoring":true,"history":true,"scouting":true,"teamMeeting":true,"finance":true,"responsibilities":true,"development":true,"awards":true,"contracts":true,"facilities":true,"clauses":true,"shortlist":true,"matchPlans":true,"managerProfile":true,"compare":true,"trials":true,"playerBrands":true,"jobs":true,"crossLeagueJob":true,"internationalJob":true,"vacancies":true,"managerChanges":true,"userSacking":true}
```

## Límites conscientes

La beta ya tiene una capa de gestión mucho más amplia, pero no se presenta como una réplica completa de Football Manager 24. Las siguientes piezas de mayor valor serían:

- revisión de vídeo con interpretación arbitral completa (solo están modeladas las decisiones revisables);
- física 3D AAA (tejido, materiales, captura de movimiento);
- paridad total de pantallas y bases de datos de FM24;
- auditoría visual de fotos de jugadores (la incidencia principal era el staff cargado como plantilla).
