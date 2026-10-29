# Cómo se juega al hockey hierba

Guía de referencia para entender el deporte, sus reglas, sus fases y sus acciones específicas. Está pensada para que el modelo de atributos y el simulador tengan una base conceptual sólida, y para que cualquier persona pueda interpretar el juego sin haber jugado antes.

---

## 1. Idea general

El hockey hierba (field hockey) es un deporte de equipo de 11 jugadores por lado: 10 jugadores de campo y 1 portero. El objetivo es introducir una bola pequeña y dura en la portería rival usando un stick curvo. Se juega normalmente sobre césped artificial, en una superficie rápida que premia la técnica, la lectura y la condición física.

El hockey moderno es muy fluido: las posiciones no son estáticas y los jugadores intercambian espacios continuamente. Un lateral puede acabar en el área, un medio puede cubrir el carril central y un delantero puede presionar en la primera línea. Por eso el modelo de atributos usa **demarcaciones** y **roles**, no solo una posición fija.

---

## 2. El campo

| Elemento | Medida |
|---|---|
| Largo | 91,4 m |
| Ancho | 55 m |
| Portería | 3,66 m de ancho × 2,14 m de alto |
| Círculo de disparo (“la D”) | 14,63 m desde la línea de fondo |
| Línea de 23 m | 22,90 m desde la línea de fondo |
| Punto de stroke | 6,40 m desde el centro de la portería |
| Marcas de PC | 10 m desde el poste, sobre la línea de fondo |
| Línea de 5 m | A 5 m del círculo, para PC y saques |

El campo tiene:

- **Línea de fondo** (backline) y **línea de banda**.
- **Círculo de disparo**: solo se puede marcar desde dentro del círculo.
- **Línea de 23 m**: delimita la zona donde ciertas faltas se sancionan con PC.
- **Punto de stroke**: a 6,40 m de la portería.
- **Marcas de PC**: a 10 m del poste, sobre la línea de fondo.
- **Línea de 5 m**: referencia para la defensa de PC y la distancia en faltas.

La bola es dura, de 156-163 g y 71,3-74,8 mm de diámetro. El stick es curvo, con una cara plana y una parte redondeada; solo se puede jugar con la cara plana (y con los bordes permitidos), nunca con la parte redondeada.

### Superficies

- **Water-based**: la más rápida; habitual en élite.
- **Sand-dressed**: intermedia.
- **Sand-filled**: más lenta; habitual en categorías inferiores.
- **Hierba natural**: cada vez menos frecuente.

La superficie condiciona la velocidad de la bola, el bote y el desgaste físico.

---

## 3. Formato de partido

### FIH

- 4 cuartos de **15 minutos**.
- 2 minutos entre cuartos.
- 15 minutos de descanso al medio tiempo (en algunos formatos, 5).
- Tiempo parado en goles y PC en los últimos minutos, según reglamento.

### RFEH (España)

- 4 tiempos de **17 minutos y 30 segundos**.
- 2 minutos entre el 1.º y 2.º; 10 minutos entre el 2.º y 3.º; 2 minutos entre el 3.º y 4.º.
- El tiempo no se para en penaltis córner ni en goles.
- Acta: máximo 18 jugadores con 2 porteros, o 16 con 1 portero.
- Mínimo para empezar: 8 jugadores (4 en sala).
- Mínimo para continuar: 7 jugadores (3 en sala).

### Puntuación

- Victoria: 3 puntos.
- Empate: 1 punto.
- Derrota: 0 puntos.
- En eliminatorias, si hay empate se juega prórroga o shoot-out según el reglamento.

### Sustituciones

- **Rodantes e ilimitadas**.
- Se realizan por la línea de medio campo.
- No se para el juego (salvo sustitución de portero o lesión).
- No se puede sustituir entre la concesión y el final de un penalty corner, salvo lesión o suspensión del portero defensor.
- Un jugador expulsado no puede ser sustituido.

### Tarjetas

| Tarjeta | Efecto |
|---|---|
| Verde | Aviso; en competición internacional, 2 minutos fuera. |
| Amarilla | Suspensión temporal de 5 o 10 minutos, según el árbitro. |
| Roja | Expulsión definitiva; sin sustitución. |

