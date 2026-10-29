# Divisiones autonómicas, agentes libres y ratings

**Estado:** actualizado (2026-10-28).

## 1. Cobertura actual

La base ya no se limita a 24 equipos: se han incorporado los 59 equipos regionales del Excel, incluidos los filiales, y se han separado sus plantillas.

- Equipos regionales documentados: **59**.
- Ligas regionales jugables: **8** (1N, 1A, 1M, 1G, 1C, 1V, Superlliga y Primera Catalana).
- Segundos equipos o filiales: **26**.
- Jugadores en la base completa: **2.409**.
- Agentes libres al iniciar una partida DHA/DHB: **1.460**.
- Duplicados por nombre entre equipos: **0**.

Los jugadores de divisiones autonómicas siguen apareciendo como agentes libres en partidas DHA/DHB. En partidas regionales pertenecen a su equipo y no se duplican en el mercado.

## 2. Fuentes

- **iSquad/RFEH:** DHA, DHB, Liga Norte, Andalucía, Madrid, Galicia y Canarias. Se comprobó la categoría `MASC.` de cada ficha para descartar equipos femeninos.
- **FHCV:** 1ª División Valenciana, mediante actas PDF oficiales de 2026-27 y 2025-26.
- **FCH:** Superlliga Catalana y Primera Catalana, mediante calendario y actas de partido.
- **Excel de equipos:** `equipos_hockey_hierba_espana_masculino_2026_27.xlsx`, hojas `Equipos únicos`, `Filiales excluidos`, `Resumen por liga` y `Fuentes`.

La auditoría completa, con el detalle de las 10 ligas y las URLs, está en `38_AUDITORIA_EQUIPOS_Y_PLANTILLAS.md` y en `manager/data/audit_rosters_2026_27.json`.

## 3. Estimación de posiciones

iSquad no publica posición individual en todas las plantillas autonómicas; FHCV/FCH publican convocatorias, no siempre la posición. Se mantiene una estimación determinista:

- 2 porteros por plantilla cuando hay 16 o más jugadores;
- 28 % defensas;
- 28 % medios;
- resto delanteros;
- central/lateral según hash estable de nombre y equipo.

Los jugadores con más goles se ordenan antes en las posiciones ofensivas. La fuente queda marcada como `Estimada` y confianza `Baja`.

## 4. Ratings actuales y escalera de niveles

| Liga | Media | Rango de medias por equipo |
|---|---:|---:|
| DHA | **74,80** | 67,86–78,88 |
| DHB | **64,00** | 60,23–67,53 |
| 1ª Andaluza | **56,11** | 53,92–60,22 |
| 1ª Autonómica Norte | **53,20** | 50,50–54,17 |
| 1ª Autonómica Madrid | **53,26** | 51,19–53,92 |
| 1ª Autonómica Galicia | **53,24** | 52,21–53,96 |
| 1ª Autonómica Canarias | **52,45** | 49,95–53,92 |
| 1ª Autonómica FHCV | **53,82** | 53,55–53,92 |
| Superlliga Catalana | **59,00** | 58,28–59,70 |
| Primera Catalana | **52,98** | 51,80–53,92 |

### Fronteras entre categorías

- **DHA → DHB:** el peor equipo de DHA queda en **67,86** y el mejor de DHB en **67,85**. La frontera es prácticamente exacta.
- **DHB → 1ª Andaluza:** el peor de DHB queda en **60,23** y el mejor de 1A en **60,22**.
- **1A → ligas regionales:** el peor de 1A queda en **53,92**; las ligas regionales paralelas se ajustan alrededor de ese corte (53,9–54,2). La Superlliga Catalana es la excepción: se coloca entre 1A y DHB, con media **59,00**.
- **San Fernando DHB:** media **62,96**; el filial B queda en **56,20** y no comparte jugadores con el primer equipo.
- **Pozuelo DHB:** media **64,89**.
- **RH Privé Benalmádena (1A):** media **60,22**.
- **CHP Benalmádena B (1A):** media **54,16**.

La fórmula de generación sigue siendo:

```text
base = base_liga
     + 12 * fuerza_equipo
     + 5 * percentil_goles
     + 5 * curva_edad
     + contexto DHB
     + ruido controlado
```

`fuerza_equipo` usa clasificaciones reales, no los goles de una categoría inferior. Después se aplica un desplazamiento por liga para fijar la media objetivo y un recorte por equipo para que el mejor equipo de una categoría no supere al peor de la superior.

### Casos históricos

- **Pozuelo:** media anterior 74,37; ahora 64,89. Está en DHB y no se le infla por goles de una categoría inferior.
- **San Fernando DHB:** media 62,96; su filial B queda en 56,20. La separación de invitados/staff dejó al primer equipo con 15 jugadores oficiales y al B con 27.
- **Benalmádena:** el primer equipo queda en 60,22; su filial B, en 54,16. Ambos conviven en 1A sin repetir jugadores.
- **DHA:** los equipos punteros siguen por encima de DHB, pero sin mezclarse con los autonómicos.

## 5. Cómo aparecen en el juego

- En DHA/DHB: agentes libres con `origin_team` visible en mercado y ficha.
- En regional: jugadores del equipo, sin aparecer como agentes libres.
- Los equipos B tienen nombre propio (`CHP BENALMÁDENA B`, `POZUELO B`, etc.) y comparten liga con su primer equipo cuando corresponde.
- Los escudos reales se cargan desde `manager/web/static/crests/{team_id}.png`.

## 6. Archivos

- `tools/lower_divisions_players.csv`: plantillas regionales normalizadas.
- `tools/todos_manifest_positions.csv`: plantillas base DHA/DHB/1A.
- `tools/player_attributes_v2.csv`: ratings y atributos finales.
- `tools/build_attributes_v2.py`: generación, escalera de niveles y fronteras entre categorías.
- `tools/sync_isquad_base_rosters.py`: sincronización DHA/DHB.
- `tools/sync_second_teams.py`: equipos B y deduplicación.
- `tools/fetch_fch_rosters.py`: actas catalanas.
- `tools/fetch_fhcv_rosters.py`: actas valencianas.
- `tools/fetch_all_regional_crests.py`: escudos.
- `manager/data/audit_rosters_2026_27.json`: auditoría reproducible.

## 7. Pendiente

- Revisar posiciones individuales de San Fernando B cuando se publiquen actas con demarcación.
- Hacer interactiva la fase de ascenso regional.
- Validar posiciones individuales con fuentes federativas cuando estén publicadas.
- Revisar permisos de uso de los escudos oficiales.
