# Modo directo y recompensa a la gestión

**Estado:** implementado (2026-10-20).

Este documento explica el partido interactivo y el sistema interno que premia una buena gestión para que los equipos con plantillas inferiores no estén condenados a perder siempre.

---

## 1. Partido en directo

El partido se puede jugar de dos formas:

- **Directo:** avanzas cuarto a cuarto o momento a momento.
- **Rápido:** el motor simula los 60 minutos de golpe.

En el modo directo, el resto de la jornada se simula primero y tu partido queda aislado para que puedas tomar decisiones sin que el resto de resultados te distraiga.

### Controles

| Tecla | Acción |
|---|---|
| `Enter` | Avanzar el cuarto completo o el siguiente momento |
| `M` | Cambiar a modo minuto a minuto |
| `C` | Volver a modo cuarto completo |
| `E` | Estadísticas en directo |
| `J` | Jugadores en directo (tu equipo y rival) |
| `T` | Cambiar táctica |
| `S` | Hacer un cambio |
| `A` | Simular el resto del partido |

### Qué puedes ver

- Minuto, cuarto y marcador.
- Comentario de los eventos importantes: goles, PC, strokes, paradas, tarjetas, lesiones y cambios.
- Posesión, tiros, tiros a puerta, PC, goles de PC, strokes, paradas, tarjetas, entradas al círculo y pases.
- Minutos, goles, asistencias, tiros, paradas, tarjetas, rating, fatiga y estado de cada jugador.
- Banquillo con overall, fatiga, forma y disponibilidad.
- Gestión, cohesión y lectura táctica de ambos equipos.

### Cambios y táctica

- Puedes hacer hasta **5 cambios**.
- Los cambios se pueden hacer en cualquier pausa, no solo al final del cuarto.
- Si sustituyes a un jugador cansado por uno fresco, el motor concede un pequeño **bonus de banquillo**.
- Puedes cambiar formación, mentalidad, presión, bloque, anchura, tempo, pase y rutina de PC.
- Los cambios tácticos se aplican desde el siguiente momento.
- La **lectura táctica** premia elegir la respuesta correcta al planteamiento rival.

### Charla de vestuario

Al descanso (inicio del tercer cuarto) puedes dar una charla:

| Opción | Efecto principal |
|---|---|
| **Arenga** | Sube moral e intensidad; arriesga si el equipo va ganando cómodo o está muy bajo de moral |
| **Calma** | Ordena y protege el resultado; útil con fatiga alta |
| **Exigir** | Busca una reacción fuerte; puede generar rechazo si la moral es baja |
| **Confiar** | Da confianza cuando el equipo compite bien; mala idea si va perdiendo |
| **Delegar** | El segundo entrenador elige la charla según el contexto |

La charla se resuelve con moral, fatiga, competitividad, liderazgo, marcador y calidad del mánager o del segundo entrenador. El efecto se aplica al ataque y la defensa del siguiente cuarto y luego se reduce a la mitad para el último cuarto.

**Delegar no es una opción de castigo:** el segundo entrenador usa su propio rating y suele tomar una decisión razonable. Es la opción recomendada para quien no quiera gestionar cada detalle.

### IA reactiva

El entrenador rival ya no mantiene la misma táctica todo el partido. En los descansos de cuarto puede:

- Aumentar la mentalidad ofensiva y el tempo si va perdiendo.
- Cerrarse y bajar el ritmo si va ganando en el último cuarto.
- Arriesgar si hay empate cerca del final.
- Cambiar el pase a directo contra presión alta.
- Aprovechar un bloque bajo rival con tempo rápido.
- Reducir presión si la fatiga es alta.
- Hacer cambios si el equipo está fundido.

Los ajustes aparecen en el comentario como `[Ajuste]`. La calidad del mánager rival influye en la probabilidad de reaccionar bien.

### Menos opciones, más decisiones

El diseño evita menús infinitos:

- La charla es una sola vez, al descanso.
- Hay cuatro estilos claros y una opción de delegar.
- El modo rápido delega automáticamente la charla en el segundo entrenador.
- La IA rival se gestiona sola.
- El entrenamiento semanal tendrá un botón de **plan automático** para quien no quiera microgestionar cada sesión.

---

## 2. Gestión: la recompensa interna

Cada equipo tiene una puntuación de **Gestión (0-100)**. No depende solo de la calidad de los jugadores: depende de cómo está gestionado el club.

