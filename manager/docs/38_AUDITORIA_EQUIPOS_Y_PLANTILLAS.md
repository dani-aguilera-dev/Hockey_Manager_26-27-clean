# Auditoría de equipos y plantillas 2026-27

**Fecha:** 2026-10-28  
**Alcance:** DHA, DHB, 1N, 1A, 1M, 1G, 1C, 1V, Superlliga Catalana y Primera Catalana.  
**Objetivo:** comprobar liga a liga que están todos los equipos, que las plantillas son masculinas, que no hay jugadores repetidos y que los equipos B conviven con su primer equipo.

## Resultado global

| Liga | Equipos esperados | Equipos en el juego | Jugadores | Fuente principal |
|---|---:|---:|---:|---|
| DHA | 12 | 12 | 492 | iSquad + Excel |
| DHB | 16 | 16 | 429 | iSquad + Excel |
| 1N | 10 | 10 | 250 | iSquad + Excel |
| 1A | 8 | 8 | 232 | iSquad + Excel |
| 1M | 9 | 9 | 222 | iSquad + Excel |
| 1G | 6 | 6 | 164 | iSquad + Excel |
| 1C | 3 | 3 | 65 | iSquad + Excel |
| 1V | 7 | 7 | 155 | FHCV (actas PDF) + Excel |
| Superlliga | 8 | 8 | 231 | FCH (actas) + Excel |
| Primera Catalana | 8 | 8 | 169 | FCH (actas) + Excel |
| **Total** | **87** | **87** | **2.409** | |

- **Duplicados por nombre entre equipos:** 0.
- **Equipos B o filiales documentados:** 26.
- **Escudos reales disponibles:** 59/59 equipos regionales.
- **San Fernando B:** 27 jugadores oficiales. Se separaron los 22 invitados que el primer equipo lista y se excluyeron delegados, entrenadores y fisioterapeutas. El primer equipo queda con 15 jugadores oficiales. No hay jugadores repetidos entre ambos.

## Ligas y fuentes

### DHA y DHB

- **Fuente 1:** fichas de equipo de iSquad. Se comprobó que la categoría seleccionada fuera `MASC.` y que la competición fuera DHA/DHB masculina.
- **Fuente 2:** `equipos_hockey_hierba_espana_masculino_2026_27.xlsx`, hojas `Equipos únicos` y `Filiales excluidos`.
- Se sustituyeron las plantillas antiguas por las convocatorias actuales de iSquad.
- Los filiales de DHB que compartían nombres con su primer equipo se limpiaron: el jugador se queda en el primer equipo.
- Ejemplos corregidos: `AD Rimas`, `Egara 1935`, `HC Sant Cugat`, `Pedralbes HC`, `SPV`, `Vallès Esportiu`, `Real Sociedad 1927`.

### Liga Norte, Andalucía, Madrid, Galicia y Canarias

- **Fuente 1:** iSquad, ficha de equipo con categoría y competición masculinas.
- **Fuente 2:** Excel de equipos únicos/filiales y, cuando existe, calendario federativo (por ejemplo, la Federación Madrileña).
- Se eliminaron fichas femeninas que el buscador de iSquad devolvía con el mismo nombre de categoría. Afectaba a Stick Getxo, Covadonga, DXT Sur, Hocquet, Ourensticks, Agonek y Aridaman.
- Se incorporaron los equipos B que faltaban:
  - 1N: Jolaseta B, RST Magdalena, Sardinero B.
  - 1A: San Fernando B, CHP Benalmádena B.
  - 1M: Las Rozas Azul, Las Rozas Blanco, Pozuelo B, Real Sociedad 1927 A, Real Sociedad 1927 B, Sanse Complutense B.
  - 1C: UD Taburiente B.

### Comunidad Valenciana (1V)

- **Fuente 1:** página oficial de la FHCV y actas PDF de la temporada 2026-27.
- **Fuente 2:** actas de la temporada 2025-26 y Excel de equipos/filiales.
- Equipos: CH Xaloc, Honigvögel HH'79, Valencia CH, Santomera HC, Hockey Salduie '78, CH Carpesa B y Valencia CH 1924.
- Las actas permiten recuperar la convocatoria completa; no se inventan edades ni posiciones: se estiman como en el resto de divisiones autonómicas.

### Cataluña (Superlliga y Primera Catalana)

- **Fuente 1:** calendario y actas de partido de la Federació Catalana de Hockey.
- **Fuente 2:** Excel de equipos únicos/filiales y la propia clasificación federativa.
- Superlliga: Pedralbes 1991, Atlètic Terrassa B, CD Terrassa B, Diagonal HC, Egara 1935 B, EHC, FC Barcelona B y Vallès Esportiu B.
- Primera Catalana: Barcelona Hockey Club, CHC, Matadepera 88, Atletic 1952, Can Salas, Club Egara B, HC Sant Cugat B y RC Polo B.
- `Egara 1935 B` y `Vallès Esportiu B` se han renombrado con sufijo B para que no colisionen con sus equipos de DHB, que tienen nombres casi idénticos.

## Segundos equipos y jugadores no repetidos

La regla aplicada es:

1. Se normaliza el nombre completo del jugador.
2. Se procesan primero los primeros equipos (DHA/DHB y equipos A).
3. Si un jugador aparece en el primer equipo y en un filial, se queda en el primero.
4. Los equipos B se completan solo con jugadores que no estén ya en otro equipo.
5. El mercado de agentes libres usa la misma clave, así que un jugador no puede ficharse dos veces por dos equipos.

Esto afecta a casos reales de iSquad, que a veces publica al mismo jugador en la ficha del primer equipo y en la del filial. La comprobación final está en `manager/data/audit_rosters_2026_27.json` y da **0 duplicados**.

## Escudos

Se descargaron escudos reales para los 59 equipos regionales:

- iSquad para los equipos con ficha RFEH;
- FHCV para los valencianos;
- FCH para los catalanes;
- escudo del club matriz cuando el filial comparte identidad visual.

Los archivos están en `manager/web/static/crests/{id}.png`. No se ha generado ningún escudo inventado para los equipos con fuente federativa.

## Comprobaciones automáticas

- `tools/audit_rosters.py` genera el JSON de auditoría.
- `manager/src/tests/test_regional_leagues.py` comprueba:
  - los 8 equipos de 1A, incluidos Benalmádena y Benalmádena B;
  - los 10 equipos de 1N;
  - que no hay nombres repetidos entre equipos regionales;
  - que las 8 ligas tienen el número de equipos configurado.
- `manager/src/tests/test_lower_divisions.py` comprueba los agentes libres y el orden de medias.

## Limitaciones y siguientes pasos

- San Fernando B queda con 27 jugadores oficiales; los invitados y el staff no cuentan como plantilla.
- La fase de ascenso regional sigue siendo automática; hacerla interactiva es el siguiente paso funcional.
- Las posiciones individuales de las ligas autonómicas siguen siendo estimadas: iSquad/FHCV/FCH no siempre publican la posición.
- Los ratings se recalculan con las plantillas nuevas y el ancla de San Fernando DHB; ver `36_DATOS_DIVISIONES_Y_RATINGS.md`.
