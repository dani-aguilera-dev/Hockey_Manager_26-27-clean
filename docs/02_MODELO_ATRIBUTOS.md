# Modelo de atributos de hockey

**Versión:** 2.0 (37 atributos, cinco overalls posicionales, especialistas de set pieces).
**Archivo fuente:** `tools/player_attributes_v2.csv`.
**Script:** `tools/build_attributes_v2.py`.
**Estado:** modelo funcional y calibrado; los valores son estimaciones, no datos oficiales.

---

## 1. Por qué no basta con los goles

Un modelo basado solo en goles comete errores graves en hockey:

- Un **central** con 56 goles puede ser un drag flicker o un especialista de PC, no un delantero.
- Un **portero** con 0 goles no es un mal jugador.
- Un **medio** con pocos goles puede ser el jugador más valioso del equipo.
- Un **lateral** con 0 goles puede ser clave en la salida de balón y en la defensa de PC.
- Un **delantero** con muchos goles puede ser un finalizador de área, no un creador.

Por eso el modelo separa:

1. **Demarcación** (portero, central, lateral, medio, delantero).
2. **Atributos** (37 características).
3. **Overall posicional** (el mismo jugador puede rendir mejor en una posición que en otra).
4. **Rol/especialista** (inyector, stopper, drag flicker, etc.).
5. **Contexto** (edad, nivel del equipo, liga, goles).

---

## 2. Los 37 atributos

### 2.1. Técnica (7)

| Atributo | Etiqueta | Qué mide |
|---|---|---|
| `control` | Control | Control y recepción en estático y movimiento. |
| `pase` | Pase | Pase de push, hit y slap; precisión y peso. |
| `conduccion` | Conducción | Conducción con la bola pegada al stick. |
| `golpeo` | Golpeo | Hit, slap y sweep; potencia y precisión. |
| `flick` | Flick / scoop | Flick y scoop para elevar la bola. |
| `regate_3d` | Regate 3D | Cambios de plano, habilidad en espacios reducidos. |
| `definicion` | Definición | Remate en área, uno contra uno y definición. |

### 2.2. 3D y set pieces (10)

| Atributo | Etiqueta | Qué mide |
|---|---|---|
| `aerial` | Aerial / scoop | Envío y recepción de bolas elevadas. |
| `pc_injection` | Saque de PC | Precisión, velocidad y consistencia del saque. |
| `pc_trap` | Parada de PC | Control del saque (stopper). |
| `pc_flick` | Tiro de PC | Drag flick, flick directo y potencia. |
| `pc_deflection` | Desvío en PC | Timing, mano y colocación en el desvío. |
| `pc_first_runner` | Primer runner | Salida defensiva de PC y presión. |
| `pc_gk_save` | Parada de PC (portero) | Parada específica de PC. |
| `stroke_shot` | Tiro de stroke | Tiro de penalty stroke. |
| `stroke_save` | Parada de stroke | Parada de penalty stroke. |
| `free_hit` | Faltas y 16 yardas | Faltas, 16 yardas, córners y saques de banda. |

### 2.3. Táctica (5)

| Atributo | Etiqueta | Qué mide |
|---|---|---|
| `posicionamiento` | Posicionamiento | Lectura del juego y ocupación de espacios. |
| `pressing` | Pressing | Presión, recuperación y pressing tras pérdida. |
| `cobertura` | Cobertura | Ayudas, basculación y cobertura defensiva. |
| `transicion` | Transición | Ataque-defensa y defensa-ataque. |
| `desmarque` | Desmarque | Ruptura y generación de espacios. |

### 2.4. Física (5)

| Atributo | Etiqueta | Qué mide |
|---|---|---|
| `velocidad` | Velocidad | Reacción y desplazamiento. |
| `resistencia` | Resistencia | Capacidad aeróbica y repetir esfuerzos. |
| `fuerza` | Fuerza | Golpeo, duelos y PC. |
| `agilidad` | Agilidad | Cambios de dirección y coordinación. |
| `coordinacion` | Coordinación | Coordinación óculo-manual y técnica corporal. |

