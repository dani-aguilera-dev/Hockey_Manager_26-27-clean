# Hockey Manager España 2026-27

Diseño y prototipo de un juego de **entrenador y gestión de club** de hockey hierba, solo texto, inspirado en la arquitectura de Football Manager y adaptado a la DHA, la DHB, la Primera Andaluza y seis ligas internacionales.

## Estado

- **Diseño:** completo en `docs/`.
- **Datos:** 29 clubes españoles y 70 internacionales, plantillas reales en las seis ligas internacionales y 37 atributos.
- **Motor:** DHA y DHB jugables, partidos en directo, mercado, staff, entrenamiento, cantera, Copa, EHL, multi-temporada y guardado/carga.
- **Web React:** Flask como backend/API + SPA React en `/app`, con fotos de jugadores, escudos oficiales de iSquad, noticias inmersivas y diseño responsive.
- **Beta avanzada:** calendario de amistosos, prensa con periodistas y medios, marcas reales de equipación (Osaka, Ritual, Gryphon, TK, Grays, STX…), editor de fichas, auditoría de plantillas y simulación 3D del partido con esqueleto, IK, sticks, respuesta de materiales, colisiones de cuerpo/stick-cuerpo, biomecánica procedural, tejido estilizado, revisión de vídeo, junta y visión de club, cesiones, data hub, afiliados y mentoring, historial completo, ojeo con asignaciones, reunión de equipo, arbitraje discrecional, protestas, tiempo añadido, protesta en directo, responsabilidades del staff, centro financiero, análisis de partido y conexión a MatchEngine.
- **Tests:** 238 superados.

## Inicio rápido

La interfaz principal es web y React. El ejecutable de escritorio queda como
compatibilidad histórica.

Web:

```bash
cd /home/daniel/hockey_espana/manager
./build_web.sh          # compila la SPA React
python3 run_web.py      # Flask + API
```

Abre `http://127.0.0.1:5000/app`.

Juego de terminal:

```bash
cd /home/daniel/hockey_espana/manager
python3 run.py
```

Web React:

```bash
cd /home/daniel/hockey_espana/manager
./build_web.sh
python3 run_web.py
```

Abre `http://127.0.0.1:5000/app`. La raíz `/` redirige a la interfaz React.
La arquitectura de la migración está en `docs/27_INTERFAZ_REACT.md`.

Modo interactivo con una base de datos alternativa:

```bash
python3 run.py --db /ruta/mi_partida.db
```

Simular una temporada completa sin interacción:

```bash
python3 run.py --auto --club cd-terrassa --seed 7
```

Pruebas:

```bash
python3 -m pytest src/tests -q
```

El juego incluye:

