# Roadmap

Plan de continuación del proyecto. Prioriza la calidad del dato antes de añadir nuevas funcionalidades.

---

## 1. Visión

Convertir el proyecto en una herramienta estable para:

- consultar plantillas, posiciones y atributos del hockey español masculino;
- simular la temporada con el formato real;
- comparar jugadores por demarcación;
- documentar y compartir el conocimiento del deporte;
- permitir que entrenadores, aficionados y analistas corrijan y amplíen los datos.

---

## 2. Prioridades

### P0 — Calidad del dato

1. **Validar los 175 perfiles oficiales.**
   - Revisar nombre, equipo, posición y fuente.
   - Corregir erratas.
2. **Revisar los 400 defensas con subposición estimada.**
   - Priorizar los que tienen más goles y los que son especialistas de PC.
3. **Revisar los porteros.**
   - San Fernando 1ª Andaluza no tiene portero identificado.
   - Comprobar los 75 porteros y sus equipos.
4. **Revisar invitados.**
   - 467 perfiles; marcar cuáles son jugadores reales y cuáles completan la simulación.
5. **Actualizar plantillas y bajas.**
   - Fecha de corte: octubre de 2026.

### P1 — Modelo

1. Añadir altura, peso y envergadura.
2. Añadir datos de PC convertidos, strokes y paradas.
3. Ajustar la escala de porteros.
4. Separar overall actual y potencial con más precisión.
5. Añadir un factor de minutos jugados.
6. Añadir un factor de nivel de competición más fino.
7. Validar los especialistas con entrenadores o prensa.
8. Añadir confianza por atributo (no solo por posición).

### P2 — Juego

1. Exportar/importar overrides en JSON.
2. Añadir una vista de “pizarra” de PC.
3. Añadir comparador de jugadores.
4. Añadir filtros por atributo y por especialista.
5. Añadir una vista de plantilla por equipo con barras de atributos.
6. Añadir simulación de Copa del Rey.
7. Añadir una simulación de la temporada 2027-28.
8. Añadir modo oscuro/claro.
9. Mejorar la accesibilidad (teclado, contraste, ARIA).
10. Añadir una versión móvil.

### P3 — Expansión

1. Hockey femenino.
2. Categorías juveniles y sub-21.
3. Segunda división autonómica.
4. Otras comunidades autónomas.
5. Datos históricos de temporadas anteriores.
6. Base de datos SQLite/Postgres.
7. API de consulta.
8. Panel de administración para editar datos.

---

## 3. Hitos

| Hito | Estado | Fecha |
|---|---|---|
| Lista única de clubes | Completado | 2026-10 |
| Plantillas e imágenes | Completado | 2026-10 |
| Juego HTML v1 | Completado | 2026-10 |
| Formato real DHA/DHB | Completado | 2026-10 |
| Posiciones 976 perfiles | Completado | 2026-10 |
| Informe de ligas | Completado | 2026-10 |
| Informe de posiciones | Completado | 2026-10 |
| Atributos v1 (24) | Completado | 2026-10 |
| Atributos v2 (37 + set pieces) | Completado | 2026-10-19 |
| Editor de jugador | Completado | 2026-10-19 |
| Excel ampliado | Completado | 2026-10-19 |
| Documentación maestra | Completado | 2026-10-19 |
| Validación manual de posiciones | Pendiente | — |
| Datos de PC/stroke | Pendiente | — |
| Hockey femenino | Pendiente | — |

---

## 4. Backlog detallado

| Tarea | Impacto | Esfuerzo | Prioridad |
|---|---|---|---|
| Validar 175 posiciones oficiales | Alto | Medio | P0 |
| Revisar 399 subposiciones estimadas | Alto | Alto | P0 |
| Identificar portero de San Fernando 1ª Andaluza | Medio | Bajo | P0 |
| Revisar los 75 porteros | Medio | Medio | P0 |
| Añadir altura/peso | Medio | Medio | P1 |
| Añadir PC convertidos y strokes | Alto | Alto | P1 |
| Ajustar escala de porteros | Medio | Bajo | P1 |
| Exportar overrides | Medio | Bajo | P2 |
| Comparador de jugadores | Medio | Medio | P2 |
| Pizarra de PC | Alto | Alto | P2 |
| Simulación de Copa del Rey | Bajo | Medio | P2 |
| Hockey femenino | Alto | Alto | P3 |
| Base de datos | Alto | Alto | P3 |

---

## 5. Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Datos de plantillas cambian | Medio | Fecha de corte y actualización periódica. |
| Posiciones estimadas erróneas | Alto | Editor y revisión manual. |
| Atributos poco realistas | Alto | Calibración y validación con expertos. |
| Derechos de imagen | Medio | Uso personal/educativo y atribución. |
| Reglamento cambia | Medio | Revisar circular RFEH/FIH cada temporada. |
| Scripts en `/tmp` se pierden | Alto | Copia persistente en `tools/`. |
| HTML demasiado grande | Bajo | Datos embebidos; 1,3 MB es aceptable. |
| Navegador bloquea `localStorage` | Bajo | Manejo de errores y aviso. |

---

## 6. Definición de “hecho”

Una tarea se considera terminada cuando:

1. El dato está documentado y tiene fuente.
2. El pipeline se ejecuta sin errores.
3. El HTML se ha probado con Selenium.
4. El Excel se ha regenerado.
5. `06_CHANGELOG.md` está actualizado.
6. No hay errores en consola.
7. La documentación refleja el cambio.

---

## 7. Próxima sesión recomendada

1. Abrir `docs/00_PROYECTO.md` y `docs/02_MODELO_ATRIBUTOS.md`.
2. Ejecutar el pipeline en `tools/`.
3. Revisar 20 jugadores al azar y 10 centrales con goles.
4. Corregir posiciones en el editor o en el CSV.
5. Regenerar Excel y HTML.
6. Actualizar el changelog.

---

## 8. Ideas futuras

- **Modo carrera:** entrenar un equipo durante varias temporadas.
- **Modo draft:** elegir jugadores por atributos y construir un equipo.
- **Scouting:** comparar jugadores por percentiles y roles.
- **Pizarra táctica:** dibujar PC y jugadas.
- **Datos en vivo:** conectar con iSquad/RFEH.
- **API pública:** consultar jugadores y equipos.
- **App móvil:** versión PWA.
- **Comunidad:** que los clubes validen sus plantillas.