### 2.5. Mental (4)

| Atributo | Etiqueta | Qué mide |
|---|---|---|
| `decisiones` | Decisiones | Toma de decisiones bajo presión. |
| `concentracion` | Concentración | Consistencia y atención. |
| `competitividad` | Competitividad | Intensidad, carácter y competitividad. |
| `liderazgo` | Liderazgo | Liderazgo y comunicación. |

### 2.6. Portero (6)

| Atributo | Etiqueta | Qué mide |
|---|---|---|
| `reflejos` | Reflejos | Reacción y reflejos. |
| `blocaje` | Blocaje | Blocaje y control de paradas. |
| `distribucion` | Distribución | Saque y distribución. |
| `uno_vs_uno` | 1 contra 1 | Salidas y duelos uno contra uno. |
| `alto` | Paradas altas | Paradas altas y juego aéreo. |
| `rebote_gk` | Control de rebotes | Segunda jugada y control de rebotes. |

---

## 3. Pesos por posición

El overall de cada posición es una media ponderada de los atributos. Los pesos suman 1,00.

### 3.1. Portero (POR)

| Atributo | Peso |
|---|---:|
| Reflejos | 22 % |
| Blocaje | 20 % |
| Distribución | 12 % |
| Parada de PC | 12 % |
| Parada de stroke | 10 % |
| 1 contra 1 | 8 % |
| Paradas altas | 6 % |
| Posicionamiento | 5 % |
| Liderazgo | 5 % |

### 3.2. Central (CEN)

| Atributo | Peso |
|---|---:|
| Cobertura | 18 % |
| Posicionamiento | 12 % |
| Primer runner | 10 % |
| Fuerza | 10 % |
| Parada de PC (stopper) | 8 % |
| Pase | 8 % |
| Decisiones | 8 % |
| Agilidad | 6 % |
| Velocidad | 5 % |
| Liderazgo | 5 % |
| Transición | 5 % |
| Control | 5 % |

### 3.3. Lateral (LAT)

| Atributo | Peso |
|---|---:|
| Velocidad | 16 % |
| Cobertura | 14 % |
| Resistencia | 12 % |
| Pase | 10 % |
| Conducción | 8 % |
| Transición | 8 % |
| Posicionamiento | 7 % |
| Pressing | 7 % |
| Agilidad | 6 % |
| Decisiones | 6 % |
| Primer runner | 6 % |

### 3.4. Medio (MED)

| Atributo | Peso |
|---|---:|
| Pase | 16 % |
| Posicionamiento | 12 % |
| Resistencia | 12 % |
| Pressing | 8 % |
| Transición | 8 % |
| Cobertura | 7 % |
| Conducción | 7 % |
| Decisiones | 7 % |
| Saque de PC | 6 % |
| Faltas / 16 yardas | 5 % |
| Control | 5 % |
| Desmarque | 4 % |
| Parada de PC | 3 % |

### 3.5. Delantero (DEL)

| Atributo | Peso |
|---|---:|
| Definición | 20 % |
| Velocidad | 13 % |
| Regate 3D | 12 % |
| Posicionamiento | 8 % |
| Conducción | 8 % |
| Aerial | 6 % |
| Tiro de PC | 6 % |
| Desvío en PC | 6 % |
| Decisiones | 6 % |
| Resistencia | 5 % |
| Desmarque | 5 % |
| Flick | 5 % |

> **Lectura clave:** un central no se evalúa por definición; se evalúa por cobertura, posicionamiento, primer runner, fuerza, pase y stopper. Un delantero no se evalúa por cobertura. Por eso un central con goles sigue siendo central.

---

## 4. Generación de atributos

### 4.1. Fórmula base

Para cada jugador:

```
base = 38
     + 16 * percentil_goles_equipo
     + 10 * percentil_goles_liga
     +  9 * curva_edad
     +  7 * fuerza_liga
     + N(0, 3)
```

