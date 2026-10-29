# Sistema de ligas DHA y DHB 2026-27

Documento de referencia para el simulador y para cualquier persona que continúe el proyecto. Resume el formato real, las fases, los ascensos y descensos, los clubes vinculados y la implementación en el juego.

---

## 1. Pirámide y ámbito

La competición nacional masculina sénior se organiza en:

```
División de Honor A (DHA)          12 equipos
        │  ascenso / descenso
División de Honor B (DHB)          16 equipos, 2 grupos
        │  ascenso / descenso
Primeras divisiones autonómicas    varias comunidades
```

El proyecto incluye DHA, DHB y una primera división autonómica: la Primera Andaluza, con el Club de Hockey San Fernando. No se simulan los ascensos desde todas las primeras autonómicas a DHB; solo se incluye San Fernando como caso representativo.

### Equipos DHA 2026-27

1. CD Terrassa Hockey
2. Junior FC
3. Atlètic Terrassa HC
4. CH Carpesa
5. FC Barcelona
6. Club Egara
7. RC Polo
8. Real Club de Campo Villa de Madrid
9. Sanse Complutense
10. Sardinero Hockey Club
11. RS Tenis
12. UD Taburiente

### Equipos DHB 2026-27

1. AD Rimas *(vinculado a CD Terrassa)*
2. Aticos Inmobiliaria CH San Fernando
3. Castelldefels HC
4. CD Giner de los Ríos
5. Club Hockey Madrid - Las Rozas
6. Egara 1935 *(vinculado a Club Egara)*
7. HC Sant Cugat
8. Iluro HC
9. Línia 22 Stern Motor
10. Pedralbes HC *(vinculado a RC Polo)*
11. RC Jolaseta
12. Pozuelo
13. Real Sociedad 1927 *(vinculado a Real Club de Campo)*
14. SPV *(vinculado a Sanse Complutense)*
15. Universitat d'Alacant - San Vicente
16. Vallès Esportiu *(vinculado a Atlètic Terrassa)*

### Primera Andaluza

- Club de Hockey San Fernando.

> **Atención:** “Aticos Inmobiliaria CH San Fernando” (DHB) y “Club de Hockey San Fernando” (Primera Andaluza) aparecen como equipos distintos. No son el mismo equipo en la misma categoría; el proyecto los mantiene separados y documenta la relación.

---

## 2. División de Honor A (DHA)

### 2.1. Formato

- 12 equipos.
- Liga regular a doble vuelta: **22 jornadas**.
- Todos contra todos, ida y vuelta.
- 3 puntos por victoria, 1 por empate, 0 por derrota.

### 2.2. Fase final

- Los **4 primeros** de la liga regular juegan la **Final Four**.
- Semifinales: 1º vs 4º y 2º vs 3º.
- Final por el título.
- El campeón de la Final Four es el campeón de DHA.
- La Final Four se juega en una sede única y con eliminatorias directas.

### 2.3. Descenso y playout

- **12º clasificado:** desciende directamente a DHB.
- **11º clasificado:** juega un **playout al mejor de 3 partidos** contra el **2º equipo elegible de DHB**.
  - Si gana el 11º de DHA, se mantiene en DHA.
  - Si gana el 2º de DHB, asciende y el 11º desciende.
- El playout se disputa después de la Final Four y de la fase de ascenso de DHB.

### 2.4. Caso práctico

Si el 11º de DHA es un club con equipo vinculado en DHB, el vinculado no puede ocupar la plaza de ascenso si su club matriz sigue en DHA. En ese caso, la plaza pasa al siguiente equipo elegible de DHB.

### 2.5. Copa del Rey y Europa

- La Copa del Rey es una competición independiente; no se simula.
- Las plazas europeas (EHL) dependen del campeón de liga, la Copa y el ranking; no se simulan.
- El proyecto se centra en la liga y el playout.

---

## 3. División de Honor B (DHB)