- selección de club y dossier;
- dashboard;
- plantilla y ficha de jugador;
- táctica, once automático y once manual;
- calendario DHA de 22 jornadas y 132 partidos;
- motor de partido por fases con comentario de texto;
- **modo directo**: cuarto a cuarto o minuto a minuto, con estadísticas, jugadores, cambios y táctica en vivo;
- **charla de vestuario** al descanso, con opción de delegar en el segundo entrenador;
- **IA reactiva** que ajusta táctica y cambios según el marcador, la fatiga y tu planteamiento;
- **sistema de gestión**: moral, cohesión, fatiga, confianza, encaje posicional y rating del mánager que otorgan un bonus de hasta ±7 puntos;
- **entrenamiento semanal**: plan automático del segundo entrenador, editor de sesiones, recuperación y preparación del rival;
- **staff y finanzas**: siete roles de staff, junta directiva, salarios, patrocinio, taquilla, viajes y caja;
- **mercado y contratos**: ventanas de verano/invierno, ofertas, renovaciones, contratación de staff y mercado IA;
- **multi-temporada**: ascensos, descensos, DHA/DHB, contratos, canteranos y nueva temporada;
- **Copa del Rey**, cantera con categorías Sub-16/Sub-18/Sub-21, rueda de prensa y junta directiva dinámica;
- **DHA y DHB jugables desde el inicio**, DHB real de dos fases, **agentes libres** procedentes de las 8 ligas regionales, **Copa del Rey de 8 equipos DHA** y **EHL**;
- **seis ligas internacionales jugables**: Países Bajos, Bélgica, Alemania, Inglaterra, Argentina e India, con calendario y nivel propios;
- logística con bus/tren/avión, coste y fatiga;
- clasificación, Final Four y playout;
- guardado/carga SQLite y gestor de partidas guardadas (cargar, renombrar, eliminar);
- **web React** con dashboard, calendario diario, eventos, vestuario, noticias, escudos, fotos, táctica visual, mercado, perfiles de equipo, partido en directo y menú global de juego con guardado/carga, gestor de partidas, selector por país/división y opciones. La API JSON vive en `web/api.py` y la SPA en `web/frontend/`.
- **relaciones avanzadas**: conversaciones con cualquier jugador o empleado, temas según edad, rol, rendimiento, contrato, lesiones y mercado; noticias conectadas al 100% con la partida, rumores, premios individuales y fichas relacionadas. Ver `docs/28_RELACIONES_Y_NOTICIAS.md`.
- **táctica de hockey**: zona baja/media/alta, individual total y mixta, sistemas de ataque, salida, activadores de presión y roles manuales de penalty corner y penalty stroke. Ver `docs/29_TACTICA_HOCKEY.md`.
- **economía y mercado global**: marca, patrocinadores, taquilla, merchandising, campañas, staff comercial, mercado de todas las ligas, agentes libres, empleados ficticios, lista de traspaso, ofertas durante la simulación y negociación contextual. Ver `docs/30_ECONOMIA_MERCADO.md`.
- **ojeadores de mercado**: recomendaciones adaptadas a presupuesto, nivel del equipo, necesidades, edad y rendimiento, con enfoques de búsqueda. Ver `docs/31_OJEADORES.md`.
- **reglamento FIH aplicado**: cuartos de 15 minutos, tarjetas verde/amarilla/roja, suspensiones temporales reales, parte de tarjetas y lesiones. Ver `docs/32_REGLAMENTO_FIH.md`.
- **eventos con decisiones**: decisiones pendientes en el dashboard, consecuencias y cadenas de seguimiento. Centro de enfermería con lesiones, sanciones, carga y historial.
- **negociaciones por rondas**: contraofertas en fichajes, ventas y renovaciones, con paciencia, historial y persistencia. Ver `docs/33_NEGOCIACIONES.md`.
- **interfaz revisada**: foco visible, modal accesible, contraste de texto terciario corregido y pantalla de decisiones. Ver `docs/34_UI_Y_ACCESIBILIDAD.md`.
- **diálogos por turnos**: apertura contextual, memoria, temas recientes, segunda decisión, transcripción y promesas comprobadas. Ver `docs/35_DIALOGOS.md`.
- **divisiones autonómicas como agentes libres**: 1.460 jugadores de 59 equipos, con equipo de procedencia, posición estimada y ratings recalibrados por división, clasificación real e historial DHB. Ver `docs/36_DATOS_DIVISIONES_Y_RATINGS.md`.
- **ligas regionales jugables**: 1N, 1A, 1M, 1G, 1C, 1V, Superlliga Catalana y Primera Catalana, con fase regular, equipos B sin jugadores repetidos y eliminatorias de ascenso a DHB. Ver `docs/37_LIGAS_REGIONALES.md` y `docs/38_AUDITORIA_EQUIPOS_Y_PLANTILLAS.md`.
- **beta avanzada**: calendario y amistosos, prensa con periodistas/medios y confianza mediática, marcas reales de equipación, editor de jugadores y auditoría de clubes. Ver `docs/45_BETA_AVANZADA.md` y `docs/46_AUDITORIA_CLUBES.md`. Ver también `docs/48_MATRIZ_ACEPTACION_FM24_FIH.md`.

Pendiente:

- revisar permisos de los escudos oficiales descargados de iSquad;
- guardado en mitad de un partido en directo;
- EHL interactiva (ahora se simula);
- descenso DHB → 1ª Andaluza y fases de ascenso regionales interactivas;
- auditoría formal de accesibilidad con lector de pantalla.
- ajustar la convocatoria de la interfaz a 5 suplentes;
- completar rehabilitación, recaídas y llamada a cantera con menos de 11 disponibles;
- ampliar el catálogo de eventos y sus cadenas.

## Estructura

```
manager/
  README.md
  docs/
    00_VISION_Y_ARQUITECTURA.md
    01_MOTOR_PARTIDO.md
    02_LOGISTICA.md
    03_CLUBES_Y_ESTADIOS.md
    04_UI_TEXTO.md
    05_ROADMAP_Y_MVP.md
  data/
    clubs.json
    cities.json
    competitions.json
    tactical_roles.json
    staff_roles.json
    events.json
  schema/
    schema.sql
  src/
    main.py
    ui.py
    models.py
    data_loader.py
    calendar.py
    match_engine.py
    logistics.py
    season.py
    persistence.py
    tests/
    prototype.py        # prototipo legado, se conserva como referencia
  saves/
```

## Documentación

