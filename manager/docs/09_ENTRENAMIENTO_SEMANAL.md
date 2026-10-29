# Entrenamiento semanal (Fase 2A)

**Estado:** implementado (2026-10-20).

La semana de trabajo cubre el hueco entre partidos sin convertir el juego en un simulador de sesiones interminable. La filosofía es: **pocas decisiones, plan automático por defecto y opción de editar solo si quieres**.

---

## 1. Flujo semanal

Desde el dashboard:

```text
Entrenamiento: pendiente · [E] planificar la semana · Segundo entrenador 78/100
```

Al entrar en `E`:

```text
ENTRENAMIENTO SEMANAL
Próximo partido: CD Terrassa vs Club Egara
Segundo entrenador: 78/100 · Fatiga media 18.4% · Moral 12/20

[Enter] Plan automático (segundo entrenador)
[E] Editar plan sesión a sesión
[R] Semana de recuperación
[V] Volver
```

- **Plan automático:** el segundo entrenador elige las cinco sesiones según el rival, la fatiga, la moral y las instalaciones.
- **Editar plan:** muestra lunes a viernes y permite cambiar cada sesión.
- **Semana de recuperación:** plan conservador para equipos fundidos.
- Si no planificas y vas directo al partido, el segundo entrenador aplica el plan automático.

---

## 2. Sesiones

| Sesión | Fatiga | Efecto principal |
|---|---:|---|
| Recuperación | -11% | Baja fatiga y recupera lesiones leves |
| Descanso | -15% | Recuperación fuerte y moral |
| Físico | +10% | Resistencia, fuerza y velocidad; más riesgo |
| Táctico | +5% | Cohesión y atributos tácticos |
| Set pieces | +4% | PC, stroke, faltas y primer runner |
| Ataque | +6% | Definición, regate, pase y desmarque |
| Defensa | +6% | Cobertura, pressing, posición y transición |
| Vídeo / rival | +1% | Decisiones, concentración y preparación del rival |
| Activación | -3% | Forma y moral antes del partido |

Cada sesión se aplica a toda la plantilla, con pequeñas variaciones aleatorias.

---

## 3. Efectos

### Fatiga

- La fatiga afecta a la fuerza del equipo y a la selección automática.
- Un plan con demasiada carga puede dejar al equipo fundido.
- La recuperación y el descanso compensan las sesiones duras.

### Forma y moral

- La forma sube con activación, recuperación y sesiones bien planteadas.
- La moral sube con recuperación, descanso y activación.
- El físico excesivo puede bajar la moral si el equipo ya está cansado.

### Cohesión

- Táctico, vídeo, set pieces y defensa mejoran la cohesión.
- La cohesión forma parte de la puntuación de gestión y del bonus de ataque/defensa.

### Atributos

- Los jugadores jóvenes y con potencial alto progresan más.
- Las ganancias son pequeñas: +1 en un atributo con cierta probabilidad.
- No se sube todo cada semana; el objetivo es progresar en una temporada, no romper el balance.

### Preparación del rival

- Las sesiones de vídeo y táctica generan un bonus de preparación.
- Se aplica al ataque y la defensa del siguiente partido.
- Se reinicia después del partido.

### Lesiones

- El riesgo sube con la fatiga y las sesiones físicas.
- Los jugadores ya lesionados no acumulan nuevo riesgo.
- La recuperación puede acortar lesiones leves.

---

## 4. Plan automático y delegación

El plan automático usa el **rating del segundo entrenador**:

- Un segundo entrenador bueno detecta mejor cuándo toca recuperar, atacar o cerrarse.
- Un segundo entrenador flojo tiende a planes más genéricos.
- La opción de editar sigue disponible para quien quiera control total.

La IA también entrena automáticamente cada semana, para que el usuario no tenga una ventaja artificial por ser el único que planifica.

---

## 5. Menos opciones

El diseño evita saturar:

- Solo hay una pantalla semanal.
- La opción por defecto es el plan automático.
- Editar es opcional.
- Hay un plan de recuperación de un solo clic.
- No hay que gestionar cada jugador individualmente.
- El entrenamiento se aplica una vez por semana.

---

## 6. Integración

- `training.py`: sesiones, presets, plan automático y aplicación.
- `season.py`: `ensure_week_training`, `ensure_ai_training` y reinicio semanal.
- `models.py`: `week_trained`, `weekly_plan`, `training_report`, `prep_bonus`.
- `ui.py`: pantalla de entrenamiento e informe.
- `match_engine.py`: el bonus de preparación se suma al ataque y la defensa.

---

## 7. Pruebas

`manager/src/tests/test_training.py` y `test_persistence.py` cubren:

- plan automático y aplicación;
- plan de recuperación para equipos cansados;
- entrenamiento semanal y reinicio;
- entrenamiento IA una vez por ronda;
- guardado/carga del estado de entrenamiento.

```bash
cd manager
python3 -m pytest src/tests -q
```

Resultado actual: **80 tests superados**.

---

## 8. Limitaciones

- No hay entrenamiento individual por jugador.
- No hay staff especializado (preparador físico, entrenador de porteros, etc.).
- No hay desarrollo de cantera.
- El plan automático usa el rating del segundo entrenador, no un análisis completo del rival.
- La carga de entrenamiento es semanal, no diaria.
