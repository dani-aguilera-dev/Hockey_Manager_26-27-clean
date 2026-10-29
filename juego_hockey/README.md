# Hockey Manager 2026-27

Juego HTML de gestión, scouting y simulación del hockey hierba masculino español, construido con las plantillas de **DHA**, **DHB** y la **Primera Andaluza** del Club Hockey San Fernando.

## Cómo abrir

Abre `index.html` en cualquier navegador moderno:

```bash
xdg-open /home/daniel/hockey_espana/juego_hockey/index.html
```

No necesita servidor ni dependencias externas. Los datos están embebidos en el HTML. Las imágenes se cargan desde `../jugadores/thumbs/`, por lo que la carpeta `jugadores` debe permanecer junto a `juego_hockey`.

## Contenido

- **29 equipos**: 12 DHA, 16 DHB y 1 Primera Andaluza.
- **976 perfiles**: 509 jugadores y 467 invitados.
- **37 atributos** por jugador, agrupados en técnica, 3D/set pieces, táctica, física, mental y portero.
- **Cinco overalls posicionales**: portero, central, lateral, medio y delantero.
- **Arquetipos**: Muro, Central constructor, Finalizador, Portero moderno, etc.
- **Especialistas de set pieces**: inyector, stopper, drag flicker, desviador, primer runner, portero de PC, tirador de stroke, portero de stroke, aéreo y faltas.
- **Perfil de set pieces del equipo**: PC ataque, PC defensa, stroke, parada de stroke y aerial.
- **Editor de jugador** con `localStorage` para corregir posición y atributos.
- **Fuente de la posición** con URL y fecha cuando está disponible.
- **Simulador con formato oficial 2026-27**:
  - DHA: 22 jornadas, Final Four y playout.
  - DHB: dos grupos, segunda fase A/B con arrastre, Final Four, ascenso y descenso.
- **Resumen de temporada**: campeones, ascensos, descensos, playout y proyección DHA 2027-28.
- **Conclusiones**: favoritos, mejores ataques/defensas, jugadores destacados y avisos metodológicos.

## Estructura

```
juego_hockey/
  index.html   # Juego completo: CSS, datos y lógica JS
  README.md    # Este documento
```

El HTML se genera a partir de:

- `../jugadores/thumbs/` → imágenes.
- `../tools/player_attributes_v2.csv` → datos y atributos.
- `../tools/hockey_template.html` → plantilla.
- `../tools/generate_game.py` → generador.

## Modelo de valoración

### Jugador

Cada jugador tiene 37 atributos y cinco overalls. El overall principal es el de su posición natural:

```text
overall_pos = suma(atributo * peso_pos)
```

Pesos principales:

- **Portero:** reflejos 22 %, blocaje 20 %, distribución 12 %, parada de PC 12 %, parada de stroke 10 %, 1v1 8 %, paradas altas 6 %, posicionamiento 5 %, liderazgo 5 %.
- **Central:** cobertura 18 %, posicionamiento 12 %, primer runner 10 %, fuerza 10 %, stopper 8 %, pase 8 %, decisiones 8 %, agilidad 6 %, velocidad 5 %, liderazgo 5 %, transición 5 %, control 5 %.
- **Lateral:** velocidad 16 %, cobertura 14 %, resistencia 12 %, pase 10 %, conducción 8 %, transición 8 %, posicionamiento 7 %, pressing 7 %, agilidad 6 %, decisiones 6 %, primer runner 6 %.
- **Medio:** pase 16 %, posicionamiento 12 %, resistencia 12 %, pressing 8 %, transición 8 %, cobertura 7 %, conducción 7 %, decisiones 7 %, saque de PC 6 %, faltas 5 %, control 5 %, desmarque 4 %, stopper 3 %.
- **Delantero:** definición 20 %, velocidad 13 %, regate 3D 12 %, posicionamiento 8 %, conducción 8 %, aerial 6 %, tiro de PC 6 %, desvío 6 %, decisiones 6 %, resistencia 5 %, desmarque 5 %, flick 5 %.

Además:

- **Potencial:** overall + bonus juvenil o penalización por edad.
- **Valor:** `(overall/100)^4 * 2.000.000 * factor_edad * factor_posición`.
- **Polivalencia:** diferencia entre el segundo mejor overall y el natural.
- **Arquetipo:** perfil según atributos.
- **Especialistas:** roles de set pieces asignados por el máximo atributo del equipo.

Los goles solo refuerzan definición, flick, tiro de PC, desvío y stroke. **No cambian la posición ni la cobertura.** Un central con 56 goles sigue siendo central.

### Equipo

```text
attackScore  = media(definición, flick, regate_3d, pase, pc_flick, pc_deflection, velocidad)
defenseScore = media(cobertura, posicionamiento, primer_runner, pressing, transición, fuerza)
```

Para porteros, `defenseScore` añade reflejos, blocaje, parada de PC, parada de stroke, 1v1 y paradas altas.

```text
ataque  = 0.55 * media_top5_attackScore
        + 0.25 * media_attackScore
        + 0.10 * profundidad
        + 0.10 * edad

defensa = 0.55 * media_top5_defenseScore
        + 0.25 * media_defenseScore
        + 0.10 * profundidad
        + 0.10 * experiencia

overall_equipo = 0.6 * ataque + 0.4 * defensa
```

Los ratings se normalizan a 40-95 y se ajustan por liga.

## Posiciones

