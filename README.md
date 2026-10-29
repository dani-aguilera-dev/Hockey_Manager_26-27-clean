# Hockey España Masculino 2026-27

Proyecto de datos, scouting y simulación del hockey hierba masculino español: **DHA**, **DHB** y **Primera Andaluza**.

## Inicio rápido

Ejecutable de escritorio con logo:

```text
/home/daniel/hockey_espana/manager/dist/HockeyManager
```

```bash
# Abrir el juego
xdg-open /home/daniel/hockey_espana/juego_hockey/index.html

# Regenerar datos, juego y Excel
cd /home/daniel/hockey_espana/tools
python3 build_attributes_v2.py
python3 generate_game.py
python3 build_excel_attributes.py
```

## Qué incluye

- **29 equipos**: 12 DHA, 16 DHB y 1 Primera Andaluza.
- **976 perfiles**: 509 jugadores y 467 invitados.
- **Posiciones**: 175 oficiales y 801 estimadas; 75 porteros.
- **37 atributos** por jugador: técnica, 3D y set pieces, táctica, física, mental y portero.
- **5 overalls posicionales**: portero, central, lateral, medio y delantero.
- **Especialistas de set pieces**: inyector, stopper, drag flicker, desviador, primer runner, portero de PC, tirador de stroke, portero de stroke, aéreo y faltas.
- **Editor** para corregir posición y atributos en el navegador.
- **Trazabilidad**: la ficha muestra la fuente de la posición, su URL y la fecha cuando está disponible.
- **Simulador** con formato real DHA/DHB, Final Four, playout, ascensos y descensos.
- **Excel** con atributos, especialistas, diccionario y cobertura.
- **Documentación** completa para continuar el proyecto.

## Archivos principales

| Archivo | Descripción |
|---|---|
| `juego_hockey/index.html` | Juego completo y autocontenido. |
| `juego_hockey/README.md` | Manual resumido del juego. |
| `equipos_hockey_hierba_espana_masculino_2026_27_con_atributos.xlsx` | Excel ampliado con atributos. |
| `jugadores_atributos_2026_27.csv` | CSV completo de jugadores y atributos. |
| `equipos_hockey_hierba_espana_masculino_2026_27_con_posiciones.xlsx` | Excel base con posiciones. |
| `jugadores_posiciones_2026_27.csv` | CSV base de posiciones. |
| `informe_sistema_ligas_DHA_DHB_2026_27.md` / `.pdf` | Informe del sistema de ligas. |
| `informe_posiciones_DHA_DHB_2026_27.md` / `.pdf` | Informe de posiciones. |
| `tools/` | Scripts y datos reproducibles. |
| `docs/` | Documentación maestra. |
| `manager/` | Diseño y prototipo del juego de gestión/entrenador (solo texto). |

## Manager (juego de gestión)

El proyecto incluye un juego de entrenador/gestión, solo texto, inspirado en Football Manager. El juego ya es jugable con **DHA y DHB** desde el inicio y añade **seis ligas internacionales** (Países Bajos, Bélgica, Alemania, Inglaterra, Argentina e India), con partidos en directo, charla de vestuario, IA reactiva, entrenamiento semanal, staff, finanzas, mercado, contratos, multi-temporada, DHB de dos fases, agentes libres, Copa del Rey, cantera, prensa, junta dinámica, logística, clasificación, Final Four, playout y guardado/carga. La **beta avanzada** añade fotos reales de jugadores, escudos oficiales de iSquad, noticias generadas, un editor de once visual, calendario y amistosos, prensa con medios, marcas reales de equipación, editor de fichas y un menú global para guardar, cargar, volver al menú principal y ajustar opciones.