- `percentil_goles_equipo`: posición del jugador dentro de los goles de su equipo.
- `percentil_goles_liga`: posición dentro de los goles de su liga.
- `curva_edad`:
  - 16-20 años: 0,55 → 1,00.
  - 21-24 años: 0,80 → 1,00.
  - 25-29 años: 1,00.
  - 30-32 años: 0,92.
  - 33+ años: 0,78.
- `fuerza_liga`: DHA 1,0; DHB 0,9; Primera Andaluza 0,8.
- `N(0,3)`: variación aleatoria controlada.
- Invitados: `base -= 4`.
- `base` se limita a 36-88.

### 4.2. Atributos de campo

```
atributo = base + sesgo_posición + N(0, 7)
```

### 4.3. Porteros

- Atributos de portero: `base + sesgo + N(0, 6)`.
- Atributos de campo: `32 + 0,28 * base + 0,4 * sesgo + N(0, 6)`.
- Los porteros tienen valores bajos en definición, regate, PC de campo, etc.

### 4.4. Atributos de portero en jugadores de campo

```
atributo = 19 + 0,22 * base + N(0, 5)
```

Así no se confunde a un jugador de campo con un portero.

### 4.5. Refuerzo por goles

Los goles solo refuerzan atributos ofensivos:

- `definicion`: `+ min(15, goles * 0,15)`.
- `flick`, `pc_flick`, `pc_deflection`, `stroke_shot`: `+ min(10, goles * 0,10)`.

No cambian la posición ni la cobertura.

### 4.6. Refuerzo de drag flick para centrales

Un central puede ser drag flicker. El modelo añade:

```
pc_flick += min(8, fuerza_proxy / 12)
```

donde `fuerza_proxy` se genera con la base y el sesgo de fuerza. Esto permite que centrales fuertes tengan un PC alto sin convertirlos en delanteros.

### 4.7. Sesgos principales

| Posición | Sesgos positivos | Sesgos negativos |
|---|---|---|
| Portero | Reflejos +16, blocaje +16, parada PC +15, alto +12, stroke +12, distribución +9 | Definición -24, regate -24, PC de campo -24 |
| Central | Cobertura +12, posicionamiento +9, primer runner +8, stopper +7, fuerza +7, PC flick +5 | Definición -10, velocidad -4, regate -8 |
| Lateral | Velocidad +10, resistencia +7, primer runner +7, cobertura +5, transición +5, pressing +5 | Definición -4, fuerza -2 |
| Medio | Pase +9, saque PC +7, faltas +7, resistencia +7, posicionamiento +6, pressing +6 | Definición -2 |
| Delantero | Definición +11, desvío PC +9, stroke +8, velocidad +7, regate 3D +7, PC flick +6, flick +5 | Cobertura -7, fuerza -2 |

---

## 5. Overall, potencial, valor y polivalencia

### 5.1. Overall

```
overall_pos = Σ(atributo * peso_pos)
```

Se calculan cinco overalls:

- `overall_portero`
- `overall_central`
- `overall_lateral`
- `overall_medio`
- `overall_delantero`

El `overall` principal es el de la posición natural. Para un jugador polivalente se usa el máximo.

### 5.2. Potencial

```
potencial = overall + bonus_edad
```

- ≤23 años: `(24 - edad) * 1,5 + 2`.
- 24-27 años: `+2`.
- 28+ años: `-(edad - 27)`.
- Se limita a 40-99.

### 5.3. Valor

```
valor = (overall/100)^4 * 2.000.000 * factor_edad * factor_posición
```

- Factor edad:
  - ≤21: 1,4.
  - 22-24: 1,3.
  - 25-27: 1,0.
  - 28-30: 0,6.
  - 31+: 0,3.
- Factor posición:
  - Portero: 0,9.
  - Defensa: 0,95.
  - Medio: 1,0.
  - Delantero: 1,1.
  - Polivalente: 1,05.
