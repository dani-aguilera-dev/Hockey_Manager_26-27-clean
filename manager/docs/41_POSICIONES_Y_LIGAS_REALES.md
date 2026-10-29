# Posiciones y cierre de ligas internacionales

**Fecha:** 2026-10-28.

## 1. Cobertura final

| Liga | Clubes | Jugadores reales | Escudos | Posiciones |
|---|---:|---:|---:|---|
| Hoofdklasse (NED) | 12 | 250 | 12 | Publicadas por los clubes |
| Belgian League (BEL) | 12 | 242 | 12 | Publicadas por la liga |
| Bundesliga (GER) | 12 | 318 | 12 | Estimadas; la liga no publica demarcación |
| Premier Division (ENG) | 12 | 243 | 12 | Estimadas desde convocatoria oficial |
| Metropolitano (ARG) | 14 | 433 | 14 | Estimadas desde planillas oficiales |
| Hockey India League (IND) | 8 | 158 | 8 | Publicadas por la liga |

La liga argentina pasa de 12 a **14 clubes**, los reales del Metropolitano A 2026. En Inglaterra entra **Bowdon** y sale Southgate, según la lista oficial 2026-27.

## 2. Fuentes de posiciones

### Países Bajos

Las webs de los clubes publican `Keeper`, `Verdediger`, `Middenvelder` y `Aanvaller`. El importador traduce esos términos al modelo español. Se corrigió la lectura de `Aanvaller` (delantero) y `Middenvelder` (medio), que antes podían caer en el valor por defecto.

### Bélgica

La ficha oficial de la Carlsberg 0.0 Hockey League publica `Goalkeeper`, `Defence`, `Midfield` y `Attack`. Se añadieron esas etiquetas al traductor. El jugador utility Nicolas De Kerpel, publicado como `ALL`, se clasifica como medio.

### Alemania

La Bundesliga publica plantilla y foto, pero no demarcación individual. Se mantiene la estimación por composición de plantilla y se marca como tal.

### Inglaterra

Fuente: API oficial de England Hockey GMS.

- 12 clubes y 243 jugadores con apariciones oficiales.
- Los porteros confirmados en las actas EHL se respetan.
- El resto de posiciones se estima por composición de la convocatoria.
- Escudos: `clubLogoUrl` oficial de la API.

### Argentina

Fuente: API TournamentTracker de la AAHBA y **182 planillas PDF** del Torneo Metropolitano A 2026.

- 14 clubes y 433 nombres reales.
- Los nombres salen de las planillas oficiales de cada partido.
- Las planillas no publican la posición individual; se estima por composición de plantilla.
- Escudos: catálogo oficial de clubes de la AAHBA.

## 3. Correcciones de calidad

- Se eliminó de NED una ficha de `Teamarts` (médico) que el scraper había confundido con jugador.
- Se corrigió **Luis Calzado** (Kampong): es portero, no mediocentro. La ficha del club solo publicaba dorsal; se verificó con Wikipedia/FIH y se añadió una corrección estable en `POSITION_OVERRIDES`.
- Se limpiaron etiquetas neerlandesas e inglesas que antes caían en `Medio` por defecto.
- Se deduplicaron jugadores por identificador/nombre dentro de cada club.
- No se han inventado nombres: ENG y ARG usan convocatorias oficiales.
- Las posiciones estimadas se identifican como tales; no se presentan como datos oficiales.

## 4. Limitaciones

- ENG y ARG no tienen fotos locales de jugador; se usan avatares.
- Las posiciones de ENG/ARG son estimaciones, no demarcaciones oficiales.
- El Metropolitano tiene 14 clubes y 26 jornadas; el calendario del juego se adapta a ese formato.
- Los ratings internacionales se calibran por liga para respetar la jerarquía NED > BEL > GER > ENG > ARG > IND.

## 5. Archivos

- `tools/fetch_eng_real.py`: importador England Hockey GMS.
- `tools/fetch_arg_real.py`: importador AAHBA/TournamentTracker y planillas.
- `manager/data/international_real.json`: plantillas reales.
- `manager/data/international.json`: clubes, ciudades y metadatos.
- `manager/src/international.py`: traducción de posiciones y calibración.
- `manager/web/static/crests/eng-*.png` y `arg-*.png`: escudos oficiales.
