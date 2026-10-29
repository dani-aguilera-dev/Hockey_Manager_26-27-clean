# Táctica específica de hockey

Esta actualización sustituye la táctica genérica por un modelo de hockey con
sistemas de bloque, marcaje, salida, ataque, activadores de presión y roles
manuales de balón parado.

## Fuentes consultadas

La terminología y el diseño se contrastaron con fuentes de entrenamiento y
reglamento:

- **Hockey Training — Marking**: distingue marcaje zonal, individual y
  *match-up* (mixto). https://www.hockeytraining.co.uk/marking
- **Tactical Field Hockey**: defensa zonal y presión al portador en individual.
  https://tacticalfieldhockey.wordpress.com/blog
- **NFHCA — Penalty Corner Toolkit**: inserter, hitter, L1/L2/R1/R2, opciones de
  desvío y rebote. https://nfhca.org/wp-content/uploads/2022/07/PCS-NFHCA_NewCoachToolkit_2022.pdf
- **FIH Rules of Hockey 2023**: reglas del penalty stroke, un solo toque y
  posición del portero. https://www.fih.hockey/static-assets/pdf/fih-rules-of-hockey-June23-update.pdf
- **bcuckow Analysis & Coaching — Modern field hockey tactics**: 4-3-3, 3-4-3,
  outletting, build-up y cambios de sistema.
  https://bcuckowanalysisandcoaching.wordpress.com/2014/06/29/a-guide-to-modern-field-hockey-tactics
- **Field Hockey BC — General Tactical Instruction**: marcaje zonal, doble
  defensa y salidas. https://fieldhockeybc.com/wp-content/uploads/2016/11/GeneralTacticalMay07.pdf

## Sistemas disponibles

### Defensa

- **Zona baja · low block**: protege el círculo, cede posesión y reduce espacios
  interiores.
- **Zona media · mid block**: equilibrio entre compactación y salida.
- **Zona alta · high block**: ahoga la salida rival y fuerza errores, con coste
  físico.
- **Individual todo el campo**: cada defensor sigue a su referencia en todo el
  campo; máxima intensidad y riesgo.
- **Individual mixta · match-up**: zonas de referencia con responsabilidad
  individual sobre el hombre que entra en la zona.

### Ataque

- Ataque posicional.
- Contraataque.
- Juego directo.
- Juego por bandas.
- Juego interior.
- Sobrecarga derecha.
- Sobrecarga izquierda.

### Salida / build-up

- Salida con portero.
- Salida por central.
- Salida por lateral.
- Salida directa.

### Activadores de presión

- Tras pérdida.
- Saque de fondo rival.
- Recepción en banda.
- Pase atrás rival.
- Presión constante.

## Balón parado

### Penalty corner

Roles asignables manualmente:

- **Sacador / injector**: pone la bola en juego.
- **Parador / stopper**: controla la recepción.
- **Tirador / flicker**: ejecuta el drag flick o tiro principal.
- **Desviador / deflector**: ataca la trayectoria.
- **Rechace / rebounder**: caza el rebote y empuja.
- **Primer defensor de PC**: primer *runner* para presionar el saque rival.
- **Portero de PC**: portero especialista en penalty corners.

Rutinas:

- Flick directo.
- Slip izquierda.
- Slip derecha.
- Desvío.
- Rebote.
- Variación.

### Penalty stroke

- **Lanzador de penalty stroke** asignable.
- **Portero de penalty stroke** asignable.
- El lanzador manual también abre la tanda de shootout.

### Golpes francos

- Especialista en golpes francos.

## Motor

`manager/src/models.py` incorpora los modificadores de los nuevos sistemas en
`attack_mod`, `defense_mod` y `fatigue_mod`. `TeamState.specialists` prioriza
los jugadores asignados manualmente y, si no están en el once, cae al mejor
atributo disponible.

`manager/src/match_engine.py` usa:

- el sacador, parador, tirador, desviador y rechace en el penalty corner;
- el portero de PC del rival;
- la rutina de PC elegida;
- el lanzador y portero de penalty stroke;
- el lanzador manual en la tanda de shootout.

La UI está en `web/frontend/src/pages/Tactics.tsx` y la API en
`/api/tactics` (GET/POST).

## Tests

- Modificadores de sistemas de hockey.
- Asignación manual de especialistas.
- Compatibilidad con partidas antiguas.
- Motor y API.

Total actualizado: **100 tests**.