- Redondeo a 10.000 €.

### 5.4. Polivalencia

```
polivalencia = max(0, min(20, mejor_overall_alternativo - overall_natural))
```

Mide cuánto mejora el jugador si se le cambia de posición. Un central con 0 de polivalencia es claramente central; un jugador con 1,6 mejora ligeramente en otra posición. La mayoría de jugadores tienen 0 porque su posición natural es también su mejor posición; no significa que no puedan jugar en otra, sino que no mejorarían al hacerlo.

---

## 6. Arquetipos

| Posición | Arquetipo | Condición |
|---|---|---|
| Central | Muro | Cobertura ≥80 y fuerza ≥75 |
| Central | Central constructor | Pase ≥75 |
| Central | Central sólido | Resto |
| Lateral | Lateral ofensivo | Velocidad ≥80 y pase ≥70 |
| Lateral | Lateral defensivo | Resto |
| Medio | Medio creativo | Pase ≥80 y posicionamiento ≥75 |
| Medio | Medio box-to-box | Resistencia ≥80 |
| Medio | Medio de equilibrio | Resto |
| Delantero | Finalizador | Definición ≥82 |
| Delantero | Delantero de espacio | Velocidad ≥80 |
| Delantero | Delantero de área | Resto |
| Portero | Portero moderno | Distribución ≥75 |
| Portero | Portero clásico | Resto |
| Polivalente | Jugador polivalente | Resto |

---

## 7. Especialistas de set pieces

Cada equipo tiene diez roles. Se asigna al jugador con el atributo más alto del equipo:

| Rol | Atributo | Qué representa |
|---|---|---|
| `pc_flicker` | `pc_flick` | Drag flicker / tiro de PC. |
| `pc_injector` | `pc_injection` | Inyector / saque de PC. |
| `pc_stopper` | `pc_trap` | Stopper / parada del saque. |
| `pc_deflector` | `pc_deflection` | Desviador en PC. |
| `pc_first_runner` | `pc_first_runner` | Primer runner defensivo. |
| `pc_goalkeeper` | `pc_gk_save` | Portero de PC. |
| `stroke_taker` | `stroke_shot` | Tirador de stroke. |
| `stroke_goalkeeper` | `stroke_save` | Portero de stroke. |
| `aerial_specialist` | `aerial` | Especialista aéreo. |
| `free_hit_taker` | `free_hit` | Especialista en faltas y 16 yardas. |

Esto refleja que el hockey tiene roles muy específicos: un equipo puede tener un central como drag flicker, un medio como inyector y un delantero como desviador.

**Rebote y otros roles de PC:** el rebote no tiene un atributo propio; se modela con `definicion`, `posicionamiento` y `pc_deflection`. El segundo runner, los postes y el flyer se modelan con `pc_first_runner`, `cobertura`, `posicionamiento` y `pressing`. Si en el futuro se dispone de datos, se pueden separar en atributos propios.

---

## 8. Cómo se relaciona con el juego

El modelo alimenta:

- **Overall** de cada jugador en la tabla.
- **Ficha del jugador:** 37 barras de atributos, cinco overalls, arquetipo y especialistas.
- **Equipos:** ataque y defensa calculados con `attackScore` y `defenseScore`.
- **Simulación:** los ratings de ataque/defensa de cada equipo.
- **Editor:** el usuario puede cambiar posición y atributos; el overall se recalcula con los mismos pesos.

### 8.1. Ataque y defensa de equipo

Para cada jugador:

```
attackScore = media(definición, flick, regate_3d, pase, pc_flick, pc_deflection, velocidad)
defenseScore = media(cobertura, posicionamiento, primer runner, pressing, transición, fuerza)
```

Para porteros, `defenseScore` añade reflejos, blocaje, parada de PC, parada de stroke, 1v1 y paradas altas.

Luego:

```
ataque = 0,55 * media(top5 attackScore)
       + 0,25 * media(attackScore plantilla)
       + 0,10 * profundidad
       + 0,10 * edad

defensa = 0,55 * media(top5 defenseScore)
        + 0,25 * media(defenseScore plantilla)
        + 0,10 * profundidad
        + 0,10 * experiencia
```

Los valores se normalizan a una escala 40-95 y se combinan:

```
overall_equipo = 0,6 * ataque + 0,4 * defensa
```

### 8.2. Perfil de set pieces del equipo

Además de los especialistas, el juego calcula cinco ratings agregados:

```
pc_attack   = media(top3 pc_injection, top3 pc_trap, top3 pc_flick, top3 pc_deflection)
pc_defense  = media(top3 pc_first_runner, top3 pc_gk_save, top3 blocaje, top3 cobertura)
stroke      = top1 stroke_shot
stroke_save = top1 stroke_save
aerial      = top3 aerial
```

Se muestran en la ficha del equipo como barras. Sirven para comparar el peligro y la solidez del equipo en acciones a balón parado.

---

## 9. Ejemplos reales del modelo

### 9.1. Iain Martin McFadden (CD Terrassa)

- Posición: **Central**.
- Overall central: **73,9**.
- Cobertura: 78.
- Pase: 76.
- Primer runner: 74.
- PC flick: 72.
- Arquetipo: **Central constructor**.
- Especialista: **stopper de PC** y **free_hit_taker** de CD Terrassa.
- Polivalencia: **1,6** (su overall de medio es 75,5, ligeramente superior al de central).

No es un delantero aunque tenga pocos goles. Su valor está en la defensa, la salida y las faltas.

### 9.2. Bruno Àvila Gran (RC Polo)

- Posición: **Central**.
- Goles iSquad: **56**.
- Overall central: **84,2**.
- Cobertura: 88.
- PC flick: 85.
- Arquetipo: **Muro**.
- Especialista: **inyector y stopper de PC**.

Es el caso que motivó el cambio de modelo: un central con muchos goles no se convierte en delantero. Sus goles refuerzan definición y PC, pero su overall se calcula con pesos de central.

### 9.3. Ricardo Sánchez Herrero (RC de Campo)

- Posición: **Central** (Global Sports Archive 2026-27, “Defender”).
- Goles iSquad: **30**.
- Overall central: **89,9**.
- Arquetipo: **Muro**.
- Especialista: **primer runner** y **especialista aéreo**.

La estimación por goles lo había colocado como delantero. La fuente actual de la plantilla lo confirma como defensa, y el modelo lo valora con pesos de central. Es el ejemplo más claro de por qué los goles no deben decidir la posición.

### 9.4. Portero

- Overall medio de los 75 porteros: **73,4**.
- Reflejos medios: **78,9**.
- Definición media: **39,5**.
- PC flick medio: **39,0**.

El portero tiene atributos de portero altos y atributos de campo bajos, como debe ser.

---

## 10. Calibración

### 10.1. Distribución final

| Métrica | Valor |
|---|---:|
| Overall medio | 68,95 |
| Desviación típica | 8,10 |
| Mínimo | 46,5 |
| Máximo | 93,2 |
| Centrales | 249 |
| Laterales | 145 |
| Medios | 242 |
| Delanteros | 262 |
| Porteros | 72 |
| Polivalentes | 6 |

### 10.2. Medias por posición

| Posición | Overall medio | Definición | Cobertura | PC flick | Reflejos |
|---|---:|---:|---:|---:|---:|
| Portero | 73,4 | 39,5 | 48,8 | 39,0 | 78,9 |
| Central | 65,1 | 49,5 | 71,1 | 69,2 | 32,4 |
| Lateral | 64,5 | 55,6 | 65,3 | 59,5 | 31,7 |
| Medio | 68,0 | 61,3 | 65,1 | 63,1 | 33,4 |
| Delantero | 74,7 | 81,9 | 61,2 | 75,9 | 34,1 |

### 10.3. Top del modelo