### Componentes

| Componente | Qué mide | Efecto |
|---|---|---|
| Moral | Ánimo del grupo (1-20) | Hasta +20 puntos |
| Cohesión | Continuidad del once y estabilidad | Hasta +15 puntos |
| Fatiga | Fatiga media del once | Hasta -30 puntos |
| Confianza | Junta y afición | Hasta ±7,5 puntos |
| Encaje | Jugadores en posiciones naturales | Hasta ±6 puntos |
| Entrenador | Trayectoria y rating del mánager | Hasta ±5 puntos |

La puntuación se traduce en un **bonus de ataque/defensa** de hasta **±7 puntos**:

```text
bonus = (gestión - 50) / 8, limitado a [-7, +7]
```

Ese bonus se suma al ataque y la defensa del equipo en cada momento del partido. No garantiza ganar, pero reduce mucho la diferencia contra plantillas superiores.

### Cómo se gana gestión

- Mantener una base estable de titulares sube la cohesión.
- Rotar a tiempo y elegir viajes equilibrados reduce la fatiga.
- Ganar partidos sube la moral, la confianza y el rating del mánager.
- Ganar a un rival claramente superior concede un bonus extra de **upset** al rating.
- Colocar jugadores en su posición natural mejora el encaje.
- Hacer cambios cuando el jugador está cansado genera bonus de banquillo.

### Cómo se pierde

- Alinear jugadores fuera de posición.
- Acumular fatiga por viajes económicos y falta de rotación.
- Cambiar media plantilla cada jornada.
- Encadenar derrotas.
- Dejar caer la confianza de la junta o la afición.

---

## 3. Lectura táctica

Además de la gestión, el motor concede una **ventaja táctica** de hasta +3 puntos si tu planteamiento explota el del rival:

- Presión alta contra rival ofensivo.
- Mentalidad defensiva contra rival muy ofensivo.
- Pase directo contra presión alta.
- Tempo rápido contra bloque bajo.
- Pase corto o mixto contra bloque alto.

La ventaja se muestra en el modo directo y se aplica a ataque y defensa. No es una garantía: es una ventaja probabilística.

---

## 4. Ejemplo de partido

Un equipo con plantilla inferior pero:

- moral 20/20;
- cohesión 20/20;
- confianza 95/100;
- jugadores descansados;
- once en posiciones naturales;
- lectura táctica correcta;

puede sumar **+10 o +12 puntos** entre gestión, moral y táctica. Eso le permite competir contra un equipo superior mal gestionado, aunque siga siendo inferior en atributos individuales.

---

## 5. API técnica

`MatchEngine` permite simular por partes:

```python
engine = MatchEngine(home, away, rng, home_lineup=..., away_lineup=..., ...)
engine.advance_quarter()      # devuelve los eventos del cuarto
engine.advance_moment()       # devuelve los eventos del momento
engine.manual_substitute(side, out_id, in_id)
engine.finished               # True al terminar
engine.result                 # MatchResult
```

`season.py` añade:

```python
ctx = prepare_live_round(state, user_lineup_ids, travel_option_id)
# ... avanzar cuartos/momentos ...
payload = finish_live_round(state, ctx)
```

`finish_live_round` actualiza el fixture, la clasificación, la fatiga, la moral, la gestión, la confianza y la jornada.

---

## 6. Pruebas

`manager/src/tests/test_live_match.py` cubre:

- equivalencia entre simulación completa y simulación por cuartos;
- cambio manual;
- jornada en directo;
- recompensa de gestión;
- charla de vestuario y delegación;
- IA reactiva.

```bash
cd manager
python3 -m pytest src/tests -q
```

Resultado actual: **80 tests superados**.

---

## 7. Limitaciones

- No se puede guardar la partida en mitad del partido.
- La IA cambia mentalidad, presión, bloque, tempo y pase; no cambia de formación en directo.
- Cambiar de formación no recoloca automáticamente a los jugadores: cambia el encaje y la lectura táctica.
- El motor es explicable y lúdico, no una simulación física.
- El bonus de gestión es deliberadamente moderado: ayuda, pero no sustituye la calidad individual.
- La charla de vestuario se da una vez por partido.
- El entrenamiento semanal todavía no está implementado; queda diseñado con opción automática para la siguiente fase.
