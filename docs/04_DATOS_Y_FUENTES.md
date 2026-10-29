# Datos, fuentes y proceso

Documento de trazabilidad: de dónde salen los datos, cómo se han tratado, qué cobertura hay y qué limitaciones debe conocer cualquier persona que continúe el proyecto.

---

## 1. Resumen de datos

| Métrica | Valor |
|---|---:|
| Equipos | 29 |
| DHA | 12 |
| DHB | 16 |
| Primera Andaluza | 1 |
| Perfiles | 976 |
| Jugadores | 509 |
| Invitados | 467 |
| Porteros | 75 |
| Posiciones oficiales | 175 |
| Posiciones estimadas | 801 |
| Imágenes disponibles | 976 |
| Bajas registradas | 14 |
| Atributos por jugador | 37 |

### Distribución por liga

| Liga | Perfiles | Posiciones oficiales | Posiciones estimadas |
|---|---:|---:|---:|
| DHA | 412 | 103 | 309 |
| DHB | 536 | 68 | 468 |
| Primera Andaluza | 28 | 4 | 24 |
| **Total** | **976** | **175** | **801** |

### Distribución por posición

| Posición base | Perfiles |
|---|---:|
| Defensa | 400 |
| Delantero | 253 |
| Medio | 242 |
| Portero | 75 |
| Medio/Delantero | 4 |
| Defensa/Medio | 2 |

### Subposición estimada

| Subposición | Perfiles |
|---|---:|
| Central | 249 |
| Lateral | 151 |
| Medio | 242 |
| Delantero | 253 |
| Portero | 75 |
| Polivalente | 6 |

De los 400 defensas, 400 tienen subposición Central o Lateral; **399 perfiles tienen la subposición estimada** porque la fuente solo indicaba “Defensa” o no especificaba el lado.

---

## 2. Fuentes principales

### 2.1. RFEH / iSquad

- **Uso:** plantillas, nombres, edades, goles, estado, imágenes, actas.
- **Cobertura:** DHA y DHB 2026-27.
- **Fiabilidad:** alta para datos de competición; media para posiciones (no siempre publica la demarcación).
- **Limitaciones:** los goles de iSquad no distinguen PC, stroke o jugada abierta; no hay asistencias completas; algunas plantillas incluyen invitados.

### 2.2. Actas oficiales de la RFEH

- **Uso:** porteros y alineaciones.
- **Volumen:** 562 actas procesadas.
- **Cobertura:** 64 perfiles con posición oficial de portero/acta.
- **Fiabilidad:** alta para quién juega y quién es portero; baja para la subposición de los defensas.
- **Limitaciones:** no todas las actas están disponibles; algunas no detallan la posición.

### 2.3. Webs oficiales de clubes

- **Uso:** posiciones oficiales de jugadores.
- **Clubes:** Atlètic Terrassa, Club Egara, RC Polo, Egara 1935.
- **Cobertura:** 68 perfiles (18 + 33 + 17).
- **Fiabilidad:** alta, pero no todos los clubes publican plantilla con posiciones.
- **Limitaciones:** la información puede quedar desactualizada; algunos clubes solo publican dorsales o nombres.

### 2.4. Prensa

- **Uso:** posiciones de CD Terrassa.
- **Fuente:** Diari de Terrassa.
- **Cobertura:** 3 perfiles.
- **Fiabilidad:** media-alta; depende de la crónica.
- **Limitaciones:** cobertura puntual.

### 2.5. Estimación por rol y goles

- **Uso:** completar los 801 perfiles sin posición oficial.
- **Método:** posición base según el rol habitual y el peso goleador dentro del equipo; subposición Central/Lateral según el perfil y el contexto.
- **Fiabilidad:** baja-media; es una aproximación, no un dato oficial.
- **Limitaciones:** un defensa con muchos goles puede parecer delantero; por eso el modelo separa posición y atributos.

### 2.6. Reglamento y formato

- **RFEH:** Circular 1 2026-27, Reglamento de competiciones, normativa 7-2026.
- **FIH:** *Rules of Hockey*.
- **Uso:** formato de liga, desempates, PC, stroke, faltas, tarjetas y duración.
- **Fiabilidad:** alta.
- **Limitaciones:** las reglas pueden cambiar; hay que contrastar la edición vigente.

### 2.7. Actas y alineaciones: qué se puede y qué no se puede obtener

- Las **actas oficiales de la RFEH** (562 procesadas) identifican convocados, titulares, porteros, goles, tarjetas y sanciones.
- **No incluyen la posición de los jugadores de campo.** La columna `P/J` solo distingue portero (`P`) y jugador (`J`).
- Por tanto, las actas sirven para confirmar **porteros y alineaciones**, pero no para asignar central, lateral, medio o delantero.
- La **prensa local** a veces menciona posiciones individuales (“el defensa X”, “el delantero Y”) o publica alineaciones por líneas, pero no de forma sistemática para todos los equipos.
- Las **webs de clubes** que publican plantilla con posición son la fuente más fiable. La cobertura se detalla en la sección 4.
- Los **partidos EHL** y las **listas de selección** pueden confirmar posiciones de jugadores internacionales, pero solo de un subconjunto.