Las tarjetas no son acumulativas como en fútbol: un jugador puede recibir varias verdes o amarillas, pero la segunda debe ser más grave. Las regulaciones locales pueden variar.

---

## 4. Posiciones y roles

El hockey se describe mejor por **líneas** y **funciones** que por posiciones rígidas.

### 4.1. Portero

- Único jugador que puede usar manos, pies, kickers y guantes dentro de su círculo.
- Lleva casco, peto, espinilleras, kickers, guantes y protección.
- Puede jugar fuera del círculo solo con el stick.
- No puede cruzar la línea de 23 m, salvo para lanzar un stroke.
- Puede ser sustituido por un jugador de campo (“kicking back”), que no tiene privilegios de portero.

Funciones:

- Parar tiros, PC y strokes.
- Dominar el área y las salidas.
- Comunicar la defensa.
- Iniciar el juego con saques precisos.
- Leer el 2 contra 1 y el 3 contra 2.

### 4.2. Defensas

#### Central

- Organiza la defensa y la línea de fondo.
- Cubre el carril central, las ayudas y el segundo palo.
- Defiende el PC como primer runner, segundo runner o poste.
- Puede ser drag flicker o stopper en ataque.
- Debe tener buena cobertura, posicionamiento, fuerza, pase y liderazgo.

#### Lateral

- Defiende el carril exterior y acompaña la subida del extremo.
- Debe tener velocidad, resistencia, cobertura y buen pase.
- Participa en la salida de balón y en el pressing.
- En ataque puede generar superioridad por banda.

### 4.3. Medios

- Conectan defensa y ataque.
- Pueden ser **mediocentros** (equilibrio, cobertura, pase), **interiores** (creación, conducción) o **carrileros** (recorrido, presión).
- Son clave en la posesión, la transición y el pressing.
- Suelen ser los inyectores de PC y los especialistas en faltas.
- Deben tener pase, posicionamiento, resistencia, pressing y lectura.

### 4.4. Delanteros

- Finalizan jugadas y presionan la salida rival.
- Pueden ser **delanteros de área** (remate, desvío, PC), **delanteros de espacio** (velocidad, ruptura) o **extremos** (1 contra 1, fondo).
- Son los principales definidores, desviadores y tiradores de stroke.
- Deben tener definición, velocidad, regate 3D, desmarque y lectura.

### 4.5. Formaciones

El hockey moderno usa formaciones fluidas:

- 4-3-3.
- 3-4-3.
- 3-3-3-1.
- 3-2-1-4.
- 5 medios, 2 delanteros.
- 3 atrás, 5 en medio, 2 arriba.

Lo importante no es el número, sino:

- ocupar carriles;
- generar superioridad;
- mantener amplitudes;
- cubrir el centro;
- presionar tras pérdida;
- replegar con orden.

---

## 5. Habilidades técnicas

### 5.1. Control y recepción

- Recibir de revés y de derecha.
- Controlar con la mano (solo el portero en el círculo; los jugadores de campo pueden usar la mano si sujetan el stick, pero no para jugar la bola).
- Orientar el primer toque para salir de la presión.
- Proteger la bola con el cuerpo y el stick.

### 5.2. Pase

- **Push**: pase raso, preciso, con las dos manos.
- **Hit**: golpeo potente, con swing; se usa para pases largos y tiros.
- **Slap**: golpeo con la stick cerca del suelo; rápido y preciso.
- **Sweep**: barrido; útil en movimiento y para levantar la bola.
- **Flick / scoop**: elevado; para pasar por encima de un rival o para el aerial.

### 5.3. Conducción y regate

- **Conducción** con la bola pegada al stick.
- **Indian dribble**: giros rápidos del stick sobre la bola.
- **Regate 3D**: levantar la bola sobre el stick o el cuerpo del rival y volver a controlarla.
- **Cambios de dirección** y aceleración.
- **Protección de bola** con el cuerpo.

### 5.4. Tiro

- **Hit**: máximo potencia; el primer tiro de PC debe ir por debajo del backboard si es hit.
- **Slap**: rápido, con menos swing.
- **Sweep**: en movimiento.
- **Flick**: elevado y colocado.
- **Drag flick**: técnica de PC; se arrastra la bola y se flicka en el último momento.
- **Desvío**: cambiar la trayectoria de un tiro o centro.

