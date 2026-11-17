# Cobertura y E2E

## Cobertura

Configuración en `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["manager/src", "manager/web"]
omit = ["src/tests/*", "*/__pycache__/*"]
```

Comando:

```bash
cd manager
python3 -m pytest src/tests -q --cov=src --cov=web --cov-report=term
```

Resultado con 351 tests:

```text
TOTAL                     14741   3778    74%
```

El 74% incluye los entrypoints legacy de consola (`src/ui.py`, `src/main.py`,
`src/prototype.py`), que no usa la web. Sin ellos:

```text
TOTAL                     13173   2210    83%
```

Módulos críticos:

| Módulo | Cobertura |
| --- | --- |
| `match_engine.py` | 97% |
| `match_referee.py` | 94% |
| `match_scoring.py` | 97% |
| `match_simulation.py` | 90% |
| `match_tactics.py` | 96% |
| `season.py` | 91% |
| `season_sim.py` | 88% |
| `season_promotion.py` | 56% |
| `persistence.py` | 90% |
| `web/api/common.py` | 93% |
| `web/api/press.py` | 83% |
| `web/app.py` | 69% |

El CI ejecuta la misma medición en `docs/ci_workflow.yml`.

## E2E dividido

Antes había un único flujo largo. Ahora hay tres suites independientes:

```bash
cd manager/web/frontend
npm run test:e2e:smoke   # health, onboarding, calendario, plantilla, táctica, mercado, partido rápido, informe, análisis
npm run test:e2e:live    # partido en directo, visor 3D, protesta, avance de momentos
npm run test:e2e:i18n    # inglés en plantilla, mercado, táctica, previa, informe y ajustes
npm run test:e2e         # regresión completa de 50+ flujos
npm run test:e2e:all     # las cuatro en orden
```

Cada suite crea su propia partida con semilla distinta, así que un fallo se
aísla sin arrastrar el estado de las demás.

### Evidencia

Smoke:

```json
{"health":true,"newGame":true,"onboarding":true,"dashboard":true,"calendar":true,"squad":true,"tactics":true,"market":true,"quickMatch":true,"report":true,"analysis":true,"i18nEnglish":true,"i18nPersisted":true,"i18nSpanish":true,"ok":true,"suite":"smoke","ms":6341}
```

Live:

```json
{"liveStart":true,"viewer":{"players":22,"frames":79,"bones":374,"sticks":22,"ikSolutions":3476,"biomechSolutions":3476,"mocapFrames":74},"viewer3d":true,"momentum":"0","audioToggle":true,"liveProtest":true,"momentsAdvanced":true,"finished":true,"ok":true,"suite":"live","ms":21313}
```

i18n:

```json
{"options":true,"squad":true,"market":true,"tactics":true,"match":true,"report":true,"spanishRestored":true,"ok":true,"suite":"i18n","ms":6039}
```

Full:

```json
{"newGame":true,"calendar":true,"monthNavigation":true,"quickMatch":true,"refereeAndSetPieces":true,"refereeDiscretion":true,"refereeDiscipline":true,"refereeSubjective":true,"refereeAdvantage":true,"goalDisallowed":true,"goalOutsideCircle":true,"goalHand":true,"analysis":true,"postPress":true,"viewerBiomechanics":{"biomechSolutions":3168,"clothUpdates":1584},"viewerMocap":{"source":"CMU-09-01","frames":74,"applied":1584},"liveProtest":true,"viewer3d":true,"viewerMaterials":{"stickBodyCollisions":16,"materialBounces":69,"stickFlexes":77},"viewerSkeleton":{"bones":374,"sticks":22,"ikSolutions":3168},"viewerPhysics":{"frames":72,"playerCollisions":0,"bodyCollisions":59,"stickCollisions":43,"ballSpeed":2.31},"videoReview":true,"videoReviewType":"penalty_corner","boardRequest":true,"loans":true,"datahub":true,"affiliates":true,"mentoring":true,"history":true,"scouting":true,"teamMeeting":true,"finance":true,"responsibilities":true,"development":true,"awards":true,"contracts":true,"facilities":true,"clauses":true,"shortlist":true,"matchPlans":true,"managerProfile":true,"compare":true,"trials":true,"playerBrands":true,"jobs":true,"crossLeagueJob":true,"internationalJob":true,"vacancies":true,"managerChanges":true,"userSacking":true}
```

## Límites

- `season_promotion.py` (56%) concentra las fases de ascenso y Final Four;
  tiene tests de integración, pero aún no de cada rama.
- La cobertura de los blueprints de API es 58–83%: los flujos principales
  están cubiertos, las variantes de error no todas.
- El E2E sigue dependiendo de Chromium local (`CHROME_PATH` o caché de
  Playwright); no se ejecuta en CI hasta activar el workflow.
