# Motor de partido — diseño de texto

**Objetivo:** simular partidos de hockey hierba de forma explicable, rápida y determinista, sin gráficos, usando los 37 atributos y las reglas reales de DHA/DHB.

---

## 1. Principios

1. **Texto, no píxeles.** El jugador lee lo que pasa y toma decisiones.
2. **Fases, no física.** No simulamos 40 Hz; simulamos fases de posesión de 20-30 segundos.
3. **Atributos con peso.** Cada acción usa los atributos relevantes, no un único overall.
4. **Contexto.** Fatiga, moral, táctica, localía, clima, superficie y logística importan.
5. **Set pieces de verdad.** PC y stroke son subestados con roles y especialistas.
6. **Determinismo.** Misma semilla + mismas decisiones = mismo resultado.
7. **Explicabilidad.** Cada evento puede rastrearse a una tirada, atributos y contexto.

---

## 2. Estructura del partido

- **4 cuartos de 15 minutos** (FIH 2026/2027), con descansos de 2-10-2 minutos.
- **16 convocados**: 11 en el campo y hasta 5 suplentes.
- **11 en el campo**: 1 portero + 10 de campo.
- **Cambios rodantes**: el jugador puede cambiar en cualquier momento, salvo entre la concesión y el final de un PC (salvo lesión/portero).
- **Tiempo añadido** por PC/stroke al final de cada cuarto.
- **Shoot-outs** si hay empate en eliminatoria.

### Estado del partido

```json
{
  "minute": 0,
  "quarter": 1,
  "score": {"home": 0, "away": 0},
  "possession": "home",
  "zone": "middle",
  "momentum": 0,
  "pc_count": {"home": 0, "away": 0},
  "cards": {"home": [], "away": []},
  "fatigue": {"home": 0.0, "away": 0.0},
  "weather": "sol",
  "pitch": "water-based",
  "events": []
}
```

---

## 3. Bucle de fases

Cada fase representa 20-30 segundos de juego. El motor decide:

1. **Quién tiene la bola** (posesión).
2. **En qué zona** está: `own_23`, `middle`, `attacking_23`, `circle`.
3. **Qué intenta**: construir, progresar, presionar, entrar al círculo, tirar, buscar PC, etc.
4. **Quién participa**: portador, apoyo, defensor, portero.
5. **Resolución**: comparación de atributos + táctica + contexto + azar.
6. **Evento**: texto, estadísticas, cambios de estado.

### 3.1. Selección de acción

El portador elige entre:

- pase corto;
- pase largo;
- conducción;
- regate 3D;
- pase aéreo (aerial);
- entrada al círculo;
- tiro;
- pase atrás;
- autopase (si hay falta).

La elección se pondera con:

```
peso_accion = base_táctica
            * atributo_principal
            * contexto_zona
            * fatiga
            * moral
            * presión_rival
            * riesgo
```

El motor elige por ruleta ponderada. Esto permite que un equipo conservador juegue pases cortos y un equipo directo busque el aerial.

### 3.2. Resolución de un duelo

Ejemplo: pase corto bajo presión.

```
ataque = 0.45 * pase
       + 0.20 * control
       + 0.15 * decisiones
       + 0.10 * posicionamiento
       + 0.10 * (20 - fatiga*20)/20

defensa = 0.35 * pressing
        + 0.25 * intercepcion (posicionamiento/cobertura)
        + 0.20 * agilidad
        + 0.10 * decisiones
        + 0.10 * (20 - fatiga*20)/20

prob_exito = 1 / (1 + exp(-(ataque - defensa)/8))
```

Ajustes:

- +5% si el pase es hacia adelante y hay superioridad.
- -10% si el receptor está marcado.
- -15% si el equipo está en fatiga alta.
- +5% si el jugador es especialista en `pase` y el equipo usa `pase corto`.
- -10% con lluvia fuerte o campo mojado.

El resultado:

- éxito → avanza la zona o genera ocasión;
- fallo → intercepción, tackle o falta;
- falta → PC, stroke, free hit o tarjeta según zona e intención.

---

## 4. Acciones y atributos