1. [`docs/00_VISION_Y_ARQUITECTURA.md`](docs/00_VISION_Y_ARQUITECTURA.md) — visión, referencia de Football Manager, capas y módulos.
2. [`docs/01_MOTOR_PARTIDO.md`](docs/01_MOTOR_PARTIDO.md) — motor de texto, fases, atributos, set pieces y calibración.
3. [`docs/02_LOGISTICA.md`](docs/02_LOGISTICA.md) — viajes, costes, fatiga, clima y superficie.
4. [`docs/03_CLUBES_Y_ESTADIOS.md`](docs/03_CLUBES_Y_ESTADIOS.md) — los 29 clubes, historia, estadio y logística.
5. [`docs/04_UI_TEXTO.md`](docs/04_UI_TEXTO.md) — pantallas, comandos y flujo de interfaz.
6. [`docs/05_ROADMAP_Y_MVP.md`](docs/05_ROADMAP_Y_MVP.md) — fases, backlog y criterios de aceptación.
7. [`docs/06_MODELO_DATOS.md`](docs/06_MODELO_DATOS.md) — tablas, atributos, eventos y guardado.
8. [`docs/07_FASE1_IMPLEMENTACION.md`](docs/07_FASE1_IMPLEMENTACION.md) — implementación, comandos, motor, pruebas y limitaciones de la Fase 1.
9. [`docs/08_MODO_DIRECTO_Y_GESTION.md`](docs/08_MODO_DIRECTO_Y_GESTION.md) — partido en directo y recompensa a la buena gestión.
10. [`docs/09_ENTRENAMIENTO_SEMANAL.md`](docs/09_ENTRENAMIENTO_SEMANAL.md) — entrenamiento semanal, plan automático y preparación del rival.
11. [`docs/10_STAFF_Y_FINANZAS.md`](docs/10_STAFF_Y_FINANZAS.md) — staff, junta directiva, salarios y finanzas.
12. [`docs/11_FASE3_MERCADO_Y_MULTITEMPORADA.md`](docs/11_FASE3_MERCADO_Y_MULTITEMPORADA.md) — mercado, contratos, staff y multi-temporada.
13. [`docs/12_FASE4_COPA_CANTERA_PRENSA_JUNTA.md`](docs/12_FASE4_COPA_CANTERA_PRENSA_JUNTA.md) — Copa, cantera, prensa y junta.
14. [`docs/13_FASE5A_DHB_REAL_Y_AGENTES_LIBRES.md`](docs/13_FASE5A_DHB_REAL_Y_AGENTES_LIBRES.md) — DHB de dos fases y agentes libres.
15. [`docs/14_TEST_ESTRESS_10_TEMPORADAS.md`](docs/14_TEST_ESTRESS_10_TEMPORADAS.md) — test de 10 temporadas con mercado y retiros.
16. [`docs/15_WEB_ALPHA.md`](docs/15_WEB_ALPHA.md) — alpha web local con Flask.
17. [`docs/16_DISENO_UI.md`](docs/16_DISENO_UI.md) — investigación, paleta, usabilidad, escudos y noticias.
18. [`docs/17_CANTERA_Y_CATEGORIAS.md`](docs/17_CANTERA_Y_CATEGORIAS.md) — categorías Sub-16/Sub-18/Sub-21 y nombres por comunidad.
19. [`docs/18_SIMULACION_DIARIA_Y_SCOUTING.md`](docs/18_SIMULACION_DIARIA_Y_SCOUTING.md) — calendario diario, eventos, vestuario, scouting y perfiles.
20. [`docs/19_STAFF_Y_CUERPO_TECNICO.md`](docs/19_STAFF_Y_CUERPO_TECNICO.md) — staff real de iSquad, entrenador y compatibilidad.
21. [`docs/20_EJECUTABLE.md`](docs/20_EJECUTABLE.md) — ejecutable de escritorio y logo.
22. [`docs/21_COPA_Y_EHL_CALENDARIO.md`](docs/21_COPA_Y_EHL_CALENDARIO.md) — Copa y EHL dentro del calendario diario.
23. [`docs/22_VALORACIONES_POR_CATEGORIA.md`](docs/22_VALORACIONES_POR_CATEGORIA.md) — estrellas relativas por categoría.
24. [`docs/23_EVENTOS_VESTUARIO_Y_PRENSA.md`](docs/23_EVENTOS_VESTUARIO_Y_PRENSA.md) — relación con jugadores, eventos y ruedas de prensa.
25. [`docs/24_LIGAS_INTERNACIONALES.md`](docs/24_LIGAS_INTERNACIONALES.md) — seis ligas internacionales y estrategia de datos.
26. [`docs/25_DATOS_REALES_NED_BEL.md`](docs/25_DATOS_REALES_NED_BEL.md) — plantillas, fotos y escudos reales de Países Bajos y Bélgica.
27. [`docs/26_DATOS_REALES_ALEMANIA_INDIA.md`](docs/26_DATOS_REALES_ALEMANIA_INDIA.md) — plantillas, fotos y escudos reales de Alemania e India.
28. [`docs/32_REGLAMENTO_FIH.md`](docs/32_REGLAMENTO_FIH.md) — reglamento FIH 2026/2027 aplicado a tarjetas, suspensiones, tiempos y lesiones.
29. [`docs/33_NEGOCIACIONES.md`](docs/33_NEGOCIACIONES.md) — negociaciones con contraofertas, rondas y persistencia.
30. [`docs/34_UI_Y_ACCESIBILIDAD.md`](docs/34_UI_Y_ACCESIBILIDAD.md) — paleta, contraste, foco, botones y revisión de usabilidad.
31. [`docs/35_DIALOGOS.md`](docs/35_DIALOGOS.md) — diálogos por turnos, memoria, repetición y promesas.
32. [`docs/36_DATOS_DIVISIONES_Y_RATINGS.md`](docs/36_DATOS_DIVISIONES_Y_RATINGS.md) — divisiones autonómicas, agentes libres y recalibración de ratings.
33. [`docs/37_LIGAS_REGIONALES.md`](docs/37_LIGAS_REGIONALES.md) — ligas regionales jugables y fase de ascenso a DHB.
34. [`docs/38_AUDITORIA_EQUIPOS_Y_PLANTILLAS.md`](docs/38_AUDITORIA_EQUIPOS_Y_PLANTILLAS.md) — auditoría liga a liga, equipos B, fuentes y duplicados.
35. [`docs/39_GESTOR_PARTIDAS.md`](docs/39_GESTOR_PARTIDAS.md) — gestor de partidas guardadas: cargar, renombrar, eliminar.
36. [`docs/40_NIVELES_LIGAS_Y_MEDIAS.md`](docs/40_NIVELES_LIGAS_Y_MEDIAS.md) — escalera DHA/DHB/1A, fronteras y medias internacionales.
37. [`docs/41_POSICIONES_Y_LIGAS_REALES.md`](docs/41_POSICIONES_Y_LIGAS_REALES.md) — posiciones y cierre real de las seis ligas internacionales.
38. [`docs/42_SELECTOR_PAISES_Y_DIVISIONES.md`](docs/42_SELECTOR_PAISES_Y_DIVISIONES.md) — selector de nueva partida por país y división, con logos de liga.
21. [`docs/20_EJECUTABLE.md`](docs/20_EJECUTABLE.md) — ejecutable de escritorio, logo y guardado local.

