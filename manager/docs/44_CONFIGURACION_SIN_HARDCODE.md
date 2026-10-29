# Configuración de ligas sin hardcode

**Estado:** implementado (2026-10-28).

## Principio

Ninguna liga, club o comunidad tiene una excepción escrita dentro del motor.
La configuración vive en datos y los sistemas de competición se seleccionan por
el campo `system` de cada competición.

## Fuentes de datos

- `manager/data/competitions.json`: nombre, país, nivel, fechas, número de
  equipos, formato, sistema, zona de ascenso y rondas regulares de las 16
  competiciones.
- `manager/data/league_rules.json`: reglas transversales (fechas de la fase
  nacional, plazas de ascenso, mínimo de plantilla, mínimo de alineación y liga
  regional de respaldo).
- `manager/data/regional_teams.json`: equipos, comunidad, ciudad y estadio de
  las ligas autonómicas.
- `manager/data/ehl.json`: participantes europeos, calendario y etiquetas de la
  EHL.
- `manager/data/cup.json`: formato, fases, fechas y activación de la Copa.

## Clases

`manager/src/league_systems.py` contiene:

- `LeagueSystem`: contrato común para construir calendario y clasificación.
- `DoubleRoundRobinSystem`.
- `RegionalLeagueSystem`.
- `InternationalLeagueSystem`.
- `DHASystem`.
- `DHBTwoPhaseSystem`.
- `LeagueWorld`: orquesta todas las ligas de un `GameState`.

`competitions.py` solo carga y valida los JSON. `season.py` usa
`competition(code).system` y `promotion_groups()`; no contiene listas de clubes
ni mapas de comunidades.

## Destino de un descendido

`regional_league_for(team, state)` busca clubes reales de la misma comunidad en
las ligas regionales y elige la competición de mayor nivel. Si no hay
representación, usa `default_regional_league` de `league_rules.json`.

## Mercado y plantillas

`_seed_free_agents` no protege clubes concretos:

1. Conserva todos los jugadores con perfil `Jugador`.
2. Los `Invitado` pasan al mercado.
3. Si un club queda por debajo del mínimo de alineación, se completa con el
   mercado real priorizando su liga y el nivel más bajo.
4. El cuerpo técnico no se mezcla con jugadores.
5. La deduplicación global conserva una sola ficha por jugador.

San Fernando y Pozuelo no tienen ninguna excepción: sus plantillas se cargan
como las del resto de clubes.