### 5.5. Defensa

- **Tackle**: meter el stick en la trayectoria de la bola.
- **Jab tackle**: pinchazo rápido.
- **Bloqueo**: interponer el stick.
- **Pressing**: presionar al portador y las líneas de pase.
- **Cobertura**: ayudar al compañero batido.
- **Basculación**: mover la línea defensiva hacia el lado de la bola.

### 5.6. Juego aéreo

- **Scoop / aerial**: elevar la bola por encima de los rivales.
- **Recepción**: controlar la bola que cae con el stick.
- **Regla de los 5 m**: el rival debe estar a 5 m del receptor.
- **Seguridad**: no se puede jugar la bola de forma peligrosa contra un adversario.

---

## 6. Fases del juego

### 6.1. Ataque

1. **Salida**: el portero o un defensa inicia; se busca superioridad numérica.
2. **Progresión**: el medio conecta con los carriles exteriores o el centro.
3. **Creación**: se genera espacio con desmarques, bloqueos, conducciones y paredes.
4. **Finalización**: remate dentro del círculo, PC o stroke.
5. **Rebote**: segunda jugada tras parada o poste.

Principios:

- Ampliar el campo.
- Fijar y pasar.
- Generar superioridad.
- Atacar el círculo con intención.
- Tener cobertura detrás de la bola.

### 6.2. Defensa

1. **Pressing**: el delantero presiona la salida.
2. **Bloque medio**: el equipo cierra el centro y orienta a la banda.
3. **Bloque bajo**: defensa cerca del círculo, con coberturas.
4. **Recuperación**: tras pérdida, presión inmediata o repliegue.

Principios:

- Cerrar el centro.
- Orientar al rival a la banda.
- Mantener distancias.
- No meter el stick a lo loco.
- Proteger el segundo palo.
- Evitar PC innecesarios.

### 6.3. Transiciones

- **Ataque-defensa**: presión tras pérdida durante 3-5 segundos; si no se recupera, replegar.
- **Defensa-ataque**: salir rápido al espacio, buscar el 2 contra 1.
- **Reorganización**: si no hay superioridad, volver a estructura.

---

## 7. Set pieces: el corazón del hockey moderno

Una parte importante de los goles llega de acciones a balón parado, especialmente del penalty corner. Por eso el modelo tiene atributos específicos y especialistas.

### 7.1. Penalty corner (PC)

#### Cuándo se concede

- Falta de un defensor dentro del círculo que no evita un gol probable.
- Falta intencionada de un defensor dentro del círculo contra un rival sin posesión.
- Falta intencionada de un defensor fuera del círculo pero dentro de su área de 23 m.
- Jugar deliberadamente la bola por encima de la línea de fondo.
- Bola atrapada en la ropa o el equipo de un defensor dentro del círculo.
- Salida repetida antes de tiempo en un PC anterior.

#### Procedimiento

- **Cinco defensores** detrás de la línea de fondo, incluido el portero; el resto detrás de la línea de medio campo.
- La bola se coloca en la marca de PC, a 10 m del poste, sobre la línea de fondo.
- Un atacante (inyector) pone la bola en juego.
- El resto de atacantes espera fuera del círculo.
- La bola debe salir del círculo antes de que se pueda marcar.
- El primer tiro, si es **hit**, debe cruzar la línea de gol por debajo del backboard (460 mm). Si es **flick, scoop, push o desvío**, puede ir más alto, siempre que no sea peligroso.
- El PC termina cuando se marca, la bola sale por la línea de fondo, se concede stroke, se concede falta o la bola se aleja más de 5 m del círculo.

#### Roles atacantes

| Rol | Función |
|---|---|
| **Inyector** | Saque preciso y rápido desde la marca. |
| **Stopper** | Para/controla el saque en la parte superior del círculo. |
| **Drag flicker** | Tira el PC con drag flick. |
| **Desviador** | Desvía el tiro en el primer palo o en el área. |
| **Reboteador** | Busca el rechace y la segunda jugada. |
| **Tirador alternativo** | Puede recibir, pasar o tirar si la jugada se rompe. |

#### Variantes