### 3.1. Formato general

- 16 equipos.
- Dos grupos de 8 en la primera fase.
- Segunda fase con dos grupos de 8: Grupo A (élite) y Grupo B (permanencia).
- 22 partidos en total para cada equipo:
  - 14 en la primera fase.
  - 14 en la segunda fase: 6 arrastrados + 8 nuevos.

### 3.2. Primera fase

- Dos grupos de 8.
- Doble vuelta dentro del grupo: **14 partidos**.
- Los 4 primeros de cada grupo pasan al Grupo A.
- Los 4 últimos de cada grupo pasan al Grupo B.

### 3.3. Segunda fase

#### Grupo A (del 1º al 8º)

- 8 equipos: los 4 primeros de cada grupo de la primera fase.
- Se arrastran los resultados de la primera fase contra los otros 3 equipos del mismo grupo de origen: **6 partidos**.
- Se juegan 8 partidos contra los 4 equipos del otro grupo de origen, ida y vuelta: **8 partidos**.
- Total: **14 partidos**.
- La clasificación final del Grupo A decide el ascenso.

#### Grupo B (del 9º al 16º)

- 8 equipos: los 4 últimos de cada grupo de la primera fase.
- Mismo sistema: 6 partidos arrastrados + 8 partidos cruzados = 14.
- La clasificación final del Grupo B decide el descenso.

### 3.4. Final Four y ascenso

- Los **4 primeros del Grupo A** juegan la **Final Four** de DHB.
- El campeón de la Final Four es el campeón deportivo de DHB.
- **El ascenso no lo decide la Final Four.** Asciende el **1º elegible del Grupo A**.
- El **2º elegible del Grupo A** juega el playout contra el 11º de DHA.
- Un equipo vinculado a un club de DHA **no puede ascender** si su club matriz sigue en DHA.
- Si el 1º no es elegible, la plaza pasa al siguiente elegible; si el 2º no es elegible, la plaza de playout pasa al siguiente.

### 3.5. Descenso

- Descienden los **dos últimos de la clasificación final de DHB** (posiciones 15ª y 16ª, correspondientes al Grupo B).
- Los ascensos desde las primeras autonómicas completan la DHB 2027-28; no se simulan todos.

### 3.6. Resumen de la segunda fase

```
Grupo A: 1º-4º del Grupo 1 + 1º-4º del Grupo 2
Grupo B: 5º-8º del Grupo 1 + 5º-8º del Grupo 2

Cada equipo:
  · 6 partidos arrastrados (contra los otros 3 de su grupo de origen)
  · 8 partidos cruzados (contra los 4 del otro grupo de origen, ida y vuelta)
  · 14 partidos
```

---

## 4. Reglas comunes

### 4.1. Puntuación y desempates

- Victoria: 3 puntos.
- Empate: 1 punto.
- Derrota: 0 puntos.

Desempates en liga a doble vuelta (Art. 58):

1. Resultados particulares entre los equipos empatados (puntos).
2. Diferencia de goles particular.
3. Goles particulares.
4. Diferencia de goles general.
5. Goles generales.
6. Tanda de shoot-outs.

En liga a una sola vuelta el orden empieza por partidos ganados, diferencia de goles general, goles generales, resultados particulares, diferencia particular, goles particulares y shoot-outs.

### 4.2. Formato de partido y actas

- **Duración:** 4 tiempos de **17 minutos y 30 segundos**.
- **Descansos:** 2 minutos entre el 1º y 2º; 10 minutos entre el 2º y 3º; 2 minutos entre el 3º y 4º.
- **Tiempo:** no se para en penaltis córner ni en goles.
- **Acta:** máximo 18 jugadores con 2 porteros, o 16 con 1 portero.
- **Mínimo para empezar:** 8 jugadores (4 en sala).
- **Mínimo para continuar:** 7 jugadores (3 en sala).
- **Incomparecencia:** 3-0 para el equipo presente.

