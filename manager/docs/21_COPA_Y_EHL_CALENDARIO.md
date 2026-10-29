# Copa del Rey y EHL en el calendario diario

**Estado:** implementado (2026-10-21).

## 1. Copa del Rey

La Copa se crea después de la jornada 11 con los 8 mejores de DHA.

Fechas:

- Cuartos: **2 de diciembre de 2026**.
- Semifinal: **3 de diciembre de 2026**.
- Final y tercer puesto: **4 de diciembre de 2026**.

El calendario diario la trata como cualquier partido:

- `next_user_fixture` incluye los partidos de Copa;
- “hasta el próximo partido” se detiene en la fecha de Copa;
- el dashboard y la previa muestran “Copa del Rey · Cuartos/Semifinal/Final”;
- se puede jugar en **simulación rápida**;
- el resultado actualiza el cuadro y el ganador.

El modo directo de Copa queda pendiente; la interfaz oculta ese botón para no prometer algo que todavía no existe.

## 2. EHL

La EHL se activa después de la final de Copa y empieza en enero.

### Quién clasifica

- **3 clubes españoles de DHA**:
  - los **2 primeros de la liga al terminar la primera vuelta**;
  - el **campeón de la Copa del Rey**.
  - Si el campeón de Copa ya estaba entre los dos primeros, entra el siguiente equipo de la liga.
- **5 clubes europeos invitados**: Bloemendaal, Hurley, Kampong, Rot-Weiss Köln y Royal Léopold.

Total: **8 equipos**.

Fechas:

- Cuartos: **7 de enero de 2027**.
- Semifinal: **8 de enero de 2027**.
- Final: **9 de enero de 2027**.

Se resuelve automáticamente al avanzar el calendario por esas fechas. Cada ronda:

- actualiza el cuadro europeo;
- genera una noticia en el diario;
- queda registrada en la página **Europa / EHL**.

La EHL no se juega en directo todavía: se simula automáticamente cada ronda.

## 3. Flujo de usuario

1. Jugar hasta la jornada 11.
2. La Copa aparece en el calendario.
3. Avanzar hasta el 2 de diciembre.
4. Jugar cuartos en simulación rápida.
5. Avanzar a semifinal y final.
6. Continuar la liga.
7. En enero, la EHL se resuelve en sus fechas y aparece en noticias.

## 4. Pruebas

- La Copa se crea con fechas correctas.
- El siguiente partido puede ser de Copa.
- La simulación rápida de Copa actualiza la ronda.
- La EHL tiene fechas y se simula al avanzar hasta ellas.
- La página EHL carga correctamente.

Resultado actual: **80 tests superados**.
