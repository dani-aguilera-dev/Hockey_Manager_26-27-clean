# Auditoría de accesibilidad

## Método

- **Herramienta:** `axe-core 4.14.1` sobre Chromium con Playwright.
- **Reglas:** WCAG 2.0/2.1/2.2 niveles A y AA (`wcag2a`, `wcag2aa`,
  `wcag21a`, `wcag21aa`, `wcag22aa`).
- **Pantallas de escritorio:** dashboard, calendario, plantilla, táctica,
  mercado, entrenamiento, previa, informe, junta, finanzas y seguimiento.
- **Pantallas móviles (390×844):** dashboard, calendario, plantilla y táctica.
- **Teclado:** primer `Tab`, enlace de salto, destino del foco y nombres de la
  navegación principal.

Comando:

```bash
cd manager/web/frontend
npm run test:a11y
```

## Resultado

```json
{"pages":{"dashboard":{"violations":0,"passes":23},"calendar":{"violations":0,"passes":22},"squad":{"violations":0,"passes":19},"tactics":{"violations":0,"passes":26},"market":{"violations":0,"passes":18},"training":{"violations":0,"passes":13},"match":{"violations":0,"passes":13},"report":{"violations":0,"passes":24},"board":{"violations":0,"passes":19},"finance":{"violations":0,"passes":23},"shortlist":{"violations":0,"passes":18},"options":{"violations":0,"passes":21},"mobile-dashboard":{"violations":0,"passes":22},"mobile-calendar":{"violations":0,"passes":21},"mobile-squad":{"violations":0,"passes":19},"mobile-tactics":{"violations":0,"passes":25}},"violations":[],"keyboard":{"skipLink":true,"skipTarget":"main","navLinks":45},"serious":0,"totalViolations":0,"ok":true,"suite":"a11y","ms":20358}
```

- **0 violaciones** en 16 combinaciones pantalla/viewport.
- **0 graves o críticas**.
- El primer `Tab` enfoca “Saltar al contenido”; `Enter` mueve el foco a
  `<main id="main" tabIndex="-1">`.
- La navegación principal expone 45 enlaces con nombre accesible.

## Correcciones aplicadas

| Hallazgo | Corrección |
| --- | --- |
| `label-content-name-mismatch` en los slots de táctica | El nombre accesible sale del contenido visible; se eliminó el `aria-label` que no incluía el nombre del jugador |
| El salto de contenido dejaba el foco en `body` | `<main id="main" tabIndex={-1}>` |
| `target-size` en los partidos del calendario | `.month-event` con `min-height: 24px` |
| `scrollable-region-focusable` en la crónica | `role="region"`, `aria-label` y `tabIndex={0}` en `.event-list` |

## Límites

- axe-core es una auditoría automatizada: no sustituye una prueba manual con
  NVDA, JAWS o VoiceOver. En este entorno no hay lector de pantalla instalado,
  así que **no se reclama** una auditoría manual completa.
- No se han auditado los 50+ flujos de la regresión completa, solo las
  pantallas clave de escritorio y móvil.
- El contraste se comprueba con las reglas de axe; no hay medición manual de
  todos los estados hover/focus.