### 4.3. Elegibilidad para play-offs, Copa y promoción

Un jugador debe haber sido alineado en al menos el **25 % de los partidos de la liga regular** para poder jugar:

- los play-offs finales;
- la Copa del Rey;
- los partidos de promoción de ascenso/descenso.

Para la Copa del Rey, si se juega antes de terminar la liga, se exige el 25 % de la primera vuelta.

### 4.4. Clubes vinculados y filiales

El Reglamento distingue entre:

- **Filial:** equipo juvenil, cadete o infantil dependiente de otro club, obligatorio para inscribirse en competiciones nacionales. No es un equipo sénior “B”.
- **Club vinculado:** relación entre un club de DHA y otro de DHB o Primera, con dirección social/fiscal común, cuentas bancarias comunes o criterios equivalentes.

Reglas clave:

- No puede haber dos equipos del mismo club en la misma categoría.
- Un club con equipo en DHA puede tener un equipo vinculado en DHB o en Primera.
- El equipo vinculado **no puede ascender** a la categoría superior si el club matriz ya está en ella.
- Si el club matriz desciende directamente y su vinculado se clasifica para ascender, el club mantiene un equipo en la categoría superior.
- Si el club matriz está en el playout de descenso y su vinculado está en plazas de ascenso, el vinculado debe ceder su plaza al siguiente clasificado.
- El equipo de DHA puede alinear un máximo de **5 jugadores de su vinculado** por partido.

Vinculaciones del proyecto:

| Equipo DHB | Club matriz DHA |
|---|---|
| AD Rimas | CD Terrassa |
| Egara 1935 | Club Egara |
| Pedralbes HC | RC Polo |
| Real Sociedad 1927 | Real Club de Campo |
| SPV | Sanse Complutense |
| Vallès Esportiu | Atlètic Terrassa |

---

## 5. Implementación en el juego

### DHA

- 22 jornadas dobles.
- Clasificación con puntos, goles a favor, goles en contra, diferencia.
- Top 4 → Final Four.
- 12º → descenso directo.
- 11º → playout contra el 2º elegible de DHB.
- El playout se juega al mejor de 3.
- Proyección de la DHA 2027-28 con ascensos y descensos.

### DHB

- Dos grupos de 8.
- Primera fase: 14 jornadas.
- Segunda fase: Grupo A/B con 6 resultados arrastrados y 8 partidos cruzados.
- Top 4 del Grupo A → Final Four.
- 1º elegible del Grupo A → ascenso directo.
- 2º elegible del Grupo A → playout contra el 11º de DHA.
- 15º y 16º → descenso.
- Los clubes vinculados se marcan y no pueden ascender si su matriz está en DHA.

### Simulación

- `simulateMatch(home, away, rng)` genera goles a partir de ataque, defensa y localía.
- `simulateDhaAll()` y `simulateDhbAll()` recorren las fases.
- `monteCarlo(league, runs)` estima probabilidades de título y ascenso.
- La simulación es determinista si se fija la semilla; el juego usa aleatoriedad para cada partido.

### Limitaciones del simulador

- No simula la Copa del Rey ni la EHL.
- No simula todos los ascensos autonómicos.
- No aplica el 25 % de elegibilidad a los play-offs (se asume plantilla disponible).
- No modela sanciones, lesiones ni fatiga.
- Los resultados son lúdicos, no predictivos.

---

## 6. Fuentes

- RFEH, Circular 1 2026-27 y Reglamento de competiciones.
- RFEH, normativa 7-2026 y artículos de desempate.
- RFEH/iSquad, plantillas y actas 2026-27.
- informe_sistema_ligas_DHA_DHB_2026_27.md (análisis completo y casos prácticos).
- Páginas oficiales de los clubes.

> Las reglas exactas pueden cambiar durante la temporada. Antes de una versión oficial, contrastar con la circular vigente y con las actas de la RFEH.
