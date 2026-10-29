# Modelo de datos

**Persistencia:** SQLite para la partida; JSON para datos base (clubes, ciudades, competiciones, roles).
**Esquema:** `manager/schema/schema.sql` (41 tablas).
**Principio:** datos normalizados para entidades estables; campos JSON para atributos, tácticas y eventos.

---

## 1. Grupos de entidades

```
CLUB ──< STADIUM
  │
  ├──< FACILITIES
  ├──< CONTRACT >── PLAYER
  ├──< STAFF >── STAFF_ROLE
  ├──< TACTICS
  ├──< TRAVEL_PLAN >── FIXTURE
  ├──< TRANSACTION
  ├──< BUDGET
  ├──< BOARD_OBJECTIVE
  ├──< BOARD_CONFIDENCE
  ├──< FAN_CONFIDENCE
  └──< INBOX

COMPETITION ──< SEASON ──< FIXTURE >── CLUB
                         └──< STANDING

FIXTURE ──< MATCH_EVENT
        ├──< MATCH_STATS
        ├──< PLAYER_MATCH_STATS
        └──< LINEUP

PLAYER ──< INJURY
       ├──< SUSPENSION
       ├──< MORALE
       ├──< SCOUTING_REPORT
       └──< TRANSFER
```

---

## 2. Tablas principales

### Clubes y ciudades

| Tabla | Contenido |
|---|---|
| `clubs` | Identidad, liga, ciudad, fundación, colores, historia, reputación. |
| `cities` | Coordenadas, comunidad, provincia, aeropuerto, tren. |
| `stadiums` | Nombre, dirección, superficie, capacidad y confianza. |
| `facilities` | Campos, gimnasio, médico, vídeo, cantera. |
| `rivalries` | Rivalidad e intensidad. |

### Competiciones

| Tabla | Contenido |
|---|---|
| `competitions` | DHA, DHB, 1ª; formato JSON. |
| `seasons` | Temporada, fechas, estado. |
| `season_teams` | Equipos por temporada y grupo. |
| `fixtures` | Partidos, fase, fecha, sede, resultado, clima. |
| `standings` | Clasificación y forma. |

### Jugadores

| Tabla | Contenido |
|---|---|
| `players` | Identidad, posición, atributos JSON, overalls, valor, arquetipo. |
| `contracts` | Club, fechas, salario, rol, cláusula. |
| `player_match_stats` | Minutos, goles, asistencias, tarjetas, rating. |
| `injuries` | Tipo, gravedad, fechas. |
| `suspensions` | Partidos de sanción. |
| `morale` | Moral, felicidad, relaciones. |

### Staff

| Tabla | Contenido |
|---|---|
| `staff_roles` | 13 roles y efectos. |
| `staff` | Personas, rol, atributos, salario. |

### Táctica y partido

| Tabla | Contenido |
|---|---|
| `tactics` | Formación, instrucciones, especialistas. |
| `lineups` | Once, roles, minutos, rating. |
| `match_events` | Eventos de texto, tipo, jugador, xG. |
| `match_stats` | Posesión, tiros, PC, strokes, tarjetas, etc. |

### Finanzas y logística

| Tabla | Contenido |
|---|---|
| `budgets` | Presupuesto de fichajes, salarios, operaciones. |
| `transactions` | Ingresos y gastos. |
| `travel_plans` | Modo, fechas, distancia, coste, fatiga. |

### Mercado y cantera

| Tabla | Contenido |
|---|---|
| `transfers` | Traspaso, fee, ventana, estado. |
| `transfer_offers` | Ofertas y respuestas. |
| `scouting_assignments` | Ojeador, región, fechas. |
| `scouting_reports` | Conocimiento, rating, notas. |
| `youth_players` | Cantera. |

### Junta, afición, prensa

| Tabla | Contenido |
|---|---|
| `board_objectives` | Objetivos de temporada. |
| `board_confidence` | Confianza de la junta. |
| `fan_confidence` | Confianza de la afición. |
| `media_events` | Noticias y ruedas de prensa. |
| `inbox` | Mensajes y decisiones. |

### Historia

