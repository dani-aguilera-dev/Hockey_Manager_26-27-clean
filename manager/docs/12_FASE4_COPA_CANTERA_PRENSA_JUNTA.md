# Fase 4 — Copa, cantera, prensa y junta

**Estado:** implementado (2026-10-20).

---

## 1. Copa del Rey

Formato oficial:

- **8 equipos: los 8 mejores de DHA al terminar la primera vuelta** (jornada 11).
- **No participan equipos de DHB.**
- Cuartos de final, semifinal, **tercer/cuarto puesto** y final **a partido único**.
- Se disputa en un fin de semana, con sede en un club DHA.
- Empate en eliminatoria → shootout.
- El campeón recibe **50.000 €** y confianza para la junta.
- Si tu equipo gana, la afición sube.

Clasificación: 1º vs 8º, 2º vs 7º, 3º vs 6º y 4º vs 5º.

En el dashboard:

```text
C. Copa del Rey
```

Opciones:

- `[J]` jugar la ronda actual.
- `[S]` simular la ronda.
- `[A]` simular la Copa entera.
- `[V]` volver.

Si no juegas la Copa durante la temporada, se completa automáticamente antes del resumen final.

---

## 2. Cantera

Cada club tiene:

- **Academia (0-100)** según instalaciones.
- **Jugadores juveniles** con edad, posición, overall, potencial, salario y contrato.

En el dashboard:

```text
K. Cantera
```

Puedes:

- `[P]` promover un juvenil al primer equipo.
- `[R]` liberar un juvenil.
- Ver el desarrollo y el potencial.

Al final de cada temporada:

- los juveniles envejecen y progresan;
- se genera una nueva generación;
- los juveniles mayores de 20 años salen de la cantera si no se les promociona;
- los equipos con menos de 18 jugadores promocionan juveniles automáticamente.

---

## 3. Rueda de prensa

En el dashboard:

```text
P. Rueda de prensa
```

Cada jornada hay dos preguntas con tres respuestas posibles. Los efectos son pequeños pero acumulativos:

- moral del equipo;
- confianza de la afición;
- confianza de la junta.

Las respuestas quedan registradas en el historial de prensa.

---

## 4. Junta directiva dinámica

La junta ahora tiene:

- objetivo de temporada;
- confianza;
- presión;
- paciencia.

Al final de la temporada se hace una **revisión**:

- se compara la posición final con el objetivo;
- si se cumple, sube la confianza y el presupuesto de fichajes;
- si no se cumple, baja la confianza y el presupuesto;
- si la confianza queda muy baja, aparece riesgo de destitución.

La revisión se guarda en el resumen de temporada y en el historial.

---

## 5. Archivos

- `manager/src/cup.py`: cuadro y calendario de Copa.
- `manager/src/youth.py`: cantera, desarrollo, intake y promoción.
- `manager/src/press.py`: preguntas, respuestas y efectos.
- `manager/src/season.py`: simulación de Copa, revisión de junta y transición de temporada.
- `manager/src/ui.py`: pantallas de Copa, cantera, prensa y revisión.

---

## 6. Pruebas

`manager/src/tests/test_phase4.py` cubre:

- cuadro y rondas de Copa;
- promoción y desarrollo de canteranos;
- rueda de prensa;
- revisión de la junta.

```bash
cd manager
python3 -m pytest src/tests -q
```

Resultado actual: **80 tests superados**.

---

## 7. Limitaciones

- La Copa no tiene sorteo con cabezas de serie ni eliminatorias a doble partido.
- La cantera no tiene ojeadores dedicados ni decisiones de formación individual.
- La prensa es un cuestionario fijo, no un sistema de rumores.
- La junta no destituye de forma interactiva; avisa del riesgo.
- La DHB no desciende a 1ª Andaluza porque esa liga no se simula.