- **Directo**: el drag flicker tira directamente tras el saque.
- **Slip izquierda/derecha**: el stopper pasa al lado y otro jugador tira.
- **Desvío**: el tiro se dirige al primer palo para que un compañero lo desvíe.
- **Rebote**: se busca el rechace del portero.
- **Jugada ensayada**: pases cortos para cambiar el ángulo.

#### Defensa del PC

| Rol | Función |
|---|---|
| **Portero** | Cubre el primer palo y el centro; decide salir o quedarse. |
| **Primer runner** | Sale desde la línea de fondo al saque; presiona al stopper/flicker. |
| **Segundo runner** | Cubre el hueco del primer runner y el desvío. |
| **Postes** | Protegen el primer y segundo palo. |
| **Flyer** | Sale por fuera para presionar el saque o el pase. |
| **Reboteadores** | Cubren el rechace y la segunda jugada. |

El primer runner no puede salir antes de que la bola se ponga en juego. Si sale repetidamente antes, se puede conceder stroke.

#### Por qué es tan importante

- Genera goles sin necesidad de jugada abierta.
- Permite explotar la potencia y la precisión de especialistas.
- Obliga a defender con roles muy definidos.
- Un PC bien entrenado puede valer varios goles por temporada.

### 7.2. Penalty stroke

#### Cuándo se concede

- Falta de un defensor en el círculo que evita un gol probable.
- Falta deliberada en el círculo.
- Salidas repetidas antes de tiempo en un PC.

#### Procedimiento

- Un atacante tira desde el punto de stroke, a 6,40 m.
- Solo el portero defiende.
- El resto de jugadores espera fuera del círculo/23 m.
- El tirador puede usar push, flick o scoop; no puede volver a jugar la bola hasta que la toque otro.
- Si se falla, el juego se reanuda con un golpe de 16 yardas para el equipo defensor.
- El portero puede usar todo el equipo protector; el tirador no puede hacer amagos antirreglamentarios.

#### Roles

- **Tirador**: definición, sangre fría, stroke_shot.
- **Portero**: reflejos, lectura, stroke_save.
- **Reboteadores**: por si hay rechace.

### 7.3. Free hit (falta)

- Se concede por faltas fuera del círculo.
- La bola debe estar parada.
- Los rivales deben estar a **5 m**.
- Se puede jugar en cualquier dirección.
- **Self-pass**: el jugador puede pasarse a sí mismo y continuar.
- En el área de 23 m atacante, la bola debe recorrer **5 m** antes de entrar en el círculo; no se puede tirar directamente desde una falta dentro de la zona de 23 m.
- Si la falta es de un atacante dentro de los 23 m rivales, se concede un golpe de 16 yardas al defensor.

### 7.4. Golpe de 16 yardas

- Se concede cuando la bola sale por la línea de fondo:
  - tras ser tocada por un atacante;
  - tras ser desviada involuntariamente por un defensor.
- Se ejecuta desde la línea de 16 yardas (14,63 m), en línea con el punto de salida.
- Los rivales deben estar a 5 m.
- Es una falta, no un PC.

### 7.5. Córner largo

- Se concede cuando un defensor juega la bola por encima de la línea de fondo **sin intención**.
- Se ejecuta como falta desde la línea de 23 m, en línea con el punto de salida.
- Si es intencionado, se concede **PC**.

### 7.6. Saque de banda

- Se ejecuta desde la línea de banda, en el punto de salida.
- Los rivales a 5 m.
- Se puede jugar con push, hit o self-pass.
- No se puede jugar directamente al círculo si se está en la zona de 23 m atacante sin que la bola recorra 5 m.

### 7.7. Aerial / scoop

- La bola se eleva por encima de los rivales.
- El receptor debe tener espacio; los rivales deben dar 5 m.
- Es peligroso si se juega contra un adversario.
- Se usa para superar pressing y cambiar de carril.
- Requiere `aerial`, control y lectura.

### 7.8. 3D

- No es una regla formal, sino una habilidad.
- Consiste en levantar la bola sobre el stick o el cuerpo de un rival y volver a controlarla.
- Debe hacerse con seguridad.
- Requiere `regate_3d`, coordinación y agilidad.
- Es especialmente útil en espacios reducidos y en el 1 contra 1.

---

## 8. El portero

### 8.1. Técnica

