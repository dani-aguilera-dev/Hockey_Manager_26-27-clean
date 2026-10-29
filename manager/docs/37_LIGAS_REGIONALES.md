# Ligas regionales jugables

**Estado:** actualizado (2026-10-28).

## Ligas disponibles

Se pueden dirigir equipos de las ocho competiciones regionales del Excel:

- **1N** · Primera División Masculina - Liga Norte: **10 equipos, 18 jornadas**.
- **1A** · Primera División Andaluza: **8 equipos, 14 jornadas**.
- **1G** · Primera División Masculina - Galicia: **6 equipos, 10 jornadas**.
- **1M** · Primera División Masculina - Madrid: **9 equipos, 18 jornadas**.
- **1C** · Primera División Masculina - Canarias: **3 equipos, 6 jornadas**.
- **1V** · Primera División Masculina - FHCV: **7 equipos, 14 jornadas**.
- **SUP** · Superlliga Catalana Masculina: **8 equipos, 14 jornadas**.
- **CAT1** · Primera Catalana Masculina: **8 equipos, 14 jornadas**.

Total: **59 equipos**. Los equipos se cargan desde `manager/data/regional_teams.json`; las plantillas, desde `tools/lower_divisions_players.csv` y las actas federativas.

## Equipos B

La liga puede contener el primer equipo y su filial. Por ejemplo, en 1A están:

- **RH PRIVÉ BENALMÁDENA** (primer equipo).
- **CHP BENALMÁDENA B** (segundo equipo).

Y en 1N:

- **REAL CLUB JOLASETA B**.
- **RST MAGDALENA**.
- **SARDINERO HC B**.

Regla de integridad:

- un jugador solo puede pertenecer a un equipo;
- si iSquad lo publica en el primer equipo y en el filial, prevalece el primer equipo;
- el mismo nombre no puede estar en dos plantillas ni dos veces en el mercado.

## Formato

- Fase regular a doble vuelta.
- En ligas de 4 o más equipos: semifinales `1º vs 4º` y `2º vs 3º`.
- En ligas de 3 equipos: semifinal entre 2º y 3º, y final contra el 1º.
- En ligas de 2 equipos: final directa.
- El campeón de la fase de ascenso sube a DHB.
- La fase de ascenso se simula automáticamente al terminar la liga regular.
- El resumen de temporada muestra semifinales, final y ascendido.

## Integración

- `new_game` carga los equipos regionales solo cuando se dirige una liga regional.
- En partidas DHA/DHB los equipos regionales no son jugables y sus jugadores aparecen como agentes libres.
- En partidas regionales los jugadores pertenecen a sus equipos y no se duplican como agentes libres.
- El campeón regional pasa a DHB al continuar la temporada.
- Los equipos B conservan su identidad y su escudo, pero comparten club matriz.
- Los equipos sin plantilla pública no se rellenan con nombres inventados.

## Cobertura y fuentes

| Liga | Equipos | Plantilla | Fuente |
|---|---:|---|---|
| 1N | 10 | 250 | iSquad + Excel |
| 1A | 8 | 214 | iSquad + Excel |
| 1M | 9 | 222 | iSquad + Excel |
| 1G | 6 | 164 | iSquad + Excel |
| 1C | 3 | 65 | iSquad + Excel |
| 1V | 7 | 155 | FHCV (actas) + Excel |
| SUP | 8 | 231 | FCH (actas) + Excel |
| CAT1 | 8 | 169 | FCH (actas) + Excel |

La auditoría detallada está en `38_AUDITORIA_EQUIPOS_Y_PLANTILLAS.md`.

## Archivos

- `manager/src/regional.py`: carga de equipos y metadatos.
- `manager/data/regional_teams.json`: equipos regionales.
- `tools/lower_divisions_players.csv`: plantillas normalizadas.
- `manager/src/season.py`: fase regular, eliminatorias y ascenso.
- `manager/src/competitions.py`: códigos y configuración regional.
- `tools/fetch_fch_rosters.py`: actas catalanas.
- `tools/fetch_fhcv_rosters.py`: actas valencianas.
- `tools/fetch_all_regional_crests.py`: escudos.

## Pendiente

- Hacer interactiva la fase de ascenso (semifinal y final jugables).
- Revisar posiciones individuales de San Fernando B cuando se publiquen actas con demarcación.
- Completar el formato de ascenso con plazas múltiples si la federación lo confirma.
