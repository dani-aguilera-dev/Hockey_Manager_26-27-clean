# Proyecto Hockey España Masculino 2026-27

**Estado:** versión funcional con modelo avanzado de atributos, editor y documentación.
**Fecha de actualización:** 19 de octubre de 2026.
**Ámbito:** hockey hierba masculino sénior en España.
**Ligas:** División de Honor A (DHA), División de Honor B (DHB) y primera división autonómica andaluza (San Fernando).

---

## 1. Objetivo

Construir una base de datos y un simulador de la temporada 2026-27 del hockey hierba masculino español que permita:

1. Identificar clubes únicos y plantillas reales, sin filiales ni duplicados.
2. Asignar posición y rol a cada jugador.
3. Valorar a cada jugador con atributos propios del hockey, no solo con goles.
4. Diferenciar el rendimiento por demarcación: portero, central, lateral, medio y delantero.
5. Modelar las acciones específicas del hockey: penalty corner, stroke, faltas, 16 yardas, aerial, 3D, etc.
6. Simular la liga con el formato real de DHA y DHB, incluidas Final Four, playout y ascensos/descensos.
7. Permitir que un usuario corrija posiciones y atributos sin tocar el código.
8. Documentar todo el proceso para que otro agente o persona pueda continuar.

---

## 2. Alcance

### Incluido

- 29 equipos:
  - 12 de DHA.
  - 16 de DHB.
  - 1 de Primera División Andaluza: Club de Hockey San Fernando.
- 976 perfiles:
  - 509 jugadores.
  - 467 invitados.
- Fotos de jugadores en el juego.
- Formato real de competición 2026-27.
- Modelo de 37 atributos por jugador.
- Cinco *overalls* posicionales.
- Arquetipos y especialistas de set pieces.
- Editor de posición y atributos en el navegador.
- Excel, CSV y HTML autocontenido.

### Excluido o pendiente

- Hockey femenino.
- Categorías juvenil, sub-21 y veteranos.
- Segunda división autonómica y categorías inferiores.
- Datos oficiales completos de atributos: no existen públicos para toda la base.
- Estadísticas oficiales de asistencias, PC, strokes, paradas, etc. para todos los jugadores.
- Lesiones, sanciones y disponibilidad semanal.
- Scouting presencial de los 976 perfiles.

---

## 3. Entregables

| Entregable | Ruta | Estado |
|---|---|---|
| Juego HTML autocontenido | `juego_hockey/index.html` | Funcional |
| README del juego | `juego_hockey/README.md` | Actualizado |
| Excel de equipos y jugadores con posiciones | `equipos_hockey_hierba_espana_masculino_2026_27_con_posiciones.xlsx` | Base |
| Excel ampliado con atributos | `equipos_hockey_hierba_espana_masculino_2026_27_con_atributos.xlsx` | Nuevo |
| CSV de jugadores con atributos | `jugadores_atributos_2026_27.csv` | Nuevo |
| CSV de posiciones | `jugadores_posiciones_2026_27.csv` | Base |
| Informe de ligas | `informe_sistema_ligas_DHA_DHB_2026_27.md` y `.pdf` | Listo |
| Informe de posiciones | `informe_posiciones_DHA_DHB_2026_27.md` y `.pdf` | Listo |
| Scripts reproducibles | `tools/` | Nuevo |
| Documentación maestra | `docs/` | Nueva |
| Diseño del juego Manager | `manager/docs/` | Nuevo |
| Prototipo de texto | `manager/src/prototype.py` | Funcional |
| PDF de documentación | `docs/00_PROYECTO.pdf`, `02_MODELO_ATRIBUTOS.pdf`, `03_COMO_SE_JUEGA_HOCKEY.pdf`, `07_GUIA_JUEGO.pdf` | Nuevo |

### Scripts en `tools/`