- **Posición base**: pies abiertos, rodillas flexionadas, manos activas, stick en el suelo.
- **Ángulos**: cubrir el primer palo y el centro; reducir el ángulo al tirador.
- **Paradas bajas**: kickers, leg guards, stick.
- **Paradas altas**: manos, casco, bloqueo con el cuerpo.
- **1 contra 1**: salir a cerrar el ángulo o esperar.
- **PC**: coordinación con el primer runner; cubrir el primer palo y el desvío.
- **Stroke**: leer al tirador, no moverse antes.
- **Rebotes**: controlar la segunda jugada.
- **Distribución**: saques rápidos y precisos.

### 8.2. Perfil del portero moderno

- Reflejos y blocaje.
- Buen uso del cuerpo y del stick.
- Comunicación.
- Distribución.
- Valiente en las salidas.
- Capacidad de jugar con el pie y con el stick.
- Lectura del PC y del stroke.

---

## 9. Reglas y faltas

### 9.1. Faltas comunes

- Jugar la bola con el pie o la pierna (salvo portero en el círculo).
- Jugar con la parte redondeada del stick.
- Levantar la bola de forma peligrosa.
- Obstaculizar con el cuerpo.
- Interferir con el stick del rival.
- Agarrar, empujar o zancadillear.
- Jugar la bola estando en el suelo (salvo portero).
- Tercer jugador: bloquear a un rival que intenta jugar la bola.

### 9.2. Obstruction

- Un defensor se interpone entre el portador y la bola.
- El stick del defensor bloquea el stick del atacante.
- Un tercer jugador bloquea a un rival.
- La sanción suele ser falta; si es intencionada y cerca del área, puede ser PC o tarjeta.

### 9.3. Dangerous play

- Bola elevada contra un rival cercano.
- Stick alto.
- Entrada peligrosa.
- Bola que puede golpear a un jugador en la cabeza.
- El árbitro puede dar falta, PC, tarjeta o stroke según la gravedad.

### 9.4. Ventaja

- El árbitro puede dejar jugar si el equipo perjudicado mantiene la posesión.
- Si la ventaja no se materializa, puede volver a la falta original.

### 9.5. Video y revisión

- En competiciones importantes hay videoarbitraje para goles, PC y strokes.
- En ligas menores, el arbitraje es presencial y sin video.

---

## 10. Táctica

### 10.1. Principios ofensivos

- **Amplitud**: abrir el campo para generar espacios.
- **Profundidad**: atacar la espalda de la defensa.
- **Superioridad**: crear 2 contra 1 en banda o en el centro.
- **Fijar y pasar**: atraer al rival y liberar al compañero.
- **Cambio de orientación**: mover la bola de un lado al otro.
- **Ataque del círculo**: entrar con intención, no solo por entrar.
- **Rebote**: tener jugadores en el segundo palo y en la frontal.

### 10.2. Principios defensivos

- **Presión**: presionar al portador y las líneas de pase.
- **Cobertura**: ayudar al compañero batido.
- **Basculación**: mover el bloque hacia la bola.
- **Compactación**: reducir espacios entre líneas.
- **Orientación**: llevar al rival a la banda.
- **Protección del círculo**: evitar PC y tiros cómodos.
- **Salida**: recuperar y contraatacar.

### 10.3. Pressing

- **Pressing alto**: delanteros presionan la salida.
- **Pressing medio**: bloque medio, se cierra el centro.
- **Pressing bajo**: bloque cerca del círculo, se cede espacio arriba.
- **Presión tras pérdida**: 3-5 segundos para recuperar; si no, replegar.

### 10.4. Ataque del PC

- Directo.
- Slip.
- Desvío.
- Rebote.
- Jugada ensayada.
- Cambio de tiro.
- Uso del portero como último recurso.

### 10.5. Defensa del PC

- Primer runner agresivo.
- Segundo runner coordinado.
- Portero con lectura.
- Postes.
- Flyer.
- Reboteadores.
- No salir antes de tiempo.

---

## 11. Preparación física y mental

### 11.1. Físico

- **Resistencia**: capacidad aeróbica para repetir esfuerzos.
- **Velocidad**: aceleración, velocidad máxima y reacción.
- **Fuerza**: golpeo, duelos, PC.
- **Agilidad**: cambios de dirección, frenadas, giros.
- **Coordinación**: óculo-manual, equilibrio, técnica corporal.
- **Core**: estabilidad para golpear y defender.
- **Prevención de lesiones**: isquiotibiales, aductores, tobillo, espalda.

