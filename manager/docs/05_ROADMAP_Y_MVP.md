# Roadmap y MVP

**Objetivo:** llegar a un juego de gestión de hockey hierba jugable, solo texto, con una temporada completa y logística real.

---

## 1. Estrategia

No empezar por el motor más complejo. Empezar por un **vertical slice** que demuestre el bucle:

```
elegir club → ver dossier → planificar semana → elegir once → jugar partido → ver resultado → avanzar
```

Después añadir profundidad: entrenamiento, moral, finanzas, mercado, cantera, multi-temporada.

---

## 2. Fases

### Fase 0 — Fundación de datos

**Estado:** completada en diseño.

- 29 clubes con historia, estadio, ciudad, instalaciones, finanzas y logística.
- 16 ciudades con coordenadas y hubs.
- 976 perfiles con 37 atributos.
- Formatos DHA/DHB/1ª.
- Roles tácticos y de staff.
- Esquema SQLite de 41 tablas.

**Entregables:**

- `manager/data/clubs.json`
- `manager/data/cities.json`
- `manager/data/competitions.json`
- `manager/data/tactical_roles.json`
- `manager/data/staff_roles.json`
- `manager/data/events.json`
- `manager/schema/schema.sql`

### Fase 1 — Vertical slice (MVP)

**Estado:** implementada (2026-10-20). Ver `07_FASE1_IMPLEMENTACION.md`.

**Objetivo:** una temporada jugable con un club, partidos de texto y logística básica.

**Nota:** la Fase 1 incluye ya una versión automática de Final Four y playout. La Fase 4 los convertirá en eliminatorias interactivas y completas.

Incluye:

- Menú y selección de club.
- Dashboard.
- Plantilla y ficha de jugador.
- Táctica y once inicial.
- Calendario DHA o DHB.
- Motor de partido por fases (versión simple).
- Comentario de texto.
- Clasificación.
- Viajes y fatiga básica.
- Guardado/carga.

No incluye:

- Mercado de fichajes.
- Cantera.
- Prensa compleja.
- Multi-temporada.
- Copa/EHL.

**Criterios de aceptación:**

- Se puede jugar una temporada completa de DHA con 12 equipos.
- Los partidos generan eventos coherentes.
- La clasificación y el calendario funcionan.
- El viaje afecta a la fatiga y al rendimiento.
- El juego guarda y carga.
- No hay errores de consola.

### Fase 2 — Gestión de club

**Estado parcial:** Fase 2A (entrenamiento semanal con plan automático) y Fase 2B (staff y finanzas) implementadas el 2026-10-20. Ver `09_ENTRENAMIENTO_SEMANAL.md` y `10_STAFF_Y_FINANZAS.md`.

Añade:

- Entrenamiento semanal y desarrollo.
- Moral y dinámica.
- Lesiones y sanciones.
- Junta directiva y objetivos.
- Finanzas completas.
- Prensa y afición.
- Logística avanzada (hoteles, comidas, opciones).
- Staff y efectos.

**Criterios:**

- El entrenamiento cambia atributos y fatiga.
- La moral afecta al rendimiento.
- La junta evalúa objetivos.
- Las finanzas cuadran.
- La logística es una decisión real.

### Fase 3 — Mercado y mundo

**Estado:** implementada (2026-10-20). Ver `11_FASE3_MERCADO_Y_MULTITEMPORADA.md`.

Añade:

- Ventanas de fichajes.
- Ofertas y contratos.
- Ojeadores y conocimiento parcial.
- Cantera y captación.
- IA de mercado.
- Rumores y agentes.
- Historial de temporadas.

**Criterios:**

- Los clubes IA fichan de forma coherente.
- Los jugadores aceptan/rechazan ofertas.
- La cantera produce jugadores.
- El mercado no se rompe en 10 temporadas.

### Fase 5 — Mundo completo

**Estado parcial:** Fase 5A implementada (2026-10-21): DHB real de dos fases, agentes libres de 1ª Andaluza, Copa del Rey de 8 equipos DHA y EHL. Ver `13_FASE5A_DHB_REAL_Y_AGENTES_LIBRES.md`. Queda el descenso DHB → 1ª Andaluza y el sorteo de Copa con cabezas de serie.

### Fase 4 — Profundidad y pulido

**Estado:** implementada parcialmente (2026-10-20). Copa, cantera, prensa y junta dinámica ya están en el juego. Ver `12_FASE4_COPA_CANTERA_PRENSA_JUNTA.md`.

Añade:

