# Guía del juego HTML

Manual de uso de `juego_hockey/index.html`: vistas, filtros, fichas, simulador, editor y solución de problemas.

---

## 1. Abrir el juego

```bash
xdg-open /home/daniel/hockey_espana/juego_hockey/index.html
```

También se puede abrir con doble clic desde el explorador de archivos. No necesita servidor web: los datos y las imágenes van embebidos o se cargan desde rutas relativas del proyecto.

Navegadores recomendados:

- Chrome / Chromium.
- Firefox.
- Edge.

El juego está pensado para escritorio; en móvil o tablet puede requerir scroll horizontal.

---

## 2. Estructura de la interfaz

La barra lateral tiene cinco vistas:

| Vista | Contenido |
|---|---|
| **Inicio** | Resumen, favoritos, KPIs y accesos rápidos. |
| **Equipos** | Equipos por liga, ratings, plantilla y especialistas. |
| **Jugadores** | Tabla filtrable de los 976 perfiles. |
| **Simulador** | DHA, DHB, Final Four, playout y resumen de temporada. |
| **Conclusiones** | Insights automáticos del modelo. |

---

## 3. Inicio

Muestra:

- Número de equipos, jugadores y perfiles.
- Favorito DHA y DHB según el modelo.
- Probabilidad de título estimada con Monte Carlo.
- Jugadores destacados.
- Accesos a equipos y jugadores.

Los ratings son una estimación del modelo, no una predicción oficial.

---

## 4. Equipos

### 4.1. Filtros

- **Liga:** DHA, DHB, Primera Andaluza o todas.
- **Orden:** rating, nombre, etc. (según la vista).
- **Buscador:** por equipo o club.

### 4.2. Tarjeta de equipo

Muestra:

- Nombre y escudo/iniciales.
- Liga.
- Rating de ataque, defensa y overall.
- Estrellas.
- Probabilidad de título.
- Posición en la clasificación del modelo.

### 4.3. Ficha de equipo

Al hacer clic en un equipo:

- Datos generales.
- Edad media, goles, número de jugadores e invitados.
- Ratings.
- **Especialistas:** inyector, stopper, drag flicker, desviador, primer runner, portero de PC, tirador de stroke, portero de stroke, aéreo y faltas.
- **Set pieces:** barras de PC ataque, PC defensa, stroke, parada de stroke y aerial.
- **Plantilla:** tabla con posición, edad, goles, overall, potencial, valor y estrellas.
- Al hacer clic en un jugador se abre su ficha.

---

## 5. Jugadores

### 5.1. Filtros

- **Buscar:** nombre, equipo o club.
- **Liga:** DHA, DHB, Primera Andaluza.
- **Equipo:** todos o uno concreto.
- **Posición:** Portero, Central, Lateral, Medio, Delantero, Polivalente.
- **Orden:** overall, potencial, valor, goles, edad, nombre.

### 5.2. Tabla

Columnas:

| Columna | Contenido |
|---|---|
| # | Posición en el orden actual. |
| Jugador | Nombre, foto y arquetipo. |
| Pos. | Subposición (Central, Lateral, etc.). |
| Equipo | Equipo. |
| Liga | DHA/DHB/1ª Andaluza. |
| Edad | Edad. |
| Goles | Goles iSquad. |
| Overall | Overall de su posición natural. |
| Potencial | Potencial estimado. |
| Valor | Valor de mercado estimado. |
| Estrellas | Valoración visual. |

### 5.3. Ficha de jugador

Incluye:

- Foto, nombre, equipo, liga, posición, edad, perfil y estado.
- Etiquetas de especialista.
- Overall, potencial, goles y valor.
- Barras de overall, potencial y percentil de goles.
- Texto de scouting.
- Fuente y confianza de la posición.
- Botón **Editar posición / atributos**.
- Arquetipo y polivalencia.
- Estrellas.
- **Valoración por posición:** cinco barras (Portero, Central, Lateral, Medio, Delantero).
- **Atributos:** 37 barras agrupadas en:
  - Técnica.
  - 3D y set pieces.
  - Táctica.
  - Física.
  - Mental.
  - Portero.

---

## 6. Editor de jugador

### 6.1. Abrir

En la ficha del jugador, pulsar **Editar posición / atributos**.

### 6.2. Cambiar posición

Selector **Posición natural**:

- Portero.
- Central.
- Lateral.
- Medio.
- Delantero.
- Polivalente.

Al guardar, el overall se recalcula con los pesos de la nueva posición.

### 6.3. Cambiar atributos

El editor muestra los 37 atributos agrupados. Cada uno tiene un campo numérico de 25 a 99.

Ejemplo para un central con goles:

1. Posición: Central.
2. Cobertura: 88.
3. Posicionamiento: 85.
4. Primer runner: 80.
5. PC flick: 85.
6. Definición: 60.

Al guardar, el overall central sube, pero el jugador sigue siendo central.

### 6.4. Guardar

- **Guardar cambios:** aplica los cambios, recalcula overalls, potencial, valor, arquetipo, polivalencia, ratings de equipo y probabilidades.
- **Cancelar:** vuelve a la ficha sin guardar.
- **Quitar ajuste manual:** elimina el override de ese jugador y recarga la página.

### 6.5. Persistencia