### 2.8. Fuentes conceptuales

- Wikipedia, *Field hockey* y *Penalty corner* (consulta 2026).
- Manuales y artículos de técnica de hockey.
- Videos y análisis de PC, drag flick y stroke.

---

## 3. Proceso de datos

### 3.1. Extracción

1. Descarga de plantillas y datos de iSquad/RFEH.
2. Procesamiento de actas para detectar porteros.
3. Revisión de webs oficiales de clubes.
4. Búsqueda de prensa para CD Terrassa.
5. Normalización de nombres, equipos y ligas.

### 3.2. Normalización

- Nombres en mayúsculas.
- Eliminación de tildes en identificadores internos, pero conservación en pantalla.
- Equipos con nombres de competición.
- Clubes con nombre completo.
- Duplicados de jugadores con distinto perfil (Jugador/Invitado) conservados.
- Imágenes asociadas por `archivo_thumb`.

### 3.3. Posiciones

- Si hay fuente oficial: se usa la posición oficial.
- Si no: se estima por rol y goles.
- Si la posición es “Defensa” sin lado: se asigna Central o Lateral según perfil y contexto.
- Si hay duda: se marca confianza Baja y `sub_estimada = True`.

### 3.4. Atributos

- Generación con `build_attributes_v2.py`.
- 37 atributos por jugador.
- Pesos por posición.
- Refuerzo por goles solo en atributos ofensivos.
- Especialistas por equipo.

### 3.5. Validación

- Comprobación de 976 filas y 29 equipos.
- Comprobación de 75 porteros.
- Revisión de ejemplos:
  - Iain Martin McFadden: Central, 73,9, Central constructor.
  - Bruno Àvila Gran: Central, 56 goles, 84,2, Muro.
- Pruebas del HTML con Selenium.
- Pruebas del editor y de `localStorage`.

---

## 4. Cobertura de posiciones

### 4.1. Por fuente

| Fuente | Perfiles | % |
|---|---:|---:|
| Estimada | 801 | 82,1 % |
| Acta oficial RFEH | 64 | 6,6 % |
| Web oficial Club Egara | 33 | 3,4 % |
| Web oficial Atlètic Terrassa | 18 | 1,8 % |
| Web oficial RC Polo | 17 | 1,7 % |
| Prensa (Diari de Terrassa) | 6 | 0,6 % |
| Mundo Deportivo (selección española 2025) | 4 | 0,4 % |
| EuroHockey (selección sub-21) | 3 | 0,3 % |
| Global Sports Archive | 2 | 0,2 % |
| Diari de Terrassa | 2 | 0,2 % |
| Canarias7 | 1 | 0,1 % |
| Confederación Argentina de Hockey | 1 | 0,1 % |
| 8SPORTS.es | 1 | 0,1 % |
| University of Pretoria | 1 | 0,1 % |
| Deporte de la Isla | 19 | 1,9 % |
| Deporte Alicante | 1 | 0,1 % |
| El Castillo de San Fernando | 1 | 0,1 % |
| Web oficial CD Giner de los Ríos | 1 | 0,1 % |
| **Total** | **976** | **100 %** |

### 4.2. Por confianza

| Confianza | Perfiles |
|---|---:|
| Alta | 150 |
| Media | 169 |
| Baja | 657 |

### 4.3. Por liga y fuente

| Liga | Acta | Estimada | Prensa | Atlètic | Egara | RC Polo |
|---|---:|---:|---:|---:|---:|---:|
| DHA | 31 | 309 | 6 | 18 | 18 | 17 |
| DHB | 33 | 468 | 0 | 0 | 15 | 0 |
| Primera Andaluza | 0 | 24 | 0 | 0 | 0 | 0 |

> La tabla no incluye las columnas de Mundo Deportivo (4), EuroHockey (3), GSA (2), Diari de Terrassa (2), Canarias7 (1), CAH (1), 8SPORTS.es (1), University of Pretoria (1), Deporte de la Isla (19), Deporte Alicante (1), El Castillo de San Fernando (1) ni Web oficial CD Giner de los Ríos (1); están contabilizadas en la tabla 4.1.

### 4.4. Huecos conocidos

- **Primera Andaluza:** 4 posiciones oficiales y 24 estimadas. La cobertura sigue siendo baja; la mayoría de la plantilla no tiene posición oficial.
- **Defensas genéricos:** 399 de los 400 defensas tienen subposición Central/Lateral estimada; solo uno tiene lateral explícito.
- **Invitados:** 467 perfiles no son plantilla oficial; su posición y atributos son más inciertos.
- **Bajas:** 14 perfiles tienen fecha de baja; se mantienen para contexto histórico.

---

## 5. Estructura de archivos

### 5.1. `tools/todos_manifest_positions.csv`

Base de 976 perfiles. Columnas principales:

| Columna | Contenido |
|---|---|
| `liga` | DHA, DHB, 1ª Andaluza. |
| `equipo` | Nombre de competición. |
| `club` | Nombre completo del club. |
| `perfil` | Jugador o Invitado. |
| `jugador` | Nombre. |
| `edad` | Edad. |
| `goles` | Goles iSquad (puede ser “-”). |
| `fecha_baja` | Fecha de baja, si existe. |
| `pos` | Posición base. |
| `src` | Fuente de la posición. |
| `conf` | Confianza. |
| `archivo_thumb` | Archivo de imagen. |

