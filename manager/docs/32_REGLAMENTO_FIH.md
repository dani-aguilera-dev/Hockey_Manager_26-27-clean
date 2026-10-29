# Reglamento FIH aplicado al juego

**Referencia:** FIH Rules of Hockey. Edición 2026 (efectiva desde el 1 de marzo de 2026) y edición 2027 (efectiva desde el 1 de noviembre de 2026).

La temporada 2026-27 empieza con el reglamento de 2026 y pasa al de 2027 el 1 de noviembre. Para el motor usamos la edición **2027** como referencia principal, porque es la que cubre la mayor parte de la temporada, y dejamos preparado el cambio de reglas.

## Fuentes oficiales

- FIH Rules of Hockey 2026: <https://www.fih.hockey/static-assets/pdf/fih-Rules-of-hockey-2026-final.pdf>
- FIH Rules of Hockey 2027: <https://www.fih.hockey/static-assets/pdf/2026_09_14_fih_rules_of_hockey_2027_clean.pdf>
- Documento oficial de la FIH: <https://www.fih.hockey/about-fih/official-documents/rules-of-hockey>
- Traducción federativa española de 2026: <https://www.fmhockey.es/documentos/reglhhierba.pdf>

## 1. Partido y equipos

- Un partido tiene **cuatro cuartos de 15 minutos**.
- Hay un intervalo de **2 minutos** entre el primer y segundo cuarto y entre el tercero y el cuarto.
- El descanso entre el segundo y el tercer cuarto es de **10 minutos**.
- Cada equipo tiene **11 jugadores en el campo** y un máximo de **16 personas** en la convocatoria: 11 titulares y hasta 5 suplentes.
- Las sustituciones son **ilimitadas y rodantes**. No hace falta parar el tiempo, salvo en sustituciones de portero.
- Los jugadores entran y salen por la zona central, a menos de 3 metros de la línea de centro.
- No se puede sustituir a un jugador suspendido mientras dura su suspensión.
- Después de cumplir la suspensión, el jugador puede ser sustituido sin volver antes al campo.
- Durante un penalty corner no se puede sustituir, salvo por lesión o suspensión del portero defensor.
- Si el portero es suspendido, el equipo defensor juega con un jugador menos.
- Un jugador lesionado o sangrando debe salir del campo, salvo que motivos médicos lo impidan, y no puede volver hasta que la herida esté cubierta.

**Nota para el juego:** el motor ya usa 4×15 y la base de 16 convocados con 5 suplentes. Las competiciones concretas podrán variar el número de suplentes.

## 2. Tarjetas y suspensiones

La regla 14 regula las sanciones personales.

| Sanción | Duración | Efecto en el equipo | Vuelta |
|---|---:|---|---|
| Amonestación verbal | — | Ninguno | — |
| Tarjeta verde | **2 minutos** de tiempo de juego | Juega con uno menos | Al cumplir los 2 minutos |
| Tarjeta amarilla | **5 o 10 minutos** de tiempo de juego | Juega con uno menos | Al cumplir la suspensión |
| Tarjeta roja | **Resto del partido** | Juega con uno menos hasta el final | No vuelve |

Reglas importantes de la edición 2027:

- Un mismo jugador **no debe recibir dos tarjetas verdes ni dos amarillas** en el mismo partido, aunque sean faltas distintas.
- Si ya tiene una sanción personal, la siguiente falta que merezca tarjeta debe recibir una **categoría superior**.
- Excepción: las tarjetas por una falta de equipo (por ejemplo, la regla 2.1 o 3.4 sobre el capitán) no cuentan para esa progresión.
- La tarjeta amarilla es de **5 o 10 minutos**, según la gravedad.
- La tarjeta roja implica expulsión del partido. El reglamento permite que las regulaciones de la competición añadan suspensiones posteriores.
- Un jugador suspendido temporalmente puede reunirse con el equipo en el intervalo, pero debe volver al lugar designado para completar la suspensión.
- Al terminar la suspensión, el jugador debe volver al campo cerca de la línea de centro, salvo que sea sustituido.
- El tiempo de suspensión es **tiempo de juego**, no tiempo real.
- Las tarjetas también se pueden mostrar a miembros del cuerpo técnico en la edición 2027; si ocurre, el equipo juega con uno menos.

### Diferencia 2026 / 2027

