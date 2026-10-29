# Fase 1 — Implementación del vertical slice

**Estado:** implementada y probada (2026-10-20).

**Objetivo:** una temporada completa de DHA jugable con un club, partidos de texto, logística, clasificación y guardado/carga.

---

## 1. Qué se puede hacer

- Elegir uno de los 12 clubes de DHA.
- Ver dossier de club: historia, estadio, junta, finanzas, logística y jugadores clave.
- Consultar plantilla, ficha individual, 37 atributos, overalls posicionales, arquetipo y especialistas.
- Configurar táctica: formación, mentalidad, presión, bloque, anchura, tempo, pase y rutina de PC.
- Elegir once automático o manual.
- Jugar la temporada regular: 22 jornadas, 132 partidos, ida y vuelta.
- Jugar el partido en **directo**: cuarto a cuarto o minuto a minuto, con estadísticas, jugadores, cambios y táctica en vivo.
- Dar una **charla de vestuario** al descanso o delegarla en el segundo entrenador.
- Enfrentarte a una **IA reactiva** que ajusta táctica y cambios según el marcador y la fatiga.
- Planificar el **entrenamiento semanal** o delegarlo en el segundo entrenador, con plan automático y editor de sesiones.
- Consultar **staff y junta directiva**, con efectos reales del staff en entrenamiento y charla.
- Gestionar **finanzas**: caja, presupuesto de fichajes, salarios, patrocinio, taquilla y viajes.
- Usar el **mercado**: buscar jugadores, hacer ofertas, renovar contratos, contratar/despedir staff y recibir ofertas.
- Continuar **varias temporadas**, con ascensos, descensos y DHA/DHB.
- Jugar la **Copa del Rey** con los 8 mejores de DHA, gestionar la **cantera**, responder a la **prensa** y revisar la **junta directiva**.
- Competir en la **EHL** si el club se clasifica.
- Ver comentario textual por cuartos, estadísticas, ratings, tarjetas, lesiones y cambios.
- Gestionar moral, cohesión, fatiga, confianza, encaje posicional y rating del mánager. La gestión otorga un bonus interno de hasta ±7 puntos.
- Elegir viaje en los partidos fuera de casa (económico, equilibrado o premium).
- Consultar clasificación, calendario, finanzas y estado físico.
- Guardar y cargar la partida en SQLite.
- Al terminar la liga: Final Four, playout y resumen de temporada.

La Fase 1 se centra en DHA. La DHB ya tiene liga propia de dos fases y puede jugarse si el club asciende o desciende. La 1ª Andaluza no se simula: sus jugadores pasan al mercado como agentes libres.

---

## 2. Cómo ejecutar

Desde `manager/`:

```bash
python3 run.py
```

Con una base de datos alternativa:

```bash
python3 run.py --db /ruta/mi_partida.db
```

Simulación automática de una temporada completa (sin interacción):

```bash
python3 run.py --auto --club cd-terrassa --seed 7
```

Pruebas:

```bash
cd manager
python3 -m pytest src/tests -q
```

Resultado esperado: **80 tests superados**.

---

## 3. Flujo de juego

```
Menú principal
  → Nueva partida / Cargar partida
  → Elegir club DHA
  → Dossier y aceptar el puesto
  → Dashboard
      → Plantilla / ficha
      → Táctica y once
      → Calendario y clasificación
      → Club y estadio
      → Finanzas
      → Logística
      → Jugar partido
      → Simular jornada (auto)
      → Guardar / Salir
```

### Partido

1. Previa: rival, estadio, posición y moral.
2. Once automático o manual.
3. Si se juega fuera: elección de viaje.
4. Confirmación.
5. Simulación de los 64 momentos de juego.
6. Comentario por cuartos, estadísticas, ratings e incidencias.
7. En modo directo: pausas para ver estadísticas/jugadores, cambiar táctica o hacer cambios.
8. Actualización de clasificación, fatiga, moral, presupuesto, confianza y gestión.

---

## 4. Arquitectura

```
manager/
  run.py                  # lanzador
  src/
    main.py               # argparse: interactivo y --auto
    ui.py                 # CLI de texto
    models.py             # dataclasses y serialización
    data_loader.py        # clubs.json, cities.json, CSV de atributos
    calendar.py           # round-robin, clasificación, tabla
    match_engine.py       # motor por fases, PC, stroke, eventos
    logistics.py          # distancias, opciones de viaje, fatiga
    season.py             # jornadas, Final Four, playout, resumen
    persistence.py        # SQLite y JSON
  data/                   # datos base
  saves/                  # manager.db (ignorado por git)
  docs/                   # documentación
```

