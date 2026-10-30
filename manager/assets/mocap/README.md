# Mocap CMU · carrera (subject 9, trial 1)

Clip de captura de movimiento real usado por el visor 3D para la locomoción de
los jugadores. El clip es una carrera capturada por el Graphics Lab de Carnegie
Mellon University.

## Fuente y licencia

- Dataset: **CMU Graphics Lab Motion Capture Database**
- Página: <http://mocap.cs.cmu.edu/>
- Sujeto: **9**
- Ensayo: **1**
- Movimiento: **run**
- ASF: <http://mocap.cs.cmu.edu/subjects/09/09.asf>
- AMC: <http://mocap.cs.cmu.edu/subjects/09/09_01.amc>
- Licencia publicada en las FAQ del dataset: *“The motion capture data may be
  copied, modified, or redistributed without permission.”*
  (<http://mocap.cs.cmu.edu/faqs.php>, consultado el 2026-10-30>)
- Atribución: *Motion data courtesy of Carnegie Mellon University Graphics Lab
  Motion Capture Database.*

## Archivos

```text
source/09.asf             # esqueleto ASF original
source/09_01.amc          # captura AMC original (120 fps)
cmu_09_01_run.json        # clip derivado y reducido a 60 fps para el visor
```

## Conversión

`cmu_09_01_run.json` conserva por frame:

- `lb`: rotación de `lowerback` (grados).
- `lf` / `rf`: flexión de fémur izquierdo/derecho.
- `lt` / `rt`: flexión de tibia izquierda/derecha.
- `lfoot` / `rfoot`: rotación de pie.

Se muestrea cada dos frames (120 → 60 fps) y se redondea a dos decimales. El
visor aplica estos valores a los grupos de piernas y cadera del jugador
procedural. Es un retargeting estilizado, no una réplica biomecánica del hockey.

## Límites

- No es mocap específico de hockey.
- No incluye tejido, colisiones de tela ni captura facial.
- No sustituye una pipeline AAA de animación o física.