- **2026:** amarilla = mínimo 5 minutos.
- **2027:** amarilla = 5 o 10 minutos.
- **2027:** se prohíbe expresamente que el mismo jugador reciba dos verdes o dos amarillas en el mismo partido.
- **2027:** se regulan las tarjetas a miembros del cuerpo técnico.

## 3. Penalti córner y penalti stroke

Resumen de las reglas que afectan al motor:

- El penalty corner se concede por faltas defensivas dentro del círculo que no impiden un gol probable, por faltas intencionadas del defensor en el círculo, por faltas intencionadas fuera del círculo dentro de los 23 metros y por jugar intencionadamente la bola por la línea de fondo.
- El penalty stroke se concede cuando una falta defensiva dentro del círculo impide un gol probable, o cuando hay una falta intencionada sobre un atacante con posesión o con oportunidad de jugar la bola.
- En el penalty corner, el inyector debe tener al menos un pie fuera del campo.
- El resto de atacantes deben estar fuera del círculo.
- No puede haber más de cinco defensores detrás de la línea de fondo, incluido el portero.
- Los demás defensores deben estar más allá de la línea de centro.
- Hasta que se juega la bola, ningún atacante que no sea el inyector puede entrar en el círculo.
- El inyector no puede volver a jugar la bola hasta que la juegue otro jugador.
- No se puede marcar gol hasta que la bola haya salido del círculo.
- El partido se prolonga al final de cada cuarto para completar un penalty corner o un penalty stroke.
- El penalty stroke se lanza desde el punto de penalty stroke, a 6,40 metros de la línea de gol.
- El portero debe tener ambos pies sobre la línea de gol hasta que suene el silbato.
- El lanzador no puede lanzar hasta que suene el silbato.

## 4. Lesiones y protocolo médico

- El reglamento FIH obliga a salir del campo al jugador lesionado o sangrando.
- La vuelta exige que la herida esté cubierta y que no haya ropa manchada.
- Las sustituciones por lesión son posibles, pero el reglamento no convierte la lesión en una decisión táctica automática.
- Los protocolos de conmoción cerebral dependen de la competición y de las regulaciones médicas; no están desarrollados en las Reglas de Hockey.
- Para el juego vamos a separar **lesión** de **sanción**:
  - lesión: disponibilidad física, recuperación y riesgo de recaída;
  - sanción: tarjetas, comité y partidos de suspensión.

## 5. Estado de implementación

**Hecho en esta primera fase:**

1. `QUARTER_MINUTES` está en **15**.
2. Tarjeta verde: **2 minutos**.
3. Tarjeta amarilla: **5 o 10 minutos**.
4. Tarjeta roja: resto del partido y posible sanción posterior.
5. Suspensión temporal real: el equipo juega con uno menos.
6. Las tarjetas se guardan con minuto, duración, motivo y tipo.
7. El parte del partido incluye tarjetas y lesiones.
8. Las lesiones guardan tipo, gravedad, partidos estimados e historial.
9. El auto-once ya no debería alinear a un jugador no disponible; queda revisar el caso de emergencia con menos de 11.

**Pendiente:**

- ajustar la convocatoria de la interfaz de 7 a 5 suplentes;
- definir la llamada a cantera cuando haya menos de 11 disponibles;
- completar la rehabilitación y el riesgo de recaída;
- confirmar las variaciones de competición RFEH/DHA.

## 6. Decisiones de implementación

Para esta primera fase:

- `RULESET = "FIH_2027"`.
- Cuartos de **15 minutos**.
- Verde: **2 minutos**.
- Amarilla: **5 o 10 minutos**, según gravedad.
- Roja: resto del partido.
- El equipo juega con uno menos durante la suspensión.
- La roja puede generar **1 partido de sanción posterior** como simplificación de competición; el módulo disciplinario podrá ampliarlo.
- Verde y amarilla **no** generan sanción para el partido siguiente.
- El parte incluirá tarjetas con minuto, duración y motivo.
- Las lesiones se irán ampliando en el siguiente bloque con tipo, gravedad y rehabilitación.

## 7. Pendiente de competición

Las reglas FIH permiten que las competiciones varíen algunos aspectos. Antes de cerrar el balance hay que confirmar con las bases RFEH/DHA:

- número exacto de convocados y suplentes;
- duración de las amarillas en competición nacional;
- suspensiones posteriores por roja;
- protocolo de conmoción cerebral;
- uso de video umpire.
