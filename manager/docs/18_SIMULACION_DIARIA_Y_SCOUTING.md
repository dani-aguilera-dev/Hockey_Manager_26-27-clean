# Simulación diaria, scouting y perfiles de equipo

**Estado:** vertical slice implementada (2026-10-21).

## 1. Modelo temporal

La temporada ya no avanza de golpe de jornada en jornada. `GameState.date` es la fecha actual y la simulación diaria avanza un día cada vez.

- Pretemporada: **1 de agosto de 2026**.
- Primer partido DHA: **20 de septiembre de 2026**.
- La simulación se detiene en la fecha del próximo partido regular del usuario.
- Nunca juega el partido por su cuenta: el usuario decide si usar simulación rápida o directo.
- Se puede avanzar:

  - **1 día**;
  - **hasta una fecha concreta**;
  - **hasta el próximo partido**.

El formulario está en el dashboard. Si la fecha elegida supera el próximo partido, el sistema se detiene en el día del partido.

## 2. Eventos diarios

Cada día puede generar:

- entrenamientos y subidas de forma;
- lesiones y partes médicos;
- rumores y movimientos de mercado;
- noticias de la liga del usuario;
- noticias sueltas de la otra liga (DHA ↔ DHB);
- noticias de club, afición y cantera;
- conversaciones de vestuario.

Los eventos se guardan en `state.daily_events` y aparecen en:

- dashboard, tarjeta **Diario del club**;
- noticias, sección **Diario del club**;
- inbox cuando son importantes.

El motor es determinista por semilla y fecha, para que una partida guardada reproduzca el mismo día.

## 3. Vestuario

`state.chat_messages` guarda conversaciones con jugadores.

- El entrenador puede responder con varias opciones.
- Cada opción modifica moral, forma, cohesión o confianza del mánager.
- Hay conversaciones sobre minutos, contrato y ambiente.
- Se puede abrir una conversación manualmente desde **Vestuario**.
- Las conversaciones pendientes aparecen en el dashboard.

## 4. Mercado y ventanas

La ventana ya no se cierra al jugar el primer partido.

- **Verano:** 1 de agosto - 30 de septiembre.
- **Invierno:** 1 - 31 de enero.
- Fuera de esas fechas el mercado está cerrado, pero **la lista de jugadores sigue visible**.
- Se puede consultar, otear y abrir fichas; solo se bloquean las ofertas.

El objetivo es que el primer partido no elimine la planificación de la plantilla.

## 5. Scouting y panorama de ligas

La pestaña **Mercado** muestra jugadores de todos los clubes de DHA/DHB y agentes libres.

- Filtros por nombre, club, posición y valor máximo.
- Todos los jugadores de un club se pueden ver aunque no estén en el top global.
- Cada ficha muestra club, posición, arquetipo, overall ojeado, edad, partidos, goles, asistencias, rating, precio y salario.
- El club propietario enlaza a su perfil.
- La ficha individual enlaza a la plantilla del club y a la ficha completa del jugador.

## 6. Perfiles de equipo

`/team/<team_id>` muestra:

- descripción e historia del club;
- ciudad, estadio, aforo, colores, instalaciones y academia;
- posición y estadísticas de temporada;
- **once probable** con formación, fotos reales, posición y arquetipo;
- banquillo probable con caras;
- plantilla completa con foto, PJ, goles, asistencias y rating;
- últimos resultados y próximos partidos;
- acceso al mercado filtrado por ese club.

Los nombres de equipo de la clasificación del dashboard y de la tabla enlazan a esta vista.

## 7. Histórico de jugadores

`PlayerState.career` guarda una entrada por temporada:

```text
temporada, club, liga, partidos, goles, asistencias, rating, overall
```

- Se registra al terminar la temporada, antes de resetear las estadísticas.
- Se conserva al cambiar de club.
- La ficha de jugador muestra la temporada actual y el histórico.
- La ficha de mercado también muestra el histórico.

## 8. Archivos

```text
manager/src/daily.py              # simulación diaria y eventos
manager/src/models.py             # daily_events, chat_messages y career
manager/src/season.py             # fechas de pretemporada, carrera y ventanas
manager/src/market.py             # ventana por fecha
manager/web/app.py                # /simulate, /chat, /team y filtros de mercado
manager/web/templates/dashboard.html
manager/web/templates/chat.html
manager/web/templates/team.html
manager/web/templates/player.html
manager/web/templates/market.html
manager/web/templates/market_player.html
manager/src/tests/test_daily.py
```

## 9. Pruebas

Se verifica:

- avance diario hasta una fecha;
- parada en el día del próximo partido;
- generación de eventos;
- mercado abierto tras el primer partido;
- jugadores de otros equipos en el mercado;
- registro del histórico de temporada;
- rutas de equipo, vestuario, chat y calendario.

Resultado actual: **80 tests superados**.

## 10. Limitaciones

- No se simulan ligas juveniles ni partidos de cantera.
- La Copa y la EHL ya están en el calendario diario. La Copa se puede jugar en simulación rápida desde su fecha; la EHL se resuelve automáticamente en sus fechas.
- Los eventos son generados, no noticias externas en tiempo real.
- El mercado de invierno está simplificado a enero.
- La IA de otros clubes no disputa partidos día a día; sus clasificaciones se mantienen con el motor de jornadas.