| Script | Función |
|---|---|
| `build_attributes_v2.py` | Genera los 37 atributos, overalls, arquetipos y especialistas. |
| `generate_game.py` | Inserta los datos en la plantilla y produce `index.html`. |
| `build_excel_attributes.py` | Genera el Excel ampliado y el CSV de atributos. |
| `hockey_template.html` | Plantilla del juego. |
| `todos_manifest_positions.csv` | Base de 976 perfiles con posiciones. |
| `player_attributes_v2.csv` | Salida del modelo de atributos. |
| `official_positions.json` | Posiciones oficiales recopiladas. |
| `actas_gk.json` | Porteros detectados en actas RFEH. |
| `md_to_html.py` | Convierte un informe Markdown a HTML. |
| `md_to_pdf.py` | Convierte un informe Markdown a PDF. |

---

## 4. Estado actual

### Completado

- Lista única de clubes de DHA, DHB y primeras divisiones autonómicas, sin filiales.
- Plantillas de 2026-27 con jugadores e invitados.
- Fotos incrustadas en el HTML y en el Excel.
- Posiciones para los 976 perfiles:
  - 175 oficiales (17,9 %).
  - 801 estimadas (82,1 %).
  - 75 porteros.
- Informe del sistema de ligas DHA/DHB.
- Informe de posiciones y fuentes.
- Simulador con formato real:
  - DHA: 22 jornadas, Final Four, descenso directo y playout.
  - DHB: dos grupos de 8, primera fase, segunda fase A/B con arrastre, Final Four, ascenso y descenso.
  - Clubes vinculados: elegibilidad para ascender.
- Modelo de 37 atributos en seis grupos.
- Cinco overalls por posición y arquetipos.
- Especialistas de penalty corner, stroke, aerial y faltas.
- Editor de jugador con `localStorage`.
- Excel ampliado con hojas de atributos, especialistas, diccionario y cobertura.

### En curso

- Calibración fina del modelo con validación manual.
- Revisión de los centrales con perfil de drag flicker.
- Revisión de los porteros y de la escala de overall.
- Pruebas de usabilidad del editor.

### Bloqueado o limitado

- No hay una fuente pública completa de posiciones de todos los jugadores.
- No hay una fuente pública de atributos avanzados para todos los jugadores.
- Los 801 perfiles estimados y los 976 conjuntos de atributos son modelos, no datos oficiales.
- La temporada 2026-27 está en curso: las plantillas y clasificaciones pueden cambiar.

---

## 5. Cifras clave

| Métrica | Valor |
|---|---:|
| Equipos | 29 |
| DHA | 12 |
| DHB | 16 |
| Primera Andaluza | 1 |
| Perfiles | 976 |
| Jugadores | 509 |
| Invitados | 467 |
| Porteros | 72 |
| Posiciones oficiales | 175 |
| Posiciones estimadas | 801 |
| Atributos por jugador | 37 |
| Overall posicionales | 5 |
| Especialistas por equipo | 10 |
| Overall medio | 68,95 |
| Desviación típica del overall | 8,10 |
| Overall mínimo | 46,5 |
| Overall máximo | 93,2 |

---

## 6. Arquitectura y pipeline

```
iSquad / RFEH / webs de clubes / prensa
                │
                ▼
todos_manifest_positions.csv
  · 976 perfiles
  · posición, fuente y confianza
                │
                ▼
build_attributes_v2.py
  · 37 atributos
  · overalls por posición
  · arquetipo, polivalencia, potencial, valor
  · especialistas por equipo
                │
                ▼
player_attributes_v2.csv
                │
       ┌────────┴────────┐
       ▼                 ▼
generate_game.py    build_excel_attributes.py
       │                 │
       ▼                 ▼
juego_hockey/       Excel + CSV
index.html          de atributos
```

### Flujo de trabajo

```bash
cd /home/daniel/hockey_espana/tools

# 1. Regenerar atributos
python3 build_attributes_v2.py

# 2. Regenerar el juego
python3 generate_game.py

# 3. Regenerar Excel y CSV
python3 build_excel_attributes.py
```

El juego se abre directamente:

```bash
xdg-open /home/daniel/hockey_espana/juego_hockey/index.html
```

No necesita servidor: las imágenes y los datos van embebidos.

---

## 7. Decisiones de diseño