## Datos

- `data/clubs.json`: 29 clubes con historia, estadio, instalaciones, finanzas, junta y logística.
- `data/cities.json`: coordenadas, aeropuertos y tren.
- `data/competitions.json`: formatos DHA/DHB/1ª.
- `data/tactical_roles.json`: formaciones, roles e instrucciones.
- `data/youth_names.json`: nombres y apellidos por comunidad autónoma.
- `data/staff_roles.json`: 13 roles de cuerpo técnico.
- `data/events.json`: plantillas de eventos de partido y mundo.
- `schema/schema.sql`: 41 tablas SQLite.
- `tools/lower_divisions_players.csv`: plantillas de las 8 ligas regionales, incluidos los equipos B; se usan como agentes libres en DHA/DHB y como equipos en partidas regionales.
- `../tools/fetch_isquad_crests.py`: descarga y prepara los escudos oficiales de iSquad.
- `../tools/generate_crests.py`: genera escudos SVG de respaldo.
- `../tools/fetch_isquad_staff.py`: descarga el cuerpo técnico real de iSquad.

## Fuentes y calidad

- Plantillas, goles y atributos: RFEH/iSquad y modelo propio.
- Posiciones: 145 con fuente específica y 2.273 estimadas (iSquad/FHCV/FCH no publican posición individual en todas las plantillas).
- Historias y estadios: webs oficiales, Wikipedia, iSquad y prensa local.
- Capacidades y presupuestos: estimaciones de diseño, marcadas como `estimada` o `modelo`.

## Próximo paso

1. Probar la alpha web y pulir UX.
2. Revisar permisos y calidad de los escudos oficiales.
3. EHL interactiva, descenso DHB → 1ª Andaluza y fases de ascenso regionales interactivas.
4. Auditoría de accesibilidad y pruebas de usuario.
5. Publicación en GitHub privado.

## Aviso

Proyecto personal/educativo. No es una fuente oficial de datos ni una evaluación profesional.
