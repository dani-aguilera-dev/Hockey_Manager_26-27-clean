# Relaciones, conversaciones y noticias avanzadas

Esta actualización convierte el vestuario en un sistema de relaciones y la
actualidad en un feed conectado al estado real de la partida.

## Conversaciones individuales

Motor: `manager/src/conversations.py`.

Cada conversación parte de un **contexto real**:

- edad y banda de edad (`joven`, `madurez`, `veterano`);
- posición, overall y potencial;
- rol actual: titular, rotación o sin minutos;
- forma, moral, fatiga y relación con el entrenador;
- partidos, goles, asistencias y rating;
- contrato: largo, cerca de expirar o expirado;
- lesión o sanción;
- interés real de mercado;
- posición del equipo, forma reciente y próximo rival;
- condición de máximo goleador.

### Temas

Los temas disponibles cambian según el contexto. Algunos ejemplos:

- **Jóvenes**: desarrollo, confianza, minutos, cesión, presión.
- **Madurez**: rol, rendimiento, ambición, renovación, mercado.
- **Veteranos**: liderazgo, legado, carga física, futuro, transición al staff.
- **Rendimiento**: racha, bache, falta de minutos, análisis del partido.
- **Contrato**: renovación, salario, claridad institucional.
- **Enfermería**: recuperación, riesgo, apoyo del club.
- **Mercado**: interés real, blindaje, escucha de ofertas.
- **Partido**: mensaje para el próximo rival, plan específico.
- **Club**: objetivo, junta, vestuario, exigencia.
- **Disciplina**: sanción, defensa pública, gestión privada.

### Staff

También se puede hablar con empleados (segundo entrenador, preparador físico,
fisioterapeuta, analista, ojeador, etc.). Los temas incluyen plan de
entrenamiento, análisis del rival, clima del vestuario, mercado, carga física,
cantera y proyecto de club. Los efectos modifican la relación y moral del
empleado, además de variables del equipo.

### Interfaz

- `GET /api/chat` devuelve mensajes, jugadores, staff y objetivos.
- `GET /api/chat/topics?target_type=player|staff&target_id=...` devuelve los
  temas disponibles y el contexto del objetivo.
- `POST /api/chat/start` abre una conversación con un tema concreto.
- `POST /api/chat/<id>` responde con una opción.
- `POST /api/chat/new` abre una conversación aleatoria.
- `GET /api/chat?target_type=staff&target_id=...` se puede enlazar desde la
  ficha de un empleado.

La conversación aleatoria diaria se genera desde `daily_tick`, con un máximo de
dos conversaciones pendientes para no saturar al jugador.

## Noticias avanzadas

Motor: `manager/src/news.py`.

Cada noticia se construye con datos de la partida:

- crónica del último partido;
- premios individuales: MVP, goleador, mejor defensa, portero y joven;
- previa del próximo partido;
- rendimiento y racha del equipo;
- clasificación y lucha por el título;
- ofertas reales recibidas;
- rumores de mercado deterministas basados en plantillas reales;
- tabla de goleadores;
- enfermería, cantera, scouting y junta;
- Copa y EHL.

Cada noticia incluye:

- `team_ids` y `player_ids` relacionados;
- `related_teams` y `related_players` enriquecidos por la API;
- escudos reales (`crest`, `crest2`) generados con `crest_src`;
- `awards` con jugador, equipo, métrica y valor;
- `stats` para el detalle;
- `tags` y categoría.

La UI de noticias permite filtrar por categoría, abrir el detalle, consultar
los premios de la jornada y navegar a las fichas de los equipos y jugadores
relacionados.

## Tests

Cobertura nueva:

- temas distintos para jóvenes y veteranos;
- conversación individual con efectos reales;
- conversación con staff;
- noticias con premios y entidades relacionadas;
- API de temas, inicio, respuesta y noticias.

Total actual: **89 tests**.
