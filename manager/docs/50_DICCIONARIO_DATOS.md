# Diccionario de datos

Este documento fija qué significa cada dato de plantilla. Sirve para evitar
errores como tratar `Invitado` como si fuera staff o un trialista y borrarlo
del equipo.

## Perfiles de plantilla

| Perfil | Significado | Se conserva en el equipo |
| --- | --- | --- |
| `Jugador` | Jugador oficial de la plantilla según la fuente. | Sí |
| `Invitado` | Perfil de la fuente para jugadores invitados/auxiliares. **No es staff y no es un trialista del mercado.** | **Sí, siempre** |
| `Delegado Equipo` | Cuerpo técnico. Nunca se carga como jugador. | Va a `staff`. |
| `Entrenador` | Cuerpo técnico. Nunca se carga como jugador. | Va a `staff`. |
| `Fisioterapeuta` | Cuerpo técnico. | Va a `staff`. |
| `Preparador Fisico` | Cuerpo técnico. | Va a `staff`. |
| `Médico` / `Medico` | Cuerpo técnico. | Va a `staff`. |
| `Psicólogo` / `Psicologo` | Cuerpo técnico. | Va a `staff`. |

## Campos de jugador

| Campo | Significado |
| --- | --- |
| `id` | Identificador estable del jugador. |
| `name` | Nombre visible. |
| `team_name` | Equipo actual. `Agente libre` si está en el mercado. |
| `origin_team` | Equipo de procedencia para el mercado y los informes. |
| `league` | Categoría actual. |
| `position_group` | Portero, Defensa, Medio, Delantero o Polivalente. |
| `subposition` | Puesto específico: Portero, Central, Lateral, Medio, Delantero… |
| `overall` | Nivel actual 0–100. |
| `potential` | Techo estimado 0–100. |
| `attributes` | 37 atributos de hockey. |
| `perfil` | `Jugador` o `Invitado`. |
| `photo` / `photo_remote` | Foto local/remota. |
| `value` / `salary` | Valor de mercado y salario. |
| `contract_until` | Fecha de fin de contrato. |

## Reglas de integridad

1. Ningún miembro del staff puede aparecer como jugador.
2. `Invitado` se conserva en su equipo; no se mueve automáticamente al mercado.
3. Un jugador no puede estar en dos equipos ni dos veces en el mercado.
4. Los equipos B no pueden repetir jugadores del primer equipo.
5. Las edades fuera de 10–75 son error; por encima de 50 son aviso.
6. Los grupos posicionales deben ser válidos.
7. Los clubes DHA/DHB deben tener al menos 11 jugadores.

## Validación

```bash
cd manager
python3 -m src.data_validation
```

El informe devuelve `ok`, errores, avisos e información. Los avisos no bloquean
la partida; los errores sí deberían corregirse antes de publicar datos.

## Persistencia

- Los saves nuevos se guardan como JSON comprimido con zlib.
- Los saves antiguos en texto se siguen leyendo.
- `compact_saves()` convierte los antiguos y ejecuta `VACUUM`.
- La base de datos de referencia pasó de 1,3 GB a 198 MB con 190 partidas.