| Acción | Atributos principales | Atributos secundarios |
|---|---|---|
| Pase corto | pase | control, decisiones, posicionamiento |
| Pase largo | pase, golpeo | fuerza, decisiones |
| Conducción | conduccion | control, agilidad, regate_3d |
| Regate 3D | regate_3d | control, agilidad, coordinacion |
| Aerial | aerial | golpeo, fuerza, control |
| Tiro abierto | definicion | golpeo, flick, decisiones |
| Tiro de PC | pc_flick | fuerza, definicion, concentracion |
| Desvío de PC | pc_deflection | posicionamiento, coordinacion |
| Saque de PC | pc_injection | pase, concentracion |
| Parada de PC | pc_gk_save | reflejos, blocaje, posicionamiento |
| Stroke | stroke_shot | definicion, concentracion |
| Parada de stroke | stroke_save | reflejos, uno_vs_uno |
| Tackle | cobertura, pressing | fuerza, agilidad |
| Intercepción | posicionamiento | cobertura, decisiones |
| Pressing | pressing | resistencia, velocidad |
| Cobertura | cobertura | posicionamiento, transicion |
| Falta / 16 yardas | free_hit | pase, golpeo |
| Portero 1v1 | uno_vs_uno | reflejos, blocaje |
| Paradas altas | alto | reflejos, agilidad |
| Rebote | rebote_gk | reflejos, blocaje |

---

## 5. Zonas y peligro

```
own_23  ──────  middle  ──────  attacking_23  ──────  circle
  bajo          medio              alto                máximo
```

Cada zona tiene un **valor de peligro**:

| Zona | Valor | Acciones típicas |
|---|---:|---|
| own_23 | 0.05 | salida, despeje, pase largo |
| middle | 0.25 | progresión, pressing, transición |
| attacking_23 | 0.55 | entrada al círculo, PC, centro |
| circle | 0.85 | tiro, desvío, stroke, rebote |

El motor usa el peligro para calcular la probabilidad de que una fase termine en ocasión.

---

## 6. Tiro y xG

### 6.1. Tiro abierto

```
calidad = 0.35 * definicion
        + 0.20 * golpeo
        + 0.15 * decisiones
        + 0.10 * posicionamiento
        + 0.10 * (1 - presion)
        + 0.10 * (1 - fatiga)

xg = base_zona * (calidad/100) * ajuste_portero * ajuste_clima
```

- `base_zona`: 0.05 (lejos), 0.12 (borde del círculo), 0.25 (área), 0.35 (mano a mano).
- `ajuste_portero`: 1 - (reflejos + blocaje + posicionamiento)/300.
- `ajuste_clima`: lluvia/astroturf rápido → +5%; viento → -5%.

### 6.2. PC

El PC se resuelve en fases:

1. **Saque**: `pc_injection` vs presión del primer runner.
2. **Parada**: `pc_trap` vs presión.
3. **Tiro**: `pc_flick` vs `pc_gk_save` + primer runner.
4. **Desvío**: `pc_deflection` vs portero/defensa.
5. **Rebote**: `rebote` vs defensa.

Cada fase puede fallar y generar otra fase, falta o contraataque.

### 6.3. Stroke

```
prob_gol = 0.78
         + (stroke_shot - stroke_save)/200
         + (concentracion - 10)/100
         - presion/200
```

Se limita a 0.55-0.92. Un stroke no es automático.

---

## 7. Set pieces

### 7.1. Penalty corner

Roles:

- **Inyector**: saca desde la marca.
- **Stopper**: para/controla el saque.
- **Drag flicker**: tira.
- **Desviador**: desvía en el primer palo.
- **Reboteador**: segunda jugada.
- **Primer runner**: defiende saliendo desde la línea.
- **Portero de PC**: cubre el primer palo y el centro.
- **Postes**: protegen los palos.

Rutinas:

- Directa.
- Slip izquierda/derecha.
- Desvío.
- Rebote.
- Ensayada.

La rutina elegida cambia los pesos de las fases y el riesgo de contraataque.

### 7.2. Stroke

- Tirador vs portero.
- El portero puede elegir quedarse o salir.
- El tirador puede elegir potencia/colocación.
- El resultado puede ser gol, parada, poste o fuera.

### 7.3. Falta, 16 yardas y córner largo

- Self-pass, pase corto, pase largo o aerial.
- En zona atacante, la bola debe recorrer 5 m antes de entrar al círculo.
- El córner largo se ejecuta desde la línea de 23 m.
- El golpe de 16 yardas se ejecuta desde la línea de 16 yardas.

### 7.4. Aerial y 3D

- El aerial supera la primera línea; el receptor debe controlar.
- El 3D permite superar un stick o un cuerpo; riesgo de falta si es peligroso.
- La defensa puede anticipar, interceptar o conceder falta.

---

## 8. Faltas, tarjetas y árbitro

### 8.1. Faltas

- Pie/body.
- Stick obstruction.
- Obstruction.
- Dangerous play.
- Back of stick.
- Third party.

