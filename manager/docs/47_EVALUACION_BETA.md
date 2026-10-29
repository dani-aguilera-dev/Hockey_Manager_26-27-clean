# Evaluación de la beta avanzada

**Fecha:** 2026-10-29  
**Rama:** `main`  
**Commit de la actualización:** `49bb4df`

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
| Backend | `python3 -m pytest src/tests -q` → **165 passed** | PASS |
| Frontend | `npm run build` → SPA compilada sin errores TypeScript | PASS |
| Servidor web | `/api/health` 200; `/app` 200; asset React 200 | PASS |
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

## Comandos ejecutados

```text
python3 -m pytest src/tests -q
165 passed in 272.26s

cd manager/web/frontend && npm run build
✓ built in 3.68s

curl /api/health → 200
curl /app → 200
curl /static/react/assets/index-Bu3vFlBz.js → 200
```

## Límites conscientes

La beta ya tiene una capa de gestión mucho más amplia, pero no se presenta como una réplica completa de Football Manager 24. Las siguientes piezas de mayor valor serían:

- rueda de prensa posterior al partido;
- vista mensual de calendario con drag-and-drop;
- contratos individuales de imagen con marcas;
- más animaciones y eventos únicos de hockey;
- auditoría visual de fotos de jugadores (la incidencia principal era el staff cargado como plantilla).