### Separación de capas

- **Datos:** JSON y CSV; no se modifican durante la partida.
- **Modelo:** dataclasses con estado de jugador, equipo, fixture y partida.
- **Motor:** recibe dos equipos y una semilla; devuelve un `MatchResult`.
- **Temporada:** orquesta calendario, viajes, resultados y clasificación.
- **Persistencia:** serializa el estado completo.
- **UI:** solo lee y modifica el estado; no contiene reglas de juego.

---

## 5. Motor de partido

### Estructura

- 4 cuartos × 16 momentos = **64 momentos**.
- 60 minutos de juego (4 × 15).
- Zonas: `own_23`, `middle`, `attacking_23`, `circle`.
- Posesión alternativa según medios, pase, táctica y moral.
- Acciones: pase, 3D, aerial, tackle, falta, tarjeta, entrada al círculo, tiro, PC, stroke, lesión y sustitución.

### Atributos usados

- Ataque: definición, PC flick, regate 3D, pase y velocidad.
- Defensa: cobertura, posicionamiento, primer runner, pressing y fuerza.
- Portero: reflejos, blocaje, PC GK save y stroke save.
- Especialistas: inyector, stopper, flicker, desviador, primer runner, portero de PC, stroke y faltas.

### PC y stroke

- El PC se genera desde `attacking_23` y `circle`.
- Secuencia: saque → primer runner → control → tiro/desvío → portero → rebote.
- Rotación de lanzadores: los tres mejores flickers reciben PC con pesos 55/30/15; los desviadores con 72/28.
- El stroke se resuelve con `stroke_shot` contra `stroke_save`.

### Calibración actual

Sobre 300 partidos simulados con los 12 equipos DHA:

| Métrica | Media |
|---|---:|
| Goles por partido | ≈ 5,0 |
| Tiros por partido | ≈ 16,5 |
| Tiros a puerta | ≈ 12,4 |
| Penalty corners | ≈ 6,7 |
| Goles de PC | ≈ 3,0 |

La temporada completa simulada suele quedar en **5,0–5,4 goles por partido**. Los máximos goleadores rondan **20–27 goles** en 22 jornadas.

### Fatiga

- Cada momento añade fatiga a ambos equipos.
- Presión alta y tempo rápido aumentan la fatiga.
- Los viajes añaden fatiga antes del partido.
- Recuperación semanal: 14 puntos.
- La autoalineación prioriza jugadores con fatiga < 80 % y rota si es necesario.
- La fatiga reduce ataque y defensa, y penaliza la selección automática.

---

## 6. Logística

- Distancias con Haversine entre ciudades.
- Modos: bus, tren y avión.
- Islas y trayectos largos usan avión.
- Tres opciones por desplazamiento:
  - **Económico:** mismo día, más fatiga.
  - **Equilibrado:** una noche, recomendado.
  - **Premium:** dos noches, menos fatiga y más coste.
- El coste se descuenta del presupuesto.
- En casa no hay viaje.
- La IA usa la opción equilibrada si puede pagarla; si no, la más barata.
- Ejemplo: Taburiente → Terrassa ≈ 2.179 km, avión, 5.992 € y +12 % de fatiga en la opción equilibrada.

---

## 7. Guardado y carga

Archivo por defecto: `manager/saves/manager.db`.

```sql
CREATE TABLE saves (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  club_id TEXT NOT NULL,
  season TEXT NOT NULL,
  round INTEGER NOT NULL,
  updated_at TEXT NOT NULL,
  state_json TEXT NOT NULL
);
```

- El estado completo se serializa como JSON.
- Se guarda: club, temporada, jornada, fecha, fixtures, equipos, jugadores, tácticas, fatiga, moral, lesiones, sanciones, presupuesto, Final Four, playout, inbox y último resultado.
- `export_json` / `import_json` permiten depurar o migrar una partida.
- El esquema SQLite de 41 tablas sigue siendo el objetivo de fases posteriores; para el MVP se usa un blob JSON para no acoplar la UI.

---

## 8. Final Four y playout

Al terminar la jornada 22:

