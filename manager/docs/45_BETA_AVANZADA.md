# Beta avanzada · Hockey Manager 26-27

Esta iteración convierte la alpha web en una beta de gestión mucho más cercana a un manager de referencia: calendario propio, amistosos, prensa con medios reales, marcas de equipación, editor de fichas y una auditoría de plantillas.

## 1. Plantillas y auditoría

Se detectó la causa de las fichas femeninas que aparecían como jugadoras: iSquad mezcla en el mismo CSV a jugadores y cuerpo técnico. El cargador creaba un `PlayerState` para todos los perfiles.

Ahora:

- `Jugador` e `Invitado` se cargan como jugadores.
- `Entrenador`, `Delegado Equipo`, `Staff Adicional`, `Fisioterapeuta`, `Preparador Fisico`, `Medico` y `Psicologo` se excluyen de la plantilla.
- Los perfiles vacíos de equipos B se mantienen como jugadores.
- Las partidas antiguas se limpian con `_backfill_clean_players`.
- El cuerpo técnico sigue disponible en el staff del club, con nombres y roles propios.

Prueba: `test_staff_are_not_loaded_as_players`.

## 2. Calendario y amistosos

Nueva pantalla `Calendario y amistosos`:

- calendario oficial de la competición;
- fechas libres en los próximos 75 días;
- concertación de amistosos contra cualquier equipo del mundo;
- elección de local/visitante y nota de preparación;
- simulación con el motor real, sin puntos ni clasificación;
- taquilla del amistoso y recuperación ligera;
- cancelación de amistosos pendientes.

Archivos: `src/friendlies.py`, `web/frontend/src/pages/Calendar.tsx`, rutas `/api/calendar`, `/api/friendlies`, `/api/friendlies/<id>/play`.

## 3. Rueda de prensa

La rueda de prensa ya no es un cuestionario fijo:

- periodista y medio acreditado con estilo y sesgo;
- seis temas: partido, rival, presión, vestuario, afición y objetivo;
- efectos en moral, cohesión, junta, afición, relación con un jugador y confianza de los medios;
- titular probable y resumen posterior;
- historial con medio, periodista y efectos.

Archivos: `src/press.py`, `web/frontend/src/pages/Press.tsx`, `TeamState.media_confidence`.

## 4. Marcas reales de equipación

Catálogo `data/brands.json` con marcas reales de hockey, entre ellas:

Osaka, Ritual, Gryphon, Grays, TK, Mercian, STX, Adidas, Kookaburra, JDH, Malik, Dita, Voodoo, Byte, Princess, Harrow, OBO, Fat Pipe, Monkey, Tempest y Rage.

Cada oferta incluye:

- categoría (palas, protección, ropa, calzado, portero, bolas);
- tier regional/nacional/global;
- anualidad, pago por jornada, prima de firma y años;
- bonus de equipación que se aplica al motor de partido;
- requisito deportivo y descripción de la marca.

Archivos: `src/brands.py`, `data/brands.json`, rutas `/api/brands` y `/api/brands/<offer_id>`.

## 5. Editor de jugadores

Cualquier ficha puede corregirse desde la interfaz:

- nombre, edad, línea, posición, arquetipo;
- overall y potencial;
- todos los atributos de la ficha;
- registro de cambios en `event_flags.player_edits`;
- persistencia en la partida.

Archivos: `src/player_editor.py`, `web/frontend/src/pages/Player.tsx`, ruta `/api/player/<id>/edit`.

## 6. Clubes y ubicaciones

Se corrigió el caso documentado de **CD Giner de los Ríos**: es un club de **Valencia**, nacido en 1993 en el Colegio Público Giner de los Ríos de Campanar, no de Madrid. También se añadieron fuentes y verificación de ubicación a los clubes revisados.

La auditoría completa está en `46_AUDITORIA_CLUBES.md`.

## 7. Evidencia técnica

- `python3 -m pytest src/tests -q` → **245 passed**.
- `npm run build` → SPA React compilada correctamente.
- `src/tests/test_beta_features.py` cubre:
  - plantillas sin staff;
  - amistosos sin puntos;
  - marcas y bonus;
  - editor de jugadores;
  - prensa con periodista y seis temas;
  - API de calendario, amistosos, marcas, editor y prensa;
  - ubicación verificada de Giner y descripciones de clubes.

## 8. Límites de esta beta

- No se ha implementado un calendario visual mensual con drag-and-drop; la agenda se organiza por fechas y listas.
- Los amistosos no tienen modo directo minuto a minuto; se resuelven con el motor rápido/detallado.
- La prensa es previa al partido; la rueda posterior queda como siguiente iteración.
- El editor es una herramienta de corrección, no un creador de jugadores desde cero.
- Las marcas son acuerdos de equipación del club; no hay contratos individuales de imagen por jugador.