### 11.2. Mental

- Toma de decisiones bajo presión.
- Concentración sostenida.
- Competitividad.
- Liderazgo y comunicación.
- Resiliencia tras error.
- Gestión del PC y del stroke.
- Rutinas de preparación.

### 11.3. Entrenamiento

- Técnica individual.
- Táctica de equipo.
- Set pieces.
- Transiciones.
- Partidos reducidos.
- Video y scouting.
- Recuperación y carga.

---

## 12. Cómo se conecta con el modelo de atributos

| Elemento del hockey | Atributo(s) del modelo |
|---|---|
| Control y recepción | `control` |
| Pase | `pase` |
| Conducción | `conduccion` |
| Hit / slap / sweep | `golpeo` |
| Flick / scoop | `flick`, `aerial` |
| Regate 3D | `regate_3d` |
| Definición | `definicion` |
| Saque de PC | `pc_injection` |
| Parada de PC | `pc_trap` |
| Tiro de PC | `pc_flick` |
| Desvío | `pc_deflection` |
| Primer runner | `pc_first_runner` |
| Parada de PC del portero | `pc_gk_save` |
| Stroke | `stroke_shot` |
| Parada de stroke | `stroke_save` |
| Faltas y 16 yardas | `free_hit` |
| Posicionamiento | `posicionamiento` |
| Pressing | `pressing` |
| Cobertura | `cobertura` |
| Transición | `transicion` |
| Desmarque | `desmarque` |
| Velocidad | `velocidad` |
| Resistencia | `resistencia` |
| Fuerza | `fuerza` |
| Agilidad | `agilidad` |
| Coordinación | `coordinacion` |
| Decisiones | `decisiones` |
| Concentración | `concentracion` |
| Competitividad | `competitividad` |
| Liderazgo | `liderazgo` |
| Portero | `reflejos`, `blocaje`, `distribucion`, `uno_vs_uno`, `alto`, `rebote_gk` |

### Especialistas

| Especialista | Atributo principal |
|---|---|
| Inyector | `pc_injection` |
| Stopper | `pc_trap` |
| Drag flicker | `pc_flick` |
| Desviador | `pc_deflection` |
| Primer runner | `pc_first_runner` |
| Portero de PC | `pc_gk_save` |
| Tirador de stroke | `stroke_shot` |
| Portero de stroke | `stroke_save` |
| Aéreo | `aerial` |
| Faltas | `free_hit` |

---

## 13. Glosario

| Término | Significado |
|---|---|
| **PC** | Penalty corner o córner corto. |
| **Stroke** | Penalty stroke o penalti. |
| **Drag flick** | Técnica de tiro de PC. |
| **Inyector** | Jugador que saca el PC. |
| **Stopper** | Jugador que para el saque del PC. |
| **Primer runner** | Defensor que sale primero en el PC. |
| **Flyer** | Defensor que sale por fuera en el PC. |
| **Aerial** | Scoop elevado. |
| **3D** | Levantar la bola sobre el stick/cuerpo. |
| **Self-pass** | Pasarse a uno mismo en una falta. |
| **16 yardas** | Golpe desde la línea de 16 yardas. |
| **Córner largo** | Falta desde la línea de 23 m. |
| **Kicking back** | Portero sustituido por un jugador de campo. |
| **Shoot-out** | Tanda de uno contra uno. |
| **EHL** | Euro Hockey League. |

---

## 14. Fuentes y lecturas

- FIH, *Rules of Hockey* (edición vigente).
- RFEH, Reglamento de competiciones y circular 2026-27.
- Wikipedia, *Field hockey* y *Penalty corner* (consulta 2026).
- RFEH/iSquad, actas y datos de la temporada 2026-27.
- Informes del proyecto:
  - `informe_sistema_ligas_DHA_DHB_2026_27.md`
  - `informe_posiciones_DHA_DHB_2026_27.md`

> Las reglas y interpretaciones pueden variar según la competición. Para una decisión oficial, consultar el reglamento vigente de la RFEH y las instrucciones arbitrales.