- **Semifinales:** 1º vs 4º y 2º vs 3º, en sede neutral.
- **Final:** ganadores, con prórroga/stroke si hay empate (shootout).
- **Playout:** 11º de DHA contra el mejor equipo DHB por potencial de plantilla.
  - Si gana el 11º, mantiene la plaza.
  - Si pierde, desciende y asciende el representante DHB.
- El 12º desciende directamente.
- El representante DHB del playout se elige por potencial; la liga DHB completa ya se simula para ascensos y descensos.

---

## 9. Pruebas

`manager/src/tests/` incluye:

- `test_calendar.py`: 132 partidos, 22 jornadas, 11 local/11 visitante, tabla.
- `test_logistics.py`: distancias, modos, costes y fatiga.
- `test_match_engine.py`: determinismo, estadísticas, PC/stroke y balance.
- `test_persistence.py`: SQLite y JSON.
- `test_models.py`: autoalineación, formaciones y modificadores.
- `test_season.py`: temporada completa, Final Four, playout y once manual.
- `test_live_match.py`: simulación por cuartos, cambio manual, jornada en directo, recompensa de gestión, charla de vestuario y IA reactiva.
- `test_training.py`: plan automático, recuperación, entrenamiento semanal, IA y guardado del estado.
- `test_staff_finance.py`: staff, junta, salarios, cierre financiero y resumen.
- `test_market.py`: ventanas, fichajes, contratos, staff, ofertas y multi-temporada.
- `test_phase4.py`: Copa, cantera, prensa y revisión de la junta.

Comando:

```bash
cd manager
python3 -m pytest src/tests -q
```

---

## 10. Limitaciones conocidas

- La 1ª Andaluza no se simula; sus jugadores son agentes libres.
- La DHB sí se simula con dos fases, pero no tiene descenso a 1ª Andaluza.
- Final Four y playout se simulan automáticamente; no tienen previa interactiva.
- No se puede guardar la partida en mitad del partido.
- El entrenamiento es semanal y grupal; no hay sesiones individuales, mercado, cantera, prensa ni multi-temporada.
- El mercado no incluye cesiones, cláusulas, agentes ni primas por objetivos.
- La DHB tiene dos fases reales, pero no desciende a 1ª Andaluza porque esa liga no se simula.
- La Copa no tiene cabezas de serie ni sorteo dirigido.
- La cantera y la prensa son sistemas simplificados.
- Parte del staff y de la junta son nombres de modelo, no datos oficiales.
- Las finanzas son básicas: taquilla y viajes; los salarios no se descuentan todavía.
- La IA de viaje usa equilibrado/barato; no negocia hoteles ni vuelos.
- El motor es lúdico y explicable, no una simulación física.
- Las posiciones y atributos siguen siendo estimaciones del modelo, salvo las fuentes documentadas.

---

## 11. Criterios de aceptación de Fase 1

| Criterio | Estado |
|---|---|
| Temporada DHA completa con 12 equipos | Cumplido |
| Partidos con eventos coherentes | Cumplido |
| Clasificación y calendario | Cumplido |
| Viaje → fatiga → rendimiento | Cumplido |
| Guardado y carga | Cumplido |
| Partido en directo con decisiones | Cumplido |
| La gestión influye en el rendimiento | Cumplido |
| Entrenamiento semanal con plan automático | Cumplido |
| Staff con efectos y junta directiva | Cumplido |
| Finanzas de jornada y salarios | Cumplido |
| Mercado, contratos y staff | Cumplido |
| Multi-temporada DHA/DHB | Cumplido (DHB de dos fases) |
| Copa del Rey | Cumplido |
| Cantera, prensa y junta dinámica | Cumplido |
| Sin errores de consola | Cumplido en pruebas y simulación |

---

## 12. Modo directo y gestión

El detalle de controles, componentes de gestión y lectura táctica está en
[`08_MODO_DIRECTO_Y_GESTION.md`](08_MODO_DIRECTO_Y_GESTION.md).

---

## 13. Siguiente fase recomendada

1. Entrenamiento semanal y desarrollo de atributos.
2. Moral y dinámica de grupo.
3. Junta, objetivos y finanzas completas.
4. Logística avanzada con decisiones de hotel/comida.
5. Descenso DHB → 1ª Andaluza y sorteo de Copa con cabezas de serie.
6. Partidos interactivos de Final Four.
7. Multi-temporada y mercado.
