# Staff y cuerpo técnico

**Estado:** implementado (2026-10-21).

## 1. Fuente

El cuerpo técnico se extrae de las fichas de equipo de iSquad:

```text
https://resultadoshockey.isquad.es/equipo.php?id_equipo=...
```

El script `tools/fetch_isquad_staff.py`:

1. Localiza cada club por el `team_url` del CSV de jugadores.
2. Descarga la ficha del equipo.
3. Extrae las filas de staff y sus roles.
4. Normaliza los roles a los roles internos del juego.
5. Genera `manager/data/staff_isquad.json`.

Roles detectados en iSquad:

- Entrenador
- Preparador físico
- Fisioterapeuta
- Psicólogo
- Delegado de equipo
- Médico
- Staff adicional
- Entrenador de porteros
- Analista
- Director deportivo

## 2. Reglas de conversión

- El **primer Entrenador** se guarda como `head_coach`.
- Los siguientes entrenadores se guardan como `assistant`.
- Los roles duplicados de la misma persona se deduplican por rol + nombre.
- La fuente queda marcada como `iSquad` y la confianza como `media`.
- Los salarios y ratings son estimaciones internas a partir del rol y del club.

## 3. Equipo gestionado por el usuario

Cuando el usuario dirige un club:

- su **entrenador** no aparece como miembro externo;
- en la pantalla de Staff aparece **Tú** como entrenador;
- el resto del staff real sí aparece;
- el entrenador del club se oculta en el perfil del equipo.

Así no hay dos entrenadores compitiendo por el mismo puesto.

## 4. Dónde se ve

- **Staff**: cuerpo técnico del club del usuario y junta directiva.
- **Perfil de equipo**: cuerpo técnico completo de cualquier club, con entrenador y staff real.
- **Staff de equipo**: roles, nombre, fuente y rating.

Los equipos que antes no tenían staff ahora tienen al menos un entrenador.

## 5. Compatibilidad con partidas antiguas

`_backfill_staff` rellena:

- el entrenador que falte en clubes con staff antiguo;
- el cuerpo técnico completo en clubes que estaban vacíos.

No elimina staff contratado por el usuario; solo añade lo que falta.

## 6. Archivos

```text
manager/data/staff_isquad.json
tools/fetch_isquad_staff.py
manager/src/data_loader.py
manager/src/persistence.py
manager/web/app.py
manager/web/templates/staff.html
manager/web/templates/team.html
manager/src/tests/test_phase4.py
manager/src/tests/test_persistence.py
```

## 7. Pruebas

```bash
cd manager
python3 -m pytest src/tests -q
```

Comprueba:

- todos los equipos activos tienen entrenador;
- las partidas antiguas recuperan staff;
- el perfil del equipo muestra cuerpo técnico;
- el club del usuario muestra “Tú” y oculta el entrenador externo.

Resultado actual: **80 tests superados**.

## 8. Limitaciones

- iSquad no siempre distingue primer entrenador y ayudantes; el orden de la ficha se usa como criterio.
- No se descargan fotos de staff.
- Los ratings y salarios del staff son estimaciones del juego.
- Algunos equipos tienen delegados o staff adicional repetido en distintas funciones; se conservan como roles diferentes.