Los cambios se guardan en `localStorage` del navegador con la clave:

```
hockey_overrides_v1
```

La ficha del jugador muestra una etiqueta **Ajuste manual** y un aviso cuando hay un override activo.

No modifican:

- `player_attributes_v2.csv`;
- el Excel;
- el HTML;
- los datos de otros navegadores.

### 6.6. Borrar todos los cambios

Abrir la consola del navegador (F12) y ejecutar:

```js
localStorage.removeItem('hockey_overrides_v1');
location.reload();
```

### 6.7. Limitaciones

- Si el navegador bloquea `localStorage`, los cambios no persisten.
- Los cambios son locales; no se comparten.
- El editor no valida coherencia deportiva: un portero con definición 99 es posible, pero irreal.
- El resto de atributos no editados se mantiene.

---

## 7. Simulador

### 7.1. DHA

- 12 equipos.
- 22 jornadas.
- Botón **Simular jornada** y **Simular liga**.
- Clasificación con puntos, goles, diferencia.
- Top 4 → Final Four.
- 12º → descenso.
- 11º → playout.

### 7.2. DHB

- 16 equipos en dos grupos.
- Primera fase: 14 jornadas.
- Segunda fase: Grupo A/B.
- Botón **Simular jornada** y **Simular liga**.
- Final Four.
- Ascenso del 1º elegible.
- Playout del 2º elegible.
- Descenso de 15º y 16º.

### 7.3. Final Four

- Semifinales y final.
- Se juega después de la liga regular.
- El campeón se muestra en el resumen.

### 7.4. Playout

- 11º DHA vs 2º elegible DHB.
- Al mejor de 3.
- Se muestra el ganador y la plaza.

### 7.5. Resumen de temporada

- Campeón DHA.
- Campeón DHB.
- Ascensos.
- Descensos.
- Ganador del playout.
- Proyección DHA 2027-28.

### 7.6. Simulación Monte Carlo

- Se ejecuta al cargar y al guardar un override.
- Estima probabilidades de título y ascenso.
- No es una predicción real; usa los ratings del modelo.

### 7.7. Limitaciones

- No simula Copa del Rey ni EHL.
- No simula todos los ascensos autonómicos.
- No aplica el 25 % de elegibilidad.
- No modela lesiones, sanciones ni fatiga.
- Los resultados son lúdicos.

---

## 8. Conclusiones

Genera insights automáticos:

- Favoritos.
- Mejores ataques y defensas.
- Jugadores destacados.
- Equipos con más especialistas.
- Comparativas por liga.

Los textos se basan en los ratings y atributos del modelo.

---

## 9. Atajos y accesibilidad

- **Esc:** cerrar modal.
- **Clic fuera del modal:** cerrar.
- **Tab:** navegar por controles.
- **Enter/Espacio:** activar botones.
- Los modales tienen botón de cierre.
- Las imágenes tienen texto alternativo.
- Algunos colores pueden no cumplir contraste AAA; revisar si se publica.

---

## 10. Solución de problemas

### El juego no carga

- Verificar que `index.html` existe.
- Abrir con Chrome/Firefox.
- Revisar la consola (F12) por errores.

### Las imágenes no aparecen

- Verificar la carpeta `../jugadores/thumbs/`.
- Si se movió el HTML, las rutas relativas cambian.
- Las imágenes están embebidas en el Excel, no en el HTML; el HTML usa rutas relativas.

### El editor no guarda

- Revisar que `localStorage` está permitido.
- No abrir en modo incógnito con bloqueo.
- Probar en otro navegador.

### Los cambios no se ven en el Excel

- El editor guarda solo en el navegador.
- Para cambiar el Excel, editar `tools/player_attributes_v2.csv` y regenerar.

### El juego va lento

- El HTML pesa ~1,3 MB y carga 976 imágenes.
- Cerrar otras pestañas.
- Usar un navegador actualizado.
- En móvil, puede ir lento.

### Los ratings cambian al guardar

- Es normal: el editor recalcula los ratings del equipo y las probabilidades.
- Si se quiere volver al estado original, usar **Quitar ajuste manual** o borrar `localStorage`.

---

## 11. Actualizar datos

```bash
cd /home/daniel/hockey_espana/tools

python3 build_attributes_v2.py
python3 generate_game.py
python3 build_excel_attributes.py
```

Luego recargar el HTML con Ctrl+F5.

---

## 12. Buenas prácticas

- No editar `juego_hockey/index.html` a mano.
- Guardar cambios de datos en `tools/`.
- Documentar chaque cambio en `docs/06_CHANGELOG.md`.
- Probar con Selenium después de regenerar.
- Hacer copia de seguridad antes de cambios grandes.
- Mantener una fecha de corte visible.

---

## 13. Glosario rápido

| Término | Significado |
|---|---|
| Overall | Valoración global de 0 a 100. |
| Overall posicional | Overall calculado con los pesos de una posición. |
| Potencial | Overall futuro estimado. |
| Polivalencia | Capacidad de rendir en otra posición. |
| Arquetipo | Perfil de jugador (Muro, Finalizador, etc.). |
| Especialista | Rol de set piece (inyector, stopper, etc.). |
| Override | Cambio manual guardado en el navegador. |
| Monte Carlo | Simulación repetida para estimar probabilidades. |