| Jugador | Equipo | Posición | Overall | Arquetipo |
|---|---|---|---:|---|
| Ricardo Sánchez Herrero | RC de Campo | Delantero | 93,2 | Finalizador |
| Joaquim Malgosa Freixa | Atlètic Terrassa | Delantero | 91,8 | Finalizador |
| Andrés Medina García | RC de Campo | Delantero | 91,0 | Finalizador |
| Manuel Rodríguez Muesmann | RC de Campo | Delantero | 90,6 | Finalizador |
| Mario Álvarez-Villabol Navarro | Pozuelo | Delantero | 90,4 | Finalizador |

Los delanteros dominan el top porque su overall mide definición, velocidad y regate. Los defensas tienen su propia escala y no compiten con los delanteros en la misma tabla de atributos ofensivos.

### 10.4. Advertencias de calibración

- Los porteros tienen un overall medio más alto que centrales y laterales; es una escala distinta, no una comparación directa.
- Los atributos de 99 son posibles en élite, pero deben revisarse manualmente.
- Los jugadores con pocos datos (invitados) tienen más incertidumbre.
- La subposición Central/Lateral se estima cuando la fuente solo dice "Defensa". En la versión actual, 399 perfiles tienen subposición estimada.

---

## 11. Editor y overrides

El juego incluye un editor por jugador:

- Cambiar posición natural: Portero, Central, Lateral, Medio, Delantero o Polivalente.
- Editar los 37 atributos.
- Guardar en `localStorage` con la clave `hockey_overrides_v1`.
- Recalcular overalls, potencial, valor, arquetipo y ratings de equipo.
- Restablecer el ajuste manual.

Los overrides no modifican `player_attributes_v2.csv` ni el Excel. Son locales al navegador.

### Formato del override

```json
{
  "EQUIPO||JUGADOR": {
    "subposicion": "Central",
    "positionGroup": "Defensa",
    "attributes": {
      "cobertura": 95,
      "pc_flick": 88,
      "definicion": 60
    }
  }
}
```

---

## 12. Limitaciones

1. **No hay datos oficiales de atributos.** Todo es un modelo.
2. **La posición base no siempre es oficial.** 801 perfiles tienen posición estimada.
3. **La subposición Central/Lateral no siempre está documentada.** 399 perfiles la tienen estimada.
4. **Los goles no son asistencias.** iSquad no ofrece asistencias completas.
5. **No hay datos de minutos, lesiones o sanciones.**
6. **El modelo no distingue nivel de competición con precisión.** DHA, DHB y Primera Andaluza usan factores, pero no un sistema de fuerza de liga completo.
7. **Los especialistas se asignan por máximo atributo del equipo.** No siempre coinciden con el especialista real.
8. **La escala de overall no es una escala absoluta.** Sirve para comparar y simular.

---

## 13. Reproducibilidad

```bash
cd /home/daniel/hockey_espana/tools
python3 build_attributes_v2.py
python3 generate_game.py
python3 build_excel_attributes.py
```

Salidas:

- `tools/player_attributes_v2.csv`
- `juego_hockey/index.html`
- `equipos_hockey_hierba_espana_masculino_2026_27_con_atributos.xlsx`
- `jugadores_atributos_2026_27.csv`

El generador usa una semilla determinista por jugador, equipo y versión (`hashlib.md5`). Si se cambia el orden de los atributos o se añaden draws aleatorios, los valores cambian; por eso hay que regenerar todo el pipeline y volver a probar el juego.

---

## 14. Próximas mejoras del modelo

1. Validar manualmente los 175 perfiles oficiales.
2. Revisar los centrales con más goles y los drag flickers.
3. Añadir altura, peso y envergadura para el PC y el juego aéreo.
4. Añadir datos de PC convertidos, strokes y paradas.
5. Ajustar la escala de porteros.
6. Incorporar el 25 % de elegibilidad para play-offs.
7. Separar “overall actual” y “potencial” con más precisión.
8. Añadir un modo de exportación/importación de overrides.
