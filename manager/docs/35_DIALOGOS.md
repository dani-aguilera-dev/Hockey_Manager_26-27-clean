# Sistema de diálogos

**Estado:** actualización implementada (2026-10-27).

## 1. Problema anterior

El sistema anterior tenía temas contextuales, pero la conversación era una sola pantalla:

- una pregunta;
- cuatro opciones;
- una respuesta breve;
- fin.

No había memoria, no había segunda ronda y muchas respuestas se sentían genéricas. Además, las promesas que aparecían en los textos no se comprobaban después.

## 2. Qué cambia

Cada conversación pasa a tener:

- apertura contextual con datos reales;
- una respuesta del entrenador;
- una reacción del jugador o del staff;
- una segunda decisión;
- cierre con consecuencias;
- transcripción completa en la UI.

Los temas usados recientemente se marcan y la conversación aleatoria evita repetirlos.

## 3. Contexto que se usa

La apertura y las opciones tienen en cuenta:

- edad, posición, overall y potencial;
- minutos, goles, asistencias y rating;
- forma, moral, fatiga y relación;
- contrato y situación de mercado;
- lesión o sanción;
- posición del equipo, forma y último resultado;
- próximo rival y forma del rival;
- moral y cohesión del grupo;
- conversaciones anteriores con ese jugador;
- promesas activas.

## 4. Temas

Jugadores:

- rol y minutos;
- rendimiento;
- desarrollo;
- confianza;
- contrato;
- recuperación;
- mercado;
- próximo rival;
- proyecto de club;
- disciplina;
- familia;
- prensa;
- conflicto con un compañero.

Staff:

- plan de entrenamiento;
- análisis del rival;
- clima del vestuario;
- mercado y ojeador;
- carga física;
- cantera;
- proyecto y junta.

## 5. Memoria y repetición

`_conversation_memory` recupera:

- última conversación;
- último tema;
- último resultado;
- días desde la última charla;
- temas recientes;
- número de conversaciones.

La UI muestra `Reciente` y `Sugerido` en el selector de temas. La conversación aleatoria pondera objetivos con peor relación, moral baja, contrato próximo a expirar, lesión o interés de mercado.

## 6. Promesas

Algunas opciones crean una promesa:

- minutos;
- renovación.

La promesa guarda:

```text
type, text, created, due, status
start_apps, target_apps
contract_before, salary_before
```

`check_promises` se ejecuta en el día a día:

- si se cumple: sube relación y moral;
- si se rompe: baja relación y moral;
- deja un evento en el diario del club.

Las promesas aparecen en la ficha del jugador.

## 7. Interfaz

- Burbujas de conversación para jugador y entrenador.
- Segunda ronda visible.
- Historial completo en el mismo mensaje.
- Badges de tema reciente/sugerido.
- Promesas en la ficha del jugador.

## 8. Persistencia

Los mensajes siguen guardándose en `GameState.chat_messages`; los campos nuevos (`turns`, `stage`, `max_stage`, `status`, `promise`) tienen valores por defecto para no romper partidas antiguas.

## 9. Pendiente

- árboles de diálogo específicos por personalidad;
- conversaciones de grupo;
- promesas de capitanía, cesión o rol;
- seguimiento de conversaciones en el inbox;
- pruebas de usuario sobre longitud y ritmo.