1. **Un club, un equipo.** Se excluyen filiales y equipos duplicados. Los clubes vinculados se mantienen como equipos distintos, pero no pueden ascender si su club matriz está en DHA.
2. **La posición oficial manda.** Si hay posición oficial de club, acta o prensa, se respeta. La estimación solo cubre lo que no está documentado.
3. **Los goles no definen la posición.** Un central con 56 goles sigue siendo central. Los goles refuerzan definición, flick, PC y stroke, pero no cambian la demarcación.
4. **Overall posicional.** Cada jugador tiene cinco overalls; el principal es el de su posición natural. Así un central no se compara con un delantero como si fueran lo mismo.
5. **Especialistas.** Un equipo tiene inyector, stopper, drag flicker, desviador, primer runner, portero de PC, tirador de stroke, portero de stroke, especialista aéreo y especialista en faltas.
6. **Editor local.** El usuario puede corregir posición y atributos; los cambios se guardan en el navegador y no alteran el CSV original.
7. **Transparencia.** El juego y el Excel indican qué posiciones son oficiales y cuáles estimadas.

---

## 8. Limitaciones y advertencias

- **Los atributos son estimaciones.** No son datos oficiales de la RFEH ni de los clubes.
- **La posición estimada puede fallar.** Especialmente en defensas que solo aparecen como "Defensa" y en jugadores con pocos minutos.
- **Los invitados no son plantilla oficial.** Se incluyen para completar la simulación y la información disponible.
- **El overall no es una verdad absoluta.** Es una herramienta de comparación y simulación.
- **Las clasificaciones y plantillas cambian.** Fecha de corte de datos: octubre de 2026.
- **El modelo no predice resultados reales.** La simulación es lúdica y educativa.

---

## 9. Mapa de documentación

| Documento | Contenido |
|---|---|
| `00_PROYECTO.md` | Visión general, estado, arquitectura y entregables. |
| `01_SISTEMA_LIGAS.md` | Formato real de DHA/DHB, fases, ascensos, descensos y clubes vinculados. |
| `02_MODELO_ATRIBUTOS.md` | 37 atributos, pesos, fórmulas, especialistas, calibración y ejemplos. |
| `03_COMO_SE_JUEGA_HOCKEY.md` | Reglas, posiciones, fases, set pieces, portero y táctica. |
| `04_DATOS_Y_FUENTES.md` | Fuentes, cobertura, proceso de datos y reproducibilidad. |
| `05_ROADMAP.md` | Próximos pasos, prioridades y mejoras. |
| `06_CHANGELOG.md` | Historial de cambios del proyecto. |
| `07_GUIA_JUEGO.md` | Manual de uso del HTML, filtros, simulador y editor. |
| `../manager/README.md` | Diseño y prototipo del juego de gestión/entrenador. |

Informes complementarios:

- `informe_sistema_ligas_DHA_DHB_2026_27.md`
- `informe_posiciones_DHA_DHB_2026_27.md`

---

## 10. Próximos pasos recomendados

1. Validar manualmente los 175 perfiles oficiales y revisar los centrales con más goles.
2. Revisar los porteros y ajustar la escala de overall si se detectan desviaciones.
3. Añadir asistencias, goles de PC, strokes y paradas cuando haya datos.
4. Incorporar datos de la temporada 2026-27 jornada a jornada.
5. Añadir hockey femenino y categorías juveniles.
6. Exportar el editor a un fichero JSON para compartir configuraciones.
7. Crear una versión con base de datos real (SQLite/Postgres) si el proyecto crece.
8. Implementar la Fase 1 del juego Manager: dashboard, calendario, motor de partido y logística.

---

## 11. Contacto y continuidad

Este proyecto se ha construido de forma incremental y documentada. Si otra persona o agente continúa:

1. Leer `00_PROYECTO.md`, `02_MODELO_ATRIBUTOS.md` y `04_DATOS_Y_FUENTES.md`.
2. Revisar `tools/` antes de modificar el HTML.
3. No editar `juego_hockey/index.html` a mano: regenerarlo desde `tools/hockey_template.html` y `generate_game.py`.
4. Guardar cualquier cambio de datos en `tools/` y volver a ejecutar el pipeline.
5. Actualizar `06_CHANGELOG.md` con cada cambio relevante.
