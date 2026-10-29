# Sistema de ascenso de Primera División a DHB

**Estado:** implementado (2026-10-28).

## Fuente oficial

- **RFEH, Circular nº1 2026-27**, apartado 1.3 «Ascensos y descensos» y calendario de la «Primera División Masculina – Fase de ascenso D.H.B»:
  <https://eshockey.es/download/240/circulares-1-rfeh/25288/1-circular-1-2026-2027.pdf>
- **RFEH, Semifinales de la Fase Final de ascenso a DHB (2026)**:
  <https://eshockey.es/semifinales-de-la-fase-final-de-ascenso-a-division-de-honor-b/>

La circular establece dos fases: una **Fase Autonómica** y una **Fase Nacional**. La Fase Nacional se disputa en tres fines de semana (fases previas, semifinales y final) y los **dos primeros de la Fase Final ascienden a DHB**. En 2026 la fase nacional reunió a **16 equipos en cuatro sedes/grupos**; los campeones de cada grupo jugaron una **liguilla final de cuatro** y los dos primeros subieron. Todos los partidos se juegan a partido único.

## Modelo del juego

### 1. Clasificación autonómica

Cada liga regional jugable termina su liga regular. Para la fase nacional se clasifican los **dos primeros** de cada liga:

| Grupo | Ligas que lo alimentan |
| --- | --- |
| Grupo Norte | 1ª Norte y 1ª Galicia |
| Grupo Sur | 1ª Andaluza y 1ª Canarias |
| Grupo Levante | 1ª Madrid y 1ª FHCV |
| Grupo Cataluña | Superlliga Catalana y Primera Catalana |

Esta agrupación es una simplificación geográfica del modelo oficial: la circular permite que las federaciones acuerden sedes y competiciones interautonómicas, por lo que la composición exacta puede variar cada temporada. El juego mantiene cuatro grupos de cuatro equipos para que todas las ligas jugables tengan representación.

### 2. Fase de grupos

Cada grupo disputa una liguilla **a partido único** (todos contra todos, tres jornadas). El campeón de cada grupo pasa a la fase final. Los desempates son puntos, diferencia de goles, goles a favor y nombre del equipo.

### 3. Fase final

Los cuatro campeones de grupo disputan otra liguilla **a partido único**. Los **dos primeros ascienden a DHB**. No hay final a partido único: el campeón es el primero de esta liguilla.

### 4. Descensos y equilibrio de la pirámide

- Los **dos últimos de DHB** descienden a la liga autonómica de su comunidad.
- Cuando el usuario juega en regional, los dos últimos de DHB también bajan y se calculan con una simulación de fondo de la DHB.
- Los dos primeros de la fase final autonómica suben a DHB; los dos últimos de DHA bajan a DHB y los dos primeros de DHB suben a DHA. Así se mantienen **12 equipos en DHA y 16 en DHB**.

La asignación de un descendido de DHB a su liga regional se hace por comunidad autónoma (`regional_league_for`). Si no hay correspondencia, se usa 1ª Andaluza como destino de seguridad.

## Implementación

- `manager/src/season.py`:
  - `REGIONAL_PROMOTION_GROUPS`: cuatro grupos y sus ligas.
  - `_play_promotion_group`: liguilla a partido único y tabla.
  - `_finish_regional_season`: fase autonómica + fase nacional + ascensos.
  - `_background_dhb_relegated`: descensos de DHB en partidas regionales.
  - `regional_league_for`: destino autonómico de un descendido.
- `manager/src/promotion.py`: calcula el camino de ascenso, los objetivos y la clasificación de todas las ligas regionales.
- `manager/web/frontend/src/pages/Promotion.tsx`: pestaña de fase de ascenso con objetivos, grupos, liguilla final y noticias.
- `manager/web/frontend/src/pages/SeasonEnd.tsx`: muestra los cuatro grupos, la liguilla final y las dos plazas de ascenso.
- `manager/src/tests/test_regional_leagues.py`: comprueba cuatro grupos, seis partidos por grupo, liguilla final y dos ascensos.

## Limitaciones

- La composición exacta de los cuatro grupos oficiales puede cambiar por acuerdo entre federaciones; el juego usa zonas geográficas estables.
- Las ligas autonómicas que no juega el usuario se simulan con el potencial de sus plantillas para poder resolver la fase nacional y los movimientos de la pirámide.
- La fase de ascenso se resuelve automáticamente al terminar la liga regular; no hay una pantalla de eliminatorias interactiva.
