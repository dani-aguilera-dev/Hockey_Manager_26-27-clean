# UI, paleta y accesibilidad

**Estado:** primera auditoría aplicada (2026-10-27).

## 1. Paleta

La interfaz usa una paleta oscura con acento dorado y azul:

| Token | Valor | Uso |
|---|---|---|
| `--bg` | `#0b1220` | Fondo principal |
| `--surface` | `#121d31` | Tarjetas |
| `--surface-2` | `#17243b` | Controles y superficies elevadas |
| `--text` | `#e8eef8` | Texto principal |
| `--muted` | `#a4b6d2` | Texto secundario |
| `--muted-2` | `#8ea3c2` | Texto terciario y ayudas |
| `--gold` | `#ffb020` | Acción principal y énfasis |
| `--blue` | `#5aa9ff` | Información y foco |
| `--ok` | `#43d17c` | Éxito |
| `--warn` | `#ffcc66` | Advertencia |
| `--danger` | `#ff6b6b` | Error o riesgo |

Se subió `--muted-2` desde `#7185a4` porque no llegaba a 4,5:1 sobre varias superficies. Los pares principales quedan por encima de WCAG AA:

- texto principal sobre fondo: 16,06:1;
- texto secundario sobre tarjeta: 8,19:1;
- texto terciario sobre tarjeta: 6,56:1;
- texto terciario sobre superficie elevada: 6,04:1;
- azul sobre tarjeta: 6,87:1;
- rojo de peligro sobre su fondo: 5,56:1.

## 2. Botones y controles

- Los botones principales usan dorado con texto oscuro.
- Los botones secundarios usan superficie elevada con borde.
- Los botones peligrosos usan fondo rojo oscuro y texto claro.
- Los botones de icono tienen `aria-label`.
- Los controles tienen un mínimo de 32 px de alto; los principales, 40 px.
- Los formularios usan `label` real, no placeholders como única etiqueta.
- Los estados deshabilitados reducen opacidad y bloquean el clic.

## 3. Foco y teclado

Se añadió un foco visible para:

- enlaces;
- botones;
- pestañas;
- botones de texto;
- campos, selects y textareas.

El modal:

- se abre con `role="dialog"` y `aria-modal="true"`;
- enfoca el primer control;
- atrapa el foco con `Tab` y `Shift+Tab`;
- se cierra con `Escape`;
- devuelve el foco al elemento anterior al cerrarse.

## 4. Decisiones

La nueva pantalla `Decisiones` permite:

- ver pendientes;
- ver prioridad y caducidad;
- elegir entre todas las opciones;
- consultar el historial;
- distinguir resueltas, caducadas, retiradas y rechazadas.

El dashboard muestra las decisiones pendientes y enlaza al historial.

## 5. Pendiente

- auditoría con lector de pantalla real;
- prueba de reflow al 400 %;
- revisión de contraste en imágenes y escudos;
- navegación por flechas en pestañas;
- estados de carga anunciados con `aria-live`;
- revisión de todos los textos alternativos.