- [`manager/README.md`](manager/README.md) — índice y cómo ejecutar el juego.
- [`manager/docs/00_VISION_Y_ARQUITECTURA.md`](manager/docs/00_VISION_Y_ARQUITECTURA.md) — arquitectura.
- [`manager/docs/01_MOTOR_PARTIDO.md`](manager/docs/01_MOTOR_PARTIDO.md) — motor de partido.
- [`manager/docs/02_LOGISTICA.md`](manager/docs/02_LOGISTICA.md) — viajes, costes y fatiga.
- [`manager/docs/03_CLUBES_Y_ESTADIOS.md`](manager/docs/03_CLUBES_Y_ESTADIOS.md) — los 29 clubes.
- [`manager/docs/04_UI_TEXTO.md`](manager/docs/04_UI_TEXTO.md) — interfaz de texto.
- [`manager/docs/05_ROADMAP_Y_MVP.md`](manager/docs/05_ROADMAP_Y_MVP.md) — roadmap.
- [`manager/docs/06_MODELO_DATOS.md`](manager/docs/06_MODELO_DATOS.md) — modelo de datos y guardado.
- [`manager/docs/07_FASE1_IMPLEMENTACION.md`](manager/docs/07_FASE1_IMPLEMENTACION.md) — implementación, comandos, motor y pruebas de la Fase 1.
- [`manager/docs/08_MODO_DIRECTO_Y_GESTION.md`](manager/docs/08_MODO_DIRECTO_Y_GESTION.md) — partido en directo y recompensa a la gestión.
- [`manager/docs/09_ENTRENAMIENTO_SEMANAL.md`](manager/docs/09_ENTRENAMIENTO_SEMANAL.md) — entrenamiento semanal y plan automático.
- [`manager/docs/10_STAFF_Y_FINANZAS.md`](manager/docs/10_STAFF_Y_FINANZAS.md) — staff, junta y finanzas.
- [`manager/docs/11_FASE3_MERCADO_Y_MULTITEMPORADA.md`](manager/docs/11_FASE3_MERCADO_Y_MULTITEMPORADA.md) — mercado, contratos y multi-temporada.
- [`manager/docs/12_FASE4_COPA_CANTERA_PRENSA_JUNTA.md`](manager/docs/12_FASE4_COPA_CANTERA_PRENSA_JUNTA.md) — Copa, cantera, prensa y junta.
- [`manager/docs/13_FASE5A_DHB_REAL_Y_AGENTES_LIBRES.md`](manager/docs/13_FASE5A_DHB_REAL_Y_AGENTES_LIBRES.md) — DHB de dos fases y agentes libres.
- [`manager/docs/15_WEB_ALPHA.md`](manager/docs/15_WEB_ALPHA.md) — alpha web.
- [`manager/docs/45_BETA_AVANZADA.md`](manager/docs/45_BETA_AVANZADA.md) — beta avanzada: calendario, amistosos, prensa, marcas, editor y auditoría.
- [`manager/docs/46_AUDITORIA_CLUBES.md`](manager/docs/46_AUDITORIA_CLUBES.md) — ubicaciones y fuentes de clubes.
- [`manager/docs/16_DISENO_UI.md`](manager/docs/16_DISENO_UI.md) — diseño visual, paleta, escudos y usabilidad.
- [`manager/docs/17_CANTERA_Y_CATEGORIAS.md`](manager/docs/17_CANTERA_Y_CATEGORIAS.md) — cantera Sub-16/Sub-18/Sub-21 y nombres por comunidad.
- [`manager/docs/18_SIMULACION_DIARIA_Y_SCOUTING.md`](manager/docs/18_SIMULACION_DIARIA_Y_SCOUTING.md) — calendario diario, eventos, vestuario, mercado, equipos e histórico.
- [`manager/docs/19_STAFF_Y_CUERPO_TECNICO.md`](manager/docs/19_STAFF_Y_CUERPO_TECNICO.md) — cuerpo técnico real de iSquad.
- [`manager/docs/20_EJECUTABLE.md`](manager/docs/20_EJECUTABLE.md) — ejecutable de escritorio.
- [`manager/docs/21_COPA_Y_EHL_CALENDARIO.md`](manager/docs/21_COPA_Y_EHL_CALENDARIO.md) — Copa y EHL en el calendario diario.
- [`manager/docs/22_VALORACIONES_POR_CATEGORIA.md`](manager/docs/22_VALORACIONES_POR_CATEGORIA.md) — estrellas relativas por categoría.
- [`manager/docs/23_EVENTOS_VESTUARIO_Y_PRENSA.md`](manager/docs/23_EVENTOS_VESTUARIO_Y_PRENSA.md) —relación con jugadores, eventos y prensa.

```bash
cd manager && python3 run.py
```

Alpha web local:

```bash
cd manager && python3 run_web.py
```

Abre `http://127.0.0.1:5000`.

Simulación automática de una temporada:

```bash
cd manager && python3 run.py --auto --club cd-terrassa --seed 7
```

## Documentación

- [`docs/00_PROYECTO.md`](docs/00_PROYECTO.md) — visión general, estado y arquitectura.
- [`docs/01_SISTEMA_LIGAS.md`](docs/01_SISTEMA_LIGAS.md) — formato DHA/DHB, ascensos y descensos.
- [`docs/02_MODELO_ATRIBUTOS.md`](docs/02_MODELO_ATRIBUTOS.md) — 37 atributos, pesos y especialistas.
- [`docs/03_COMO_SE_JUEGA_HOCKEY.md`](docs/03_COMO_SE_JUEGA_HOCKEY.md) — reglas, fases y set pieces.
- [`docs/04_DATOS_Y_FUENTES.md`](docs/04_DATOS_Y_FUENTES.md) — fuentes, cobertura y calidad.
- [`docs/05_ROADMAP.md`](docs/05_ROADMAP.md) — próximos pasos.
- [`docs/06_CHANGELOG.md`](docs/06_CHANGELOG.md) — historial de cambios.
- [`docs/07_GUIA_JUEGO.md`](docs/07_GUIA_JUEGO.md) — manual de uso del HTML.

Versiones PDF: [`docs/00_PROYECTO.pdf`](docs/00_PROYECTO.pdf), [`docs/02_MODELO_ATRIBUTOS.pdf`](docs/02_MODELO_ATRIBUTOS.pdf), [`docs/03_COMO_SE_JUEGA_HOCKEY.pdf`](docs/03_COMO_SE_JUEGA_HOCKEY.pdf), [`docs/07_GUIA_JUEGO.pdf`](docs/07_GUIA_JUEGO.pdf).

## Pipeline

```
iSquad / RFEH / clubes / prensa
              │
              ▼
tools/todos_manifest_positions.csv
              │
              ▼
tools/build_attributes_v2.py
              │
              ▼
tools/player_attributes_v2.csv
        ┌─────┴─────┐
        ▼           ▼
generate_game.py  build_excel_attributes.py
        │           │
        ▼           ▼
index.html      Excel + CSV
```

## Estado y limitaciones

- Los **37 atributos** y el **82,1 % de las posiciones** son estimaciones del modelo, no datos oficiales.
- 399 subposiciones Central/Lateral son estimadas.
- San Fernando 1ª Andaluza no tiene portero identificado.
- No hay datos oficiales de asistencias, PC, strokes, paradas, minutos o lesiones.
- El simulador es lúdico y educativo; no predice resultados reales.
- Fecha de corte: octubre de 2026.

## Aviso

Proyecto personal/educativo. No es una evaluación profesional ni una fuente oficial de datos. Las imágenes y datos pertenecen a sus fuentes originales; fotos y escudos se han obtenido de iSquad.