Cada falta tiene:

- zona;
- intención (accidental, deliberada, peligrosa);
- consecuencia: free hit, PC, stroke, tarjeta.

### 8.2. Tarjetas

| Tarjeta | Efecto | Duración |
|---|---|---|
| Verde | Aviso / 2 min | 2 min |
| Amarilla | Suspensión temporal | 5-10 min |
| Roja | Expulsión | resto del partido |

Las tarjetas afectan a la moral, a la disponibilidad y a la reputación.

### 8.3. Árbitro

- Estilo: permisivo, equilibrado, estricto.
- Influencia: más o menos faltas, tarjetas y PC.
- Errores: possible, pero no absurdos.
- En eliminatorias, shoot-outs.

---

## 9. Fatiga, condición y cambios

### 9.1. Fatiga

```
fatiga += intensidad_fase * (1 - resistencia/100) * factor_clima * factor_calidad
```

- Cada fase consume fatiga.
- Los cuartos y el descanso recuperan poco.
- La fatiga reduce pase, velocidad, pressing y decisiones.
- A partir de 70% de fatiga, riesgo de lesión y error.

### 9.2. Cambios

- Rodantes, hasta 16 convocados.
- La IA y el jugador pueden cambiar en cualquier momento.
- Los cambios mejoran la frescura pero rompen la cohesión si son muchos.
- Los especialistas de PC/stroke pueden entrar solo para set pieces.

### 9.3. Lesiones

```
riesgo = base * (1 + fatiga) * (1 + carga_entrenamiento) * (1 - medical/5)
```

- Tipo: muscular, golpe, esguince, fractura.
- Duración: días/semanas.
- Afecta a la plantilla y a la moral.

---

## 10. Shoot-outs

- 5 lanzadores por equipo.
- Tirador vs portero.
- Si persiste el empate, muerte súbita.
- Los especialistas de stroke y los porteros importan.
- La presión y la moral modifican la probabilidad.

---

## 11. Simulación rápida

Para partidos de IA o para avanzar rápido:

```
resultado = Poisson(lambda_local, lambda_visitante)
lambda = ataque_equipo * defensa_rival * factor_local * factor_logistica
```

Pero incluso en rápido se generan:

- goleadores;
- asistencias;
- PC/stroke;
- tarjetas;
- lesiones;
- ratings.

La simulación rápida usa los mismos atributos, pero no genera comentario extenso.

---

## 12. Comentario de texto

Plantillas con placeholders:

```
{minute}' {player} {action}...
```

Ejemplos:

- `12' PC para el Atlètic. {injector} saca, {stopper} para y {flicker} busca el primer palo.`
- `23' {player} roba en el centro y lanza el contraataque.`
- `34' ¡Paradón de {gk}! El desvío de {player} se marchaba al segundo palo.`
- `51' Tarjeta amarilla para {player} por una entrada tardía.`
- `67' {player} transforma el stroke y pone el 3-2.`

El comentario se genera a partir del evento, no se escribe a mano para cada partido.

---

## 13. Calibración objetivo

| Métrica | Objetivo |
|---|---|
| Goles por partido | 4-7 |
| PC por partido | 4-8 |
| Conversión de PC | 25-40% |
| Strokes por partido | 0-1 |
| Conversión de stroke | 70-85% |
| Tarjetas verdes | 0-2 |
| Tarjetas amarillas | 0-1 |
| Posesión | 40-60% |
| Lesiones por partido | 0-1 |
| Shoot-outs | solo eliminatorias |

Se validará con miles de partidos simulados y comparación con las medias de DHA/DHB.

---

## 14. Ejemplo de partido (fragmento)

```
ATLÈTIC TERRASSA HC  vs  RC POLO
Liga IATI · Jornada 4 · Can Salas · 12:30 · 18°C, sol

1'  Salida en corto del Atlètic. {pase} supera la primera presión.
4'  Primer acercamiento del Polo. {extremo} entra al círculo y fuerza PC.
5'  PC para el Polo. {inyector} saca, {stopper} para, {flicker} tira... ¡parada de {gk}!
9'  {central} corta un pase filtrado y monta el contraataque.
14' Gol del Atlètic. {delantero} define cruzado tras un 3D de {medio}.
17' Tarjeta verde para {lateral} del Polo.
...
```

---

## 15. Próximos pasos

1. Implementar el motor de fases en Python.
2. Cargar atributos y tácticas desde JSON.
3. Simular 10.000 partidos y calibrar.
4. Añadir comentario y eventos.
5. Integrar logística y moral.