- **175 posiciones oficiales** (17,9 %): webs de Atlètic Terrassa, Club Egara, Egara 1935 y RC Polo, actas RFEH (porteros) y prensa.
- **801 posiciones estimadas** (82,1 %): cálculo por rol y peso goleador.
- **75 porteros**.
- **399 subposiciones Central/Lateral estimadas** cuando la fuente solo indica “Defensa”.

Cada jugador tiene:

- `position_group`: Portero, Defensa, Medio, Delantero o Polivalente.
- `subposicion`: Portero, Central, Lateral, Medio, Delantero o Polivalente.
- `posicion_fuente`: web oficial, acta RFEH, prensa o estimada.
- `posicion_confianza`: Alta, Media o Baja.
- `sub_estimada`: true si la subposición Central/Lateral es estimada.

En la interfaz, la columna **Pos.** muestra la subposición. El filtro permite Portero, Central, Lateral, Medio, Delantero y Polivalente. La ficha muestra la fuente y la confianza.

**Limitación:** la estimación no sustituye a una posición oficial. El editor permite corregirla.

## Editor

En la ficha del jugador:

1. Pulsar **Editar posición / atributos**.
2. Cambiar la posición natural.
3. Ajustar los 37 atributos.
4. **Guardar cambios**.

El editor:

- Recalcula overalls, potencial, valor, arquetipo y ratings de equipo.
- Guarda el override en `localStorage` (`hockey_overrides_v1`).
- No modifica el CSV ni el Excel.
- Muestra una etiqueta **Ajuste manual** en la ficha.
- Permite **Quitar ajuste manual**.

Para borrar todos los cambios:

```js
localStorage.removeItem('hockey_overrides_v1');
location.reload();
```

## Simulación · formato oficial 2026-27

### DHA

- 12 equipos, doble vuelta: **22 jornadas**.
- Top 4 → **Final Four** (semifinales y final; desempate por shoot-outs).
- **12º desciende** directamente.
- **11º juega el playout** al mejor de 3 contra el 2º elegible de DHB. Partido 1 en casa del DHA; partidos 2 y 3 en casa del DHB.

### DHB

- 16 equipos en **dos grupos de 8**. Primera fase: 14 partidos.
- **Grupo A** de la segunda fase: los 4 primeros de cada grupo. **Grupo B**: los 4 últimos.
- Segunda fase: 6 resultados arrastrados + 8 partidos cruzados = 14. Total: 22.
- **Final Four DHB**: los 4 primeros del Grupo A.
- **Ascenso directo:** 1º elegible del Grupo A.
- **Playout:** 2º elegible del Grupo A contra el 11º de DHA.
- **Descenso:** 15º y 16º (dos últimos del Grupo B).
- **Clubes vinculados:** Egara 1935, Vallès Esportiu, Pedralbes, Real Sociedad 1927, SPV y AD Rimas no pueden ascender si su club matriz está en DHA. El ascenso se decide por la clasificación del Grupo A, no por la Final Four.

### Motor de partido

- Goles con distribución de Poisson a partir de ataque, defensa, overall y factor local.
- En Final Four y playout, si hay empate, shoot-outs.
- Cada gol se asigna a un jugador ponderando definición, PC, edad y perfil.
- Monte Carlo (350 simulaciones por liga) para probabilidades de título.
- Los ratings son una estimación, no una predicción.

## Limitaciones

- iSquad no publica posición, minutos, asistencias ni goles encajados.
- La columna `GOLES` de iSquad parece un acumulado, no necesariamente los goles de la temporada 2026-27.
- 82,1 % de las posiciones y todos los atributos son estimaciones.
- 399 subposiciones Central/Lateral son estimadas.
- San Fernando 1ª Andaluza no tiene portero identificado.
- Los `Invitado` no son plantilla federada oficial.
- La segunda fase DHB con arrastre se ha reconstruido a partir de las clasificaciones de 2025-26 y la Circular 1; conviene validarla con la RFEH.
- El playout y la proyección DHA 2027-28 son una simulación. No se simulan todos los ascensos autonómicos.
- No se simulan Copa del Rey, EHL, lesiones, sanciones ni fatiga.
- No se aplica el 25 % de elegibilidad para play-offs.

## Próximos pasos

1. Validar los 175 perfiles oficiales y revisar los 400 defensas con subposición estimada.
2. Revisar porteros y la escala de overall.
3. Añadir altura, peso, minutos y datos de PC/stroke.
4. Exportar/importar overrides en JSON.
5. Añadir comparador de jugadores y pizarra de PC.
6. Incorporar hockey femenino y categorías juveniles.
7. Conectar con datos en vivo de iSquad/RFEH.

## Documentación

- `../docs/00_PROYECTO.md` — visión general.
- `../docs/01_SISTEMA_LIGAS.md` — formato DHA/DHB.
- `../docs/02_MODELO_ATRIBUTOS.md` — modelo de 37 atributos.
- `../docs/03_COMO_SE_JUEGA_HOCKEY.md` — reglas y set pieces.
- `../docs/04_DATOS_Y_FUENTES.md` — fuentes y cobertura.
- `../docs/05_ROADMAP.md` — próximos pasos.
- `../docs/06_CHANGELOG.md` — historial.
- `../docs/07_GUIA_JUEGO.md` — manual del juego.

## Aviso

Proyecto personal/educativo de scouting y simulación. No es una evaluación profesional ni una fuente oficial de datos.
