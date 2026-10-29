# Tools

Scripts y datos para regenerar el proyecto.

## Pipeline

```bash
cd /home/daniel/hockey_espana/tools

# 0. Plantillas autonómicas (iSquad)
python3 fetch_lower_divisions.py

# 1. Atributos
python3 build_attributes_v2.py

# 2. Juego
python3 generate_game.py

# 3. Excel y CSV
python3 build_excel_attributes.py

# 4. Informes (opcional)
python3 md_to_html.py ../informe_posiciones_DHA_DHB_2026_27.md ../informe_posiciones_DHA_DHB_2026_27.html
python3 md_to_pdf.py ../informe_posiciones_DHA_DHB_2026_27.md ../informe_posiciones_DHA_DHB_2026_27.pdf
```

## Archivos

| Archivo | Función |
|---|---|
| `build_attributes_v2.py` | Genera 37 atributos, overalls, arquetipos, polivalencia y especialistas. |
| `generate_game.py` | Inserta los datos en `hockey_template.html` y escribe `../juego_hockey/index.html`. |
| `build_excel_attributes.py` | Genera el Excel ampliado y `../jugadores_atributos_2026_27.csv`. |
| `apply_positions.py` | Aplica posiciones nuevas al manifiesto (con backup y `--dry-run`). |
| `position_sources.csv` | Catálogo de fuentes de posiciones: URL, fecha y cobertura. |
| `new_positions.csv` | Lote de posiciones nuevas pendientes/aplicadas. |
| `hockey_template.html` | Plantilla del juego (CSS + lógica JS + placeholder de datos). |
| `md_to_html.py` | Convierte Markdown a HTML con estilo de informe. |
| `md_to_pdf.py` | Convierte Markdown a PDF con WeasyPrint. |
| `todos_manifest_positions.csv` | Base de 976 perfiles con posiciones y fuentes. |
| `player_attributes_v2.csv` | Salida del modelo de atributos. |
| `lower_divisions_players.csv` | Plantillas de divisiones autonómicas descargadas de iSquad. |
| `fetch_lower_divisions.py` | Descarga y normaliza plantillas autonómicas para agentes libres. |
| `official_positions.json` | Posiciones oficiales recopiladas. |
| `actas_gk.json` | Porteros detectados en actas RFEH. |

## Dependencias

- Python 3.
- pandas, numpy, openpyxl.
- markdown, weasyprint (solo para informes).
- Selenium + Chromium (solo para pruebas).

## Notas

- No editar `../juego_hockey/index.html` a mano: regenerarlo.
- La semilla del modelo es determinista por jugador, equipo y versión.
- Si se cambia el orden de los atributos, los valores cambian; regenerar todo el pipeline.
- Los overrides del editor se guardan en el navegador, no en estos archivos.