### 5.2. `tools/player_attributes_v2.csv`

Salida del modelo. Columnas nuevas:

- `position_group`, `subposicion`, `sub_estimada`.
- `archetype`, `overall`, `potential`, `value`, `polivalencia`.
- `overall_portero`, `overall_central`, `overall_lateral`, `overall_medio`, `overall_delantero`.
- `attr_*`: 37 atributos.
- `team_specialists`: JSON con los 10 roles del equipo.

### 5.3. `jugadores_atributos_2026_27.csv`

Versión legible para Excel/CSV:

- Datos base.
- Posición y grupo.
- Overall, potencial, valor.
- 37 atributos con etiquetas.
- Especialistas.

### 5.4. Excel

`equipos_hockey_hierba_espana_masculino_2026_27_con_atributos.xlsx`:

| Hoja | Contenido |
|---|---|
| Equipos únicos | Clubes y equipos. |
| Jugadores DHA | Plantilla con posiciones, overall y especialistas. |
| Jugadores DHB | Ídem. |
| San Fernando 1ª Andaluza | Ídem. |
| Resumen plantillas | Agregados por equipo. |
| Cobertura posiciones | Fuentes y cobertura. |
| Filiales excluidos | Equipos descartados. |
| Resumen por liga | Equipos y filiales. |
| Fuentes | Fuentes generales. |
| Notas | Notas del proyecto. |
| Notas jugadores | Notas de datos. |
| Atributos | 976 filas × 37 atributos. |
| Especialistas | 29 equipos × 10 roles. |
| Equipos atributos | Medias por equipo y categoría. |
| Diccionario atributos | Definición de cada atributo. |
| Cobertura atributos | Cobertura y limitaciones. |
| Fuentes atributos | Fuentes del modelo. |

---

## 6. Reproducibilidad

```bash
cd /home/daniel/hockey_espana/tools

python3 build_attributes_v2.py
python3 generate_game.py
python3 build_excel_attributes.py
```

### Dependencias

- Python 3.
- pandas.
- numpy.
- openpyxl.
- Selenium + Chromium (solo para pruebas).

### Semilla

`build_attributes_v2.py` usa una semilla determinista por jugador, equipo y versión:

```python
hashlib.md5((jugador + '|' + equipo + '|v2').encode()).hexdigest()
```

Si se cambia el orden de los atributos o se añaden draws aleatorios, los valores cambian. Hay que regenerar todo el pipeline.

---

## 7. Calidad del dato

### 7.1. Puntos fuertes

- Cobertura completa de 976 perfiles.
- 29 equipos únicos.
- Imágenes para todos.
- Formato de liga real.
- Atributos específicos de hockey.
- Especialistas de set pieces.
- Editor para corregir.

### 7.2. Puntos débiles

- 86 % de posiciones estimadas.
- 399 subposiciones estimadas.
- Sin datos oficiales de asistencias, PC, strokes o paradas.
- Sin minutos jugados.
- Sin lesiones/sanciones.
- Sin altura/peso.
- Sin datos de categorías inferiores.
- Sin hockey femenino.

### 7.3. Cómo mejorar

1. Validar manualmente los 175 perfiles oficiales.
2. Revisar los 400 defensas con subposición estimada.
3. Buscar actas con posición detallada.
4. Añadir datos de PC y strokes de crónicas o video.
5. Incorporar altura/peso de fichas oficiales.
6. Añadir minutos y participaciones.
7. Contrastar con entrenadores/clubes.

---

## 8. Privacidad y uso

- Los datos son de fuentes públicas (RFEH, clubes, prensa).
- Las imágenes se usan para identificación deportiva en un proyecto personal/educativo.
- No se publican datos sensibles.
- Si el proyecto se hace público, revisar derechos de imagen y condiciones de uso de las fuentes.
- Citar siempre la fuente y la fecha de corte.

---

## 9. Fecha de corte

- Datos de plantillas y goles: octubre de 2026.
- Clasificaciones: provisionales a 19/10/2026.
- Reglamento: circular 2026-27.
- Atributos: modelo v2, generado el 19/10/2026.

---

## 10. Fuentes citadas

- RFEH: <https://www.rfeh.es/>
- RFEH/iSquad: datos de competición.
- FIH: <https://www.fih.hockey/>
- Atlètic Terrassa: web oficial.
- Club Egara: web oficial.
- RC Polo: web oficial.
- Egara 1935: web oficial.
- Diari de Terrassa: prensa.
- Wikipedia: *Field hockey*, *Penalty corner*.
- Informes del proyecto:
  - `informe_sistema_ligas_DHA_DHB_2026_27.md`
  - `informe_posiciones_DHA_DHB_2026_27.md`

> Las URLs y la disponibilidad de las fuentes pueden cambiar. Guardar una copia o captura de las páginas clave si se necesita auditar el proyecto en el futuro.