- Copa del Rey.
- EHL (opcional).
- Final Four y playout completos.
- Multi-temporada.
- Récords e historia.
- Editor de datos.
- Mods.
- Accesibilidad.
- Balance fino.

---

## 3. Vertical slice: alcance técnico

### 3.1. Archivos

```
manager/
  src/
    models.py          # dataclasses
    data_loader.py     # JSON/CSV
    calendar.py        # fixtures y fases
    match_engine.py    # motor de fases
    logistics.py       # distancias, costes, fatiga
    world.py           # estado de temporada
    ui.py              # CLI/TUI
    prototype.py       # entrada jugable
  data/
    clubs.json
    cities.json
    competitions.json
    tactical_roles.json
    staff_roles.json
    events.json
  saves/
```

### 3.2. Flujo del prototipo

1. Cargar clubes y jugadores.
2. Elegir club.
3. Mostrar dossier.
4. Generar calendario de DHA (o DHB simplificado).
5. Mostrar dashboard.
6. Elegir once automático o manual.
7. Calcular logística del próximo partido.
8. Simular partido con comentario.
9. Actualizar clasificación, fatiga, moral y finanzas.
10. Avanzar jornada.

### 3.3. Datos de jugadores

Usar `tools/player_attributes_v2.csv` como fuente. Para el prototipo, cargar solo los jugadores del club elegido y los rivales; el resto puede ser datos agregados.

---

## 4. Backlog priorizado

| Prioridad | Tarea | Impacto | Esfuerzo |
|---|---|---|---|
| P0 | Cargar clubes/ciudades/jugadores | Alto | Bajo |
| P0 | Dossier de club | Alto | Bajo |
| P0 | Calendario DHA | Alto | Medio |
| P0 | Motor de partido básico | Muy alto | Alto |
| P0 | Comentario de texto | Alto | Medio |
| P0 | Clasificación | Alto | Bajo |
| P0 | Guardado/carga | Alto | Bajo |
| P1 | Logística y fatiga | Alto | Medio |
| P1 | Táctica y especialistas | Alto | Medio |
| P1 | Entrenamiento | Medio | Medio |
| P1 | Moral | Medio | Medio |
| P1 | Finanzas | Medio | Medio |
| P2 | Mercado | Alto | Alto |
| P2 | Cantera | Medio | Alto |
| P2 | Prensa | Medio | Medio |
| P2 | Junta | Medio | Bajo |
| P3 | Copa/EHL | Bajo | Alto |
| P3 | Multi-temporada | Alto | Alto |

---

## 5. Pruebas y balance

### 5.1. Tests unitarios

- Distancia haversine.
- Coste/fatiga de viaje.
- Calendario: 22 jornadas, 12 equipos, ida/vuelta.
- Motor: misma semilla → mismo resultado.
- Atributos: cada acción usa los pesos correctos.
- Set pieces: PC y stroke generan eventos válidos.
- Finanzas: ingresos/gastos cuadran.

### 5.2. Simulaciones largas

- 10.000 partidos para calibrar goles, PC, tarjetas y lesiones.
- 100 temporadas para comprobar que no hay colapsos económicos.
- 10 temporadas de mercado para comprobar que los clubes IA no se rompen.

### 5.3. Playtesting

- Un club de DHA grande (RC de Campo).
- Un club de DHA medio (CD Terrassa).
- Un club de DHB (Egara 1935).
- Un club canario (Taburiente).
- Un club andaluz (San Fernando).

---

## 6. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Motor demasiado complejo | Empezar con acciones simples y ampliar. |
| Partidos aburridos | Variedad de eventos, narrativa, decisiones. |
| Logística tediosa | Planes recomendados y automatización. |
| Datos incompletos | Marcar calidad y permitir edición. |
| Balance roto | Simulaciones y ajuste continuo. |
| UI pobre | Invertir en texto, tablas y ritmo. |
| Sin inmersión | Clubes con historia, prensa, moral, rivalidades. |

---

## 7. Próxima sesión recomendada

1. Implementar `models.py` y `data_loader.py`.
2. Cargar los 29 clubes y los jugadores del club elegido.
3. Mostrar el dossier y el dashboard.
4. Implementar el calendario DHA.
5. Implementar un motor de partido mínimo con comentario.
6. Guardar/cargar la partida.
7. Probar una temporada.

---

## 8. Definición de “MVP terminado”

- Se elige un club.
- Se ve su historia, estadio y logística.
- Se juega una temporada completa.
- Los partidos tienen comentario y estadísticas.
- La clasificación es correcta.
- La fatiga y los viajes importan.
- Se guarda y carga.
- No hay crashes.
- El jugador quiere jugar otra temporada.
