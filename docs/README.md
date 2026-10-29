# Documentación del proyecto

Índice de documentos. Leer en este orden si es la primera vez:

1. [`00_PROYECTO.md`](00_PROYECTO.md) — qué es, estado, entregables y arquitectura.
2. [`02_MODELO_ATRIBUTOS.md`](02_MODELO_ATRIBUTOS.md) — cómo se valora a cada jugador.
3. [`04_DATOS_Y_FUENTES.md`](04_DATOS_Y_FUENTES.md) — de dónde salen los datos.
4. [`01_SISTEMA_LIGAS.md`](01_SISTEMA_LIGAS.md) — formato DHA/DHB.
5. [`03_COMO_SE_JUEGA_HOCKEY.md`](03_COMO_SE_JUEGA_HOCKEY.md) — reglas y set pieces.
6. [`07_GUIA_JUEGO.md`](07_GUIA_JUEGO.md) — cómo usar el HTML.
7. [`05_ROADMAP.md`](05_ROADMAP.md) — próximos pasos.
8. [`06_CHANGELOG.md`](06_CHANGELOG.md) — historial.

## Documentos

| Documento | Para qué sirve |
|---|---|
| `00_PROYECTO.md` | Visión general y mapa del proyecto. |
| `01_SISTEMA_LIGAS.md` | DHA, DHB, Final Four, playout, ascensos y clubes vinculados. |
| `02_MODELO_ATRIBUTOS.md` | 37 atributos, pesos, fórmulas, arquetipos y especialistas. |
| `03_COMO_SE_JUEGA_HOCKEY.md` | Reglas, posiciones, fases, PC, stroke, portero y táctica. |
| `04_DATOS_Y_FUENTES.md` | Fuentes, cobertura, archivos y calidad del dato. |
| `05_ROADMAP.md` | Prioridades y backlog. |
| `06_CHANGELOG.md` | Cambios por fecha. |
| `07_GUIA_JUEGO.md` | Manual de uso del juego y del editor. |

## Versiones PDF

- [`00_PROYECTO.pdf`](00_PROYECTO.pdf)
- [`02_MODELO_ATRIBUTOS.pdf`](02_MODELO_ATRIBUTOS.pdf)
- [`03_COMO_SE_JUEGA_HOCKEY.pdf`](03_COMO_SE_JUEGA_HOCKEY.pdf)
- [`07_GUIA_JUEGO.pdf`](07_GUIA_JUEGO.pdf)

## Manager (juego de gestión)

- [`../manager/README.md`](../manager/README.md) — índice del proyecto Manager.
- [`../manager/docs/00_VISION_Y_ARQUITECTURA.md`](../manager/docs/00_VISION_Y_ARQUITECTURA.md)
- [`../manager/docs/01_MOTOR_PARTIDO.md`](../manager/docs/01_MOTOR_PARTIDO.md)
- [`../manager/docs/02_LOGISTICA.md`](../manager/docs/02_LOGISTICA.md)
- [`../manager/docs/03_CLUBES_Y_ESTADIOS.md`](../manager/docs/03_CLUBES_Y_ESTADIOS.md)
- [`../manager/docs/04_UI_TEXTO.md`](../manager/docs/04_UI_TEXTO.md)
- [`../manager/docs/05_ROADMAP_Y_MVP.md`](../manager/docs/05_ROADMAP_Y_MVP.md)
- [`../manager/docs/06_MODELO_DATOS.md`](../manager/docs/06_MODELO_DATOS.md)
- [`../manager/docs/15_WEB_ALPHA.md`](../manager/docs/15_WEB_ALPHA.md)
- [`../manager/docs/16_DISENO_UI.md`](../manager/docs/16_DISENO_UI.md)
- [`../manager/docs/17_CANTERA_Y_CATEGORIAS.md`](../manager/docs/17_CANTERA_Y_CATEGORIAS.md)
- [`../manager/docs/18_SIMULACION_DIARIA_Y_SCOUTING.md`](../manager/docs/18_SIMULACION_DIARIA_Y_SCOUTING.md)
- [`../manager/docs/19_STAFF_Y_CUERPO_TECNICO.md`](../manager/docs/19_STAFF_Y_CUERPO_TECNICO.md)
- [`../manager/docs/20_EJECUTABLE.md`](../manager/docs/20_EJECUTABLE.md)
- [`../manager/docs/21_COPA_Y_EHL_CALENDARIO.md`](../manager/docs/21_COPA_Y_EHL_CALENDARIO.md)
- [`../manager/docs/22_VALORACIONES_POR_CATEGORIA.md`](../manager/docs/22_VALORACIONES_POR_CATEGORIA.md)
- [`../manager/docs/23_EVENTOS_VESTUARIO_Y_PRENSA.md`](../manager/docs/23_EVENTOS_VESTUARIO_Y_PRENSA.md)
- [`../manager/docs/24_LIGAS_INTERNACIONALES.md`](../manager/docs/24_LIGAS_INTERNACIONALES.md)
- [`../manager/docs/25_DATOS_REALES_NED_BEL.md`](../manager/docs/25_DATOS_REALES_NED_BEL.md)
- [`../manager/docs/26_DATOS_REALES_ALEMANIA_INDIA.md`](../manager/docs/26_DATOS_REALES_ALEMANIA_INDIA.md)

## Informes complementarios

- `../informe_sistema_ligas_DHA_DHB_2026_27.md`
- `../informe_posiciones_DHA_DHB_2026_27.md`

## Convenciones

- Los datos de competición tienen fecha de corte: octubre de 2026.
- Las posiciones oficiales se citan con fuente; las estimadas se marcan como tales.
- Los atributos son estimaciones del modelo.
- Los scripts de `../tools/` son la fuente de verdad para regenerar el HTML y el Excel.
- No editar `juego_hockey/index.html` a mano.

## Para continuar

1. Leer `00_PROYECTO.md`, `02_MODELO_ATRIBUTOS.md` y `04_DATOS_Y_FUENTES.md`.
2. Ejecutar el pipeline en `../tools/`.
3. Revisar los datos y el juego.
4. Actualizar `06_CHANGELOG.md`.