| Tabla | Contenido |
|---|---|
| `season_history` | Campeones, ascensos, descensos. |
| `club_records` | Récords de club. |

---

## 3. Atributos del jugador

`players.attributes_json` contiene los 37 atributos:

```json
{
  "control": 68, "pase": 76, "conduccion": 71, "golpeo": 63,
  "flick": 65, "regate_3d": 54, "definicion": 66,
  "aerial": 69, "pc_injection": 68, "pc_trap": 80, "pc_flick": 72,
  "pc_deflection": 61, "pc_first_runner": 74, "pc_gk_save": 33,
  "stroke_shot": 66, "stroke_save": 29, "free_hit": 77,
  "posicionamiento": 75, "pressing": 70, "cobertura": 78,
  "transicion": 68, "desmarque": 60,
  "velocidad": 62, "resistencia": 72, "fuerza": 70,
  "agilidad": 65, "coordinacion": 67,
  "decisiones": 74, "concentracion": 71, "competitividad": 73, "liderazgo": 65,
  "reflejos": 34, "blocaje": 33, "distribucion": 31,
  "uno_vs_uno": 30, "alto": 32, "rebote_gk": 30
}
```

`players.overalls_json`:

```json
{
  "Portero": 35.6, "Central": 73.9, "Lateral": 69.9,
  "Medio": 75.5, "Delantero": 65.2
}
```

---

## 4. Táctica

`tactics` guarda la formación y las instrucciones. `set_piece_roles_json`:

```json
{
  "pc_injector": "POL CALONGE PARDO",
  "pc_stopper": "IAIN MARTIN MCFADDEN",
  "pc_flicker": "JOAN MIRO CARDELLACH",
  "pc_deflector": "ALEIX VERICAT TORRES",
  "pc_first_runner": "GUILLEM CORTINA NOGUERAS",
  "pc_goalkeeper": "SERGIO SALAS MEDINA",
  "stroke_taker": "ENRIC MIRALLES PORTILLO",
  "stroke_goalkeeper": "SERGIO SALAS MEDINA",
  "aerial_specialist": "FRANCISCO DE BORJA SOLER FERRER",
  "free_hit_taker": "IAIN MARTIN MCFADDEN"
}
```

---

## 5. Eventos

`match_events`:

```json
{
  "minute": 31,
  "type": "goal",
  "club_id": "cd-terrassa",
  "player_id": "p123",
  "assistant_id": "p456",
  "text": "PC para CD Terrassa. Joan Miro transforma con un drag flick.",
  "xg": 0.28,
  "metadata_json": {"set_piece": "pc", "routine": "directa"}
}
```

`inbox`:

```json
{
  "date": "2026-09-23",
  "club_id": "cd-terrassa",
  "category": "board",
  "subject": "La junta espera el top 6",
  "body": "La dirección deportiva confía en el proyecto, pero pide resultados.",
  "read": 0,
  "action_required": 1
}
```

---

## 6. Guardado

```
manager/saves/<save_id>.db      # SQLite con el estado de la partida
manager/saves/<save_id>.json    # metadatos, seed, versión, resumen
```

Metadatos:

```json
{
  "save_id": "cd-terrassa-2026",
  "manager": "Daniel",
  "club_id": "cd-terrassa",
  "season": "2026-27",
  "seed": 20261019,
  "version": "0.1.0",
  "updated_at": "2026-10-19T20:00:00"
}
```

---

## 7. Reglas de integridad

- Un jugador no puede tener dos contratos activos.
- Un club no puede tener dos equipos en la misma categoría.
- Un equipo vinculado no puede ascender si su matriz está en DHA.
- La masa salarial no puede superar el límite de la liga (si existe).
- Los viajes deben tener un `fixture_id` y un `club_id` válidos.
- Los eventos deben pertenecer a un partido jugado.
- Las clasificaciones se recalculan desde los resultados, no se editan a mano.

---

## 8. Migraciones

- `schema_version` en `saves`.
- Migraciones incrementales en `manager/src/migrations/`.
- Copia de seguridad antes de migrar.
- Validación de integridad al cargar.
