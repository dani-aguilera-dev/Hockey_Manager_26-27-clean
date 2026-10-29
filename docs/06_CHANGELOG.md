# Changelog

## 2026-10-22 — Plantillas reales de Alemania e India

### Añadido

- 318 jugadores reales de la 1. Feldhockey Bundesliga con foto y escudo.
- 158 jugadores reales de la Hockey India League con posición, foto y escudo.
- Actualización de los clubes alemanes 2026-27 (Berliner HC y DSD Düsseldorf).
- Actualización de las franquicias indias 2026-27 (HIL GC).
- Documento `manager/docs/26_DATOS_REALES_ALEMANIA_INDIA.md`.

### Limitaciones

- Alemania no publica demarcaciones: se estiman.
- Inglaterra y Argentina siguen con plantillas generadas.

Resultado: 80 tests superados.

---

## 2026-10-22 — Plantillas reales de Países Bajos y Bélgica

### Añadido

- 241 jugadores reales de la Belgian Hockey League con ficha, dorsal, fecha de nacimiento, nacionalidad, posición y foto.
- 233 jugadores reales neerlandeses con foto, más 13 altas públicas de Schaerweijde sin foto.
- 24 escudos oficiales de Países Bajos y Bélgica.
- Carga de datos reales desde `manager/data/international_real.json`.
- Play-offs genéricos top-4 para las ligas internacionales.
- Documento `manager/docs/25_DATOS_REALES_NED_BEL.md`.

### Limitaciones

- HDM usa la selección publicada 2025-26.
- Schaerweijde no publica plantilla completa ni fotos de todos sus jugadores.
- Las valoraciones siguen siendo estimaciones del modelo.
- Escudos y fotos son material de sus clubes/autores; su distribución pública requiere permiso.

Resultado: 80 tests superados.

---

## 2026-10-22 — Vida del club y ligas internacionales

### Añadido

- Relación jugador-entrenador (0-100) visible en ficha, plantilla y vestuario.
- Eventos de lesión, enfermedad, familia, vestuario, prensa e incidentes fuera del club.
- Citaciones judiciales con baja, motivo específico y conversación disciplinaria.
- Rueda de prensa de cinco bloques con declaraciones del entrenador rival.
- Seis ligas internacionales jugables:
  - Países Bajos (`NED`);
  - Bélgica (`BEL`);
  - Alemania (`GER`);
  - Inglaterra (`ENG`);
  - Argentina (`ARG`);
  - India (`IND`).
- 68 clubes internacionales con ciudades, estadios y plantillas generadas.
- Calendario, clasificación, mercado, viajes, fin de temporada y multi-temporada para las nuevas ligas.
- Escudos SVG de respaldo por iniciales.
- Documentos `manager/docs/23_EVENTOS_VESTUARIO_Y_PRENSA.md` y `manager/docs/24_LIGAS_INTERNACIONALES.md`.

### Pruebas

Resultado: 79 tests superados.

---

## 2026-10-22 — Estrellas relativas por categoría

### Añadido

- Modelo de valoración tipo Football Manager:
  - overall y potencial absolutos;
  - estrellas relativas a la categoría.
- Perfiles de nivel: DHA 72, DHB 62, 1ª Andaluza 48 y EHL 86.
- `PlayerState.league` y actualización automática en ascensos, descensos, fichajes y agentes libres.
- Estrellas contextuales en plantilla, ficha, mercado, perfil de equipo, once probable e informe de ojeador.
- Potencial relativo y etiquetas de rol: estrella, muy bueno, titular, rotación o suplente.
- Compatibilidad con partidas antiguas mediante retrocarga de categoría.
- Documento `manager/docs/22_VALORACIONES_POR_CATEGORIA.md`.

### Pruebas

```bash
cd manager
python3 -m pytest src/tests -q
```

Resultado: 66 tests superados.

---

## 2026-10-21 — Copa y EHL dentro del calendario diario

### Añadido

- La Copa del Rey entra en el calendario diario:
  - cuartos el 2/12/2026;
  - semifinal el 3/12/2026;
  - final y tercer puesto el 4/12/2026.
- `next_user_fixture` incluye partidos de Copa y “hasta el próximo partido” se detiene en ellos.
- Previa, dashboard y ficha de Copa muestran la competición y la fecha.
- Simulación rápida de Copa integrada y actualización del cuadro.
- La EHL se activa después de la final de Copa con fechas 7, 8 y 9 de enero de 2027; clasifican los 2 primeros de DHA tras la primera vuelta, el campeón de Copa (o el siguiente clasificado si ya estaba entre los dos primeros) y 5 clubes europeos invitados.
- La EHL se resuelve automáticamente al avanzar el calendario y genera noticias.
- Página **Europa / EHL** con participantes, cruces y resultados.
- Documento `manager/docs/21_COPA_Y_EHL_CALENDARIO.md`.

### Limitaciones

- El modo directo de Copa queda pendiente; la interfaz oculta el botón.
- La EHL se simula automáticamente, todavía no se juega en directo.

### Pruebas

```bash
cd manager
python3 -m pytest src/tests -q
```

Resultado: 64 tests superados.

---

## 2026-10-21 — Cuerpo técnico real de iSquad

### Añadido

- Extracción automática del staff visible en las fichas de equipo de iSquad para los 28 clubes activos y la 1ª Andaluza.
- Mínimo un **entrenador** por equipo, incluidos todos los clubes de DHB que antes estaban vacíos.
- Roles adicionales cuando aparecen en la web: preparador físico, fisioterapeuta, psicólogo, delegado, médico, analista, entrenador de porteros y staff adicional.
- **Perfil de equipo** con cuerpo técnico completo, entrenador y fuente.
- En el club que gestiona el usuario, el entrenador externo se oculta y aparece **Tú** como entrenador.
- Compatibilidad con partidas antiguas: se rellena el entrenador o el staff que falte.
- Script `tools/fetch_isquad_staff.py` y documento `manager/docs/19_STAFF_Y_CUERPO_TECNICO.md`.

### Pruebas

```bash
cd manager
python3 -m pytest src/tests -q
```

Resultado: 61 tests superados.

---

## 2026-10-21 — Fotos reales también en partidas antiguas

### Corregido

- Las partidas guardadas antes de añadir las fotos ya no muestran iniciales: al cargarlas se rellenan automáticamente las fotos locales de iSquad por id y, si hace falta, por equipo + nombre.
- La retrocarga cubre jugadores de todos los equipos y agentes libres.
- Se evita cargar datos de clubes en cada petición cuando la partida ya está completa.

### Pruebas

```bash
cd manager
python3 -m pytest src/tests -q
```

Resultado: 59 tests superados.

---

## 2026-10-21 — Simulación diaria, vestuario, scouting y perfiles

### Añadido

- **Calendario diario** desde el 1 de agosto: avanzar 1 día, hasta una fecha o hasta el próximo partido.
- La simulación **se detiene en el día del partido** y nunca lo juega automáticamente.
- **Eventos diarios**: entrenamientos, lesiones, mercado, noticias de liga, noticias de DHB/DHA, club y afición.
- **Diario del club** en dashboard y noticias.
- **Vestuario**: conversaciones con jugadores, respuestas con efectos en moral, forma y cohesión.
- **Mercado por fechas**: verano hasta el 30/09 e invierno del 1 al 31 de enero; el primer partido ya no lo cierra.
- **Mercado siempre consultable**: muestra jugadores de todos los clubes y agentes libres aunque esté cerrado.
- Filtro por club y estadísticas de temporada en las fichas de mercado.
- **Perfil de equipo** con historia, estadio, instalaciones, clasificación, once probable con fotos, banquillo, plantilla con caras, resultados y próximos partidos.
- **Histórico de jugadores** por temporada y club, conservado en traspasos y visible en la ficha.
- Enlaces a perfiles desde la clasificación, el dashboard y el mercado.
- Documento `manager/docs/18_SIMULACION_DIARIA_Y_SCOUTING.md`.

### Cambiado

- La fecha inicial de una partida es la pretemporada, no el primer partido.
- Tras jugar, el calendario avanza al día siguiente del partido.
- Tests ampliados a **58**.

### Pruebas

```bash
cd manager
python3 -m pytest src/tests -q
```

Resultado: 58 tests superados.

---

## 2026-10-21 — Menú de juego global y opciones

### Añadido

- **Menú de juego** accesible desde todas las pantallas:
  - continuar;
  - guardar partida con nombre editable;
  - cargar partida;
  - volver a la pantalla anterior;
  - menú principal;
  - nueva partida;
  - opciones;
  - salir al menú principal con guardado automático y confirmación opcional.
- **Menú principal** con partida en curso, guardado rápido, acceso a carga y partidas recientes.
- **Opciones**: tamaño de texto normal/grande, modo compacto y confirmación al salir.
- Nombres de guardado legibles: `Club · temporada · código corto`.
- Script `manager/web/static/app.js` para apertura, cierre, foco, Escape y confirmación del menú.
- Tests de menú, opciones y salida de partida.

### Pruebas

```bash
cd manager
python3 -m pytest src/tests -q
```

Resultado: 53 tests superados.

---

## 2026-10-21 — Escudos oficiales y cantera Sub-16/Sub-18/Sub-21

### Añadido

- **29/29 escudos oficiales de iSquad** para los clubes activos y la 1ª Andaluza:
  - descarga por `id_equipo` desde la cabecera de cada equipo;
  - recorte de fondo blanco a transparente;
  - PNG de 320 px con prioridad sobre el SVG estilizado de respaldo;
  - script reproducible `tools/fetch_isquad_crests.py`.
- **Cantera por categorías**: Sub-16 (14-15), Sub-18 (16-17) y Sub-21 (18-20).
- **Nombres y apellidos por comunidad autónoma**: pools para las 17 comunidades y respaldo común.
- Seis canteranos iniciales por club, dos por categoría, y tres incorporaciones anuales de 14-16 años.
- Crecimiento diferenciado por categoría y salida de la cantera a los 21 años.
- Vista de cantera agrupada por categoría con edades, potencial y acciones.
- Documento `manager/docs/17_CANTERA_Y_CATEGORIAS.md`.

### Corregido

- El nombre de un canterano andaluz ya no sale de un pool catalán: se selecciona según `TeamState.community`.

### Pruebas

```bash
cd manager
python3 -m pytest src/tests -q
```

Resultado: 52 tests superados.

---

## 2026-10-21 — Interfaz inmersiva, escudos y noticias

### Añadido

- **Escudos de club** para los 28 equipos activos (y 1ª Andaluza):
  - 29 SVG generados desde colores, iniciales y año de fundación;
  - soporte para sustituirlos por PNG oficiales sin tocar código;
  - visibles en dashboard, tabla, Copa, previa, directo, parte, mercado, nuevo juego y fin de temporada.
- **Noticias generadas** desde el estado del juego:
  - previa, resultado, liderato, mercado, enfermería, cantera, scouting, afición, junta y Copa;
  - ticker de última hora en el dashboard;
  - página `/news` con escudos y fotos.
- **Nuevo juego con fichas de club**: escudo, ciudad, estadio, exigencia y academia.
- **Marcador visual** con escudos, posesión y contexto en previa, directo y parte.
- **Claves del partido**: forma, goleadores, bajas y aforo previsto.
- **Documento de diseño UI**: investigación, paleta, contraste, componentes y checklist de usabilidad en `manager/docs/16_DISENO_UI.md`.

### Corregido

- **Once automático:** los jugadores se elegían en orden de prioridad y luego se emparejaban con la formación por índice, lo que podía colocar un delantero como central. Ahora cada jugador se guarda en el índice de su slot y el once sale en orden de pista.
- **Cambio de formación:** al cambiar de formación se autoalinea el once para evitar que los slots anteriores queden descolocados.

### Cambiado

- Paleta dark-first con **ámbar** como acción principal y **azul** como información, separando el verde semántico de éxito.
- Contraste de texto y componentes revisado contra WCAG AA.
- Enlace “Saltar al contenido”, foco visible, objetivos táctiles de 44 px en móvil y respeto a `prefers-reduced-motion`.
- Navegación con Noticias y escudo del club actual.
- Tests ampliados a **51**.

### Pruebas

```bash
cd manager
python3 -m pytest src/tests -q
```

Resultado: 51 tests superados.

---

## 2026-10-21 — Fotos de jugadores e interfaz web más cómoda

### Añadido

- Fotos locales de todos los jugadores en la web:
  - ruta segura `/photo/<archivo>`;
  - fallback a avatar con iniciales;
  - fotos en plantilla, ficha, táctica, mercado y partido en directo.
- Plantilla rediseñada por grupos de posición con fichas visuales.
- Ficha de jugador con foto grande, posición y arquetipo destacados y barras de atributos.
- Pizarrón de táctica con slots por posición, foto, OVR, arquetipo y selector de jugador.
- Mercado rediseñado con fichas de jugador.
- Previa y partido en directo con fotos y datos destacados.
- Tests de fotos y plantilla web.

### Cambiado

- Tests ampliados a 50.

### Pruebas

```bash
cd manager
python3 -m pytest src/tests -q
```

Resultado: 50 tests superados.

---

## 2026-10-21 — Alpha web local

### Añadido

- Aplicación web Flask + Jinja para jugar desde el navegador:
  - nueva partida DHA/DHB;
  - carga y guardado SQLite;
  - dashboard;
  - plantilla y ficha;
  - táctica y once;
  - entrenamiento;
  - mercado, contratos y agentes libres;
  - staff y junta;
  - cantera;
  - prensa;
  - Copa del Rey;
  - clasificación y calendario;
  - partido rápido;
  - partido en directo con cuartos, momentos, cambios y táctica.
- `manager/run_web.py`.
- `manager/web/app.py`, plantillas y CSS.
- `manager/docs/15_WEB_ALPHA.md`.
- Tests de rutas web y partido en directo.

### Cambiado

- Tests ampliados a 49.

### Pruebas

```bash
cd manager
python3 -m pytest src/tests -q
```

Resultado: 49 tests superados.

---

## 2026-10-21 — Corrección del formato de la Copa del Rey

### Corregido

- La Copa del Rey ya no incluye equipos de DHB.
- Participan los **8 mejores de DHA al terminar la primera vuelta** (jornada 11).
- Formato correcto:
  - cuartos de final, semifinal, tercer/cuarto puesto y final;
  - a partido único;
  - en un fin de semana;
  - empate resuelto por shootout.
- El cuadro se genera 1º vs 8º, 2º vs 7º, 3º vs 6º y 4º vs 5º.
- Se eliminó el formato incorrecto de 16 equipos con ida y vuelta.

### Pruebas

```bash
cd manager
python3 -m pytest src/tests -q
```

Resultado: 45 tests superados.

---

## 2026-10-21 — DHB jugable desde el inicio

### Añadido

- Selección de club DHA o DHB al empezar una partida.
- La DHB se puede jugar completa desde la primera temporada:
  - dos grupos de 8;
  - fase 2;
  - 21 jornadas;
  - Final Four y ascenso.
- `--auto` acepta clubes DHA y DHB.
- Test de creación de partida con club DHB.

### Cambiado

- El menú de selección de club permite cambiar de liga con `L`.
- El dashboard, calendario y clasificación muestran el grupo DHB.
- Tests ampliados a 45.

### Pruebas

```bash
cd manager
python3 -m pytest src/tests -q
```

Resultado: 45 tests superados.

---

## 2026-10-21 — Economía, retiradas y test de 10 temporadas

### Añadido

- Retiradas de jugadores al final de temporada:
  - probabilidad según edad y nivel;
  - aviso en inbox para jugadores importantes;
  - registro en el resumen de temporada;
  - sustitución con canteranos.
- Ajuste económico:
  - presupuestos de fichajes ampliados;
  - suelo salarial para estrellas;
  - valoración de mercado con factor de edad;
  - fichajes de mayor cuantía.
- Test de 10 temporadas con mercado, agentes libres y retiradas.
- Actualización de `manager/docs/14_TEST_ESTRESS_10_TEMPORADAS.md`.

### Resultado

- 41 movimientos en el test de estrés y 17 en el test con el mercado real.
- 29 retiradas en el test de estrés y 34 en el test real.
- Venta récord: 493.896 €.
- 10 temporadas sin errores.
- DHA/DHB estables y plantillas de al menos 18 jugadores.

### Pruebas

```bash
cd manager
python3 -m pytest src/tests -q
```

Resultado: 44 tests superados.

---

## 2026-10-21 — Test de estrés de 10 temporadas con mercado

### Añadido

- Simulación de 10 temporadas completas con:
  - mercado de verano e invierno;
  - agentes libres;
  - Copa;
  - EHL;
  - DHB de dos fases;
  - cantera y multi-temporada.
- Documento `manager/docs/14_TEST_ESTRESS_10_TEMPORADAS.md`.
- Registro de 40 movimientos de mercado y de los fichajes más caros.

### Resultado

- Sin errores de ejecución.
- 12 equipos DHA y 16 DHB estables.
- Ningún equipo por debajo de 18 jugadores.
- 10 temporadas en 104,4 segundos.

### Observaciones

- Algunas estrellas se mueven por debajo de su valor.
- Hay que ajustar valoración de jugadores, salarios y presupuesto de fichajes.

---

## 2026-10-21 — Copa a ida y vuelta y EHL

### Añadido

- Copa del Rey a doble partido en octavos, cuartos y semifinal.
- Final a partido único y shootout si el global acaba empatado.
- EHL de final a ocho:
  - dos primeros de DHA;
  - campeón de Copa si es DHA;
  - cinco clubes europeos modelo;
  - cuartos, semifinal y final;
  - campeón en el resumen de temporada.
- Tests de Copa a doble partido y EHL.

### Cambiado

- La Copa ya no se resuelve a partido único salvo la final.
- El resumen de temporada muestra el campeón de Copa y de EHL.
- Tests ampliados a 43.

### Pruebas

```bash
cd manager
python3 -m pytest src/tests -q
```

Resultado: 43 tests superados.

---

## 2026-10-21 — Fase 5A: DHB real y agentes libres

### Añadido

- DHB con formato de dos fases:
  - dos grupos de 8 en la primera fase;
  - 14 jornadas por grupo;
  - Grupo A y Grupo B en la segunda fase;
  - 7 jornadas de segunda fase y 21 totales;
  - Final Four del Grupo A;
  - ascenso de los dos primeros del Grupo A.
- Agentes libres:
  - todos los jugadores de 1ª Andaluza pasan al mercado;
  - el club de 1ª Andaluza desaparece del mundo simulado;
  - fichaje sin traspaso, solo salario y contrato.
- Simulación de fondo de DHA/DHB para ascensos y descensos.
- `manager/docs/13_FASE5A_DHB_REAL_Y_AGENTES_LIBRES.md`.
- Tests de agentes libres y fases DHB.

### Cambiado

- La liga DHB ya no es una única tabla de 16 equipos.
- La clasificación muestra el grupo del usuario cuando juega en DHB.
- El calendario admite ligas de ida o ida/vuelta.
- Tests ampliados a 42.

### Pruebas

```bash
cd manager
python3 -m pytest src/tests -q
```

Resultado: 42 tests superados.

---

## 2026-10-20 — Fase 4: Copa, cantera, prensa y junta dinámica

### Añadido

- Copa del Rey de 16 equipos:
  - 12 DHA + 4 mejores DHB;
  - octavos, cuartos, semifinal y final a partido único;
  - shootout en caso de empate;
  - premio de 50.000 € y confianza para el campeón;
  - pantalla de Copa y simulación completa.
- Cantera:
  - academia por club;
  - juveniles con edad, posición, overall, potencial, salario y contrato;
  - promoción al primer equipo y liberación;
  - desarrollo y nuevas generaciones al final de temporada.
- Rueda de prensa:
  - dos preguntas por jornada;
  - tres respuestas con efectos en moral, afición y junta;
  - historial de titulares.
- Junta directiva dinámica:
  - objetivo de temporada;
  - revisión al final de temporada;
  - cambios de confianza y presupuesto de fichajes;
  - aviso de riesgo de destitución.
- `manager/docs/12_FASE4_COPA_CANTERA_PRENSA_JUNTA.md`.
- Tests de Copa, cantera, prensa y junta.

### Cambiado

- El resumen de temporada incluye Copa y revisión de la junta.
- El dashboard añade Copa, prensa y cantera.
- Tests ampliados a 40.

### Pruebas

```bash
cd manager
python3 -m pytest src/tests -q
```

Resultado: 40 tests superados.

---

## 2026-10-20 — Fase 3: mercado, contratos y multi-temporada

### Añadido

- Mercado de fichajes con ventanas de verano e invierno.
- Búsqueda de jugadores con informe de ojeador y horquilla de overall.
- Ofertas de traspaso, negociación de salario y contrato.
- Ofertas recibidas por jugadores propios.
- Mercado IA entre clubes rivales.
- Renovaciones y expiración de contratos.
- Contratación y despido de staff.
- Multi-temporada:
  - ascensos y descensos DHA/DHB;
  - liga DHB simplificada de 16 equipos y 30 jornadas;
  - envejecimiento, retiradas, canteranos de relleno y nueva temporada.
- `manager/docs/11_FASE3_MERCADO_Y_MULTITEMPORADA.md`.
- Tests de mercado y multi-temporada.

### Cambiado

- El calendario y la clasificación son genéricos para DHA y DHB.
- La temporada puede continuar varias veces.
- Si el club desciende, la siguiente temporada se juega en DHB.
- Tests ampliados a 36.

### Pruebas

```bash
cd manager
python3 -m pytest src/tests -q
```

Resultado: 36 tests superados.

---

## 2026-10-20 — Staff, junta directiva y finanzas

### Añadido

- Staff DHA para los 12 clubes:
  - segundo entrenador, preparador físico, entrenador de porteros, analista, ojeador, fisioterapeuta y director deportivo;
  - ratings, salarios, contrato, fuente y confianza.
- Junta directiva completa por club:
  - presidente, vicepresidente, secretario, tesorero, vocal de hockey y vocal social;
  - nombres reales donde había fuente y modelos donde no.
- Efectos del staff:
  - segundo entrenador en plan automático y charla;
  - preparador físico en sesiones físicas y prevención;
  - fisioterapeuta en recuperación;
  - analista en vídeo y preparación del rival;
  - entrenador de porteros en set pieces.
- Finanzas:
  - caja operativa y presupuesto de fichajes separados;
  - salarios de jugadores y staff;
  - patrocinio por jornada, taquilla y viajes;
  - cierre financiero por jornada;
  - historial de movimientos;
  - aviso y pérdida de confianza si la caja entra en negativo.
- `manager/data/staff_dha.json` y `manager/data/staff_dha_sources.md`.
- `manager/docs/10_STAFF_Y_FINANZAS.md`.
- Tests de staff y finanzas.

### Cambiado

- El dashboard muestra caja, presupuesto de fichajes y salarios.
- La pantalla de finanzas se amplía con balance, movimientos y confianza.
- Los salarios de los jugadores se reparten proporcionalmente al presupuesto.
- El entrenamiento usa los ratings del staff.
- Tests ampliados a 30.

### Pruebas

```bash
cd manager
python3 -m pytest src/tests -q
```

Resultado: 30 tests superados.

---

## 2026-10-20 — Entrenamiento semanal con plan automático

### Añadido

- Pantalla de entrenamiento semanal:
  - plan automático del segundo entrenador;
  - editor de cinco sesiones;
  - semana de recuperación de un clic.
- Nueve tipos de sesión: recuperación, descanso, físico, táctico, set pieces, ataque, defensa, vídeo y activación.
- Efectos sobre fatiga, forma, moral, cohesión, atributos, lesiones y preparación del rival.
- El entrenamiento IA se aplica automáticamente cada jornada para no dar ventaja artificial al usuario.
- `prep_bonus` de preparación del rival aplicado al ataque y la defensa del siguiente partido.
- Persistencia de `week_trained`, `weekly_plan`, `training_report` y `ai_training_round`.
- Documento `manager/docs/09_ENTRENAMIENTO_SEMANAL.md`.

### Cambiado

- El dashboard muestra el estado del entrenamiento semanal.
- Si no se planifica, el segundo entrenador aplica el plan automático antes del partido.
- `play_round` y `prepare_live_round` garantizan entrenamiento de usuario e IA una vez por jornada.
- Tests ampliados a 26.

### Pruebas

```bash
cd manager
python3 -m pytest src/tests -q
```

Resultado: 26 tests superados.

---

## 2026-10-20 — Charla de vestuario e IA reactiva

### Añadido

- Charla de vestuario al descanso:
  - arenga, calma, exigir, confiar o delegar;
  - efecto según marcador, moral, fatiga, competitividad y liderazgo;
  - bonus temporal para el tercer cuarto y reducción para el cuarto final;
  - delegación en el segundo entrenador, con rating propio por club.
- IA reactiva:
  - ajusta mentalidad, presión, bloque, tempo y pase según marcador, fatiga y táctica rival;
  - hace cambios si el equipo está fundido;
  - registra los ajustes como eventos `[Ajuste]`.
- El modo rápido delega automáticamente la charla en el segundo entrenador.
- Nuevas pruebas de charla, delegación, IA reactiva y eventos.

### Cambiado

- `MatchEngine` acepta `ai_sides` y `auto_talk_sides`.
- El dashboard, la previa y el parte muestran la gestión y la charla.
- `TeamState` guarda `assistant_rating` y lo carga desde las instalaciones del club.
- `manager/docs/08_MODO_DIRECTO_Y_GESTION.md` actualizado.

### Pruebas

```bash
cd manager
python3 -m pytest src/tests -q
```

Resultado: 21 tests superados.

---

## 2026-10-20 — Modo directo y recompensa a la gestión

### Añadido

- Partido en directo en el juego de gestión:
  - avance por cuartos o minuto a minuto;
  - comentario y estadísticas en vivo;
  - consulta de jugadores propios y rivales;
  - cambios manuales (hasta 5);
  - cambios de táctica en cualquier pausa;
  - simulación rápida del resto del partido.
- Sistema interno de **gestión (0-100)**:
  - moral, cohesión, fatiga, confianza, encaje posicional y rating del mánager;
  - bonus de ataque/defensa de hasta ±7 puntos;
  - bonus de lectura táctica de hasta +3;
  - bonus de banquillo por cambios con criterio;
  - rating del mánager que sube con resultados y victorias contra equipos superiores.
- `manager/docs/08_MODO_DIRECTO_Y_GESTION.md`.
- Tests `test_live_match.py`.

### Cambiado

- `MatchEngine` permite `advance_quarter()`, `advance_moment()` y `manual_substitute()` sin romper la simulación completa.
- La gestión y la táctica se recalculan en cada momento del partido.
- El dashboard y los partes muestran gestión, cohesión, mánager y bonus.
- `manager/README.md` y `README.md` actualizados.

### Pruebas

```bash
cd manager
python3 -m pytest src/tests -q
```

Resultado: 18 tests superados.

---

## 2026-10-20 — Fase 1 del juego de gestión (DHA)

### Añadido

- Juego de gestión de texto para DHA 2026-27:
  - selección de club y dossier;
  - dashboard;
  - plantilla y ficha de jugador;
  - táctica y once automático/manual;
  - calendario de 22 jornadas y 132 partidos;
  - motor de partido por fases con comentario por cuartos;
  - logística con bus, tren y avión; coste y fatiga;
  - clasificación, Final Four y playout;
  - guardado/carga SQLite y exportación JSON.
- Módulos `manager/src/`: `models.py`, `data_loader.py`, `calendar.py`, `match_engine.py`, `logistics.py`, `season.py`, `persistence.py`, `ui.py`, `main.py`.
- Documento `manager/docs/07_FASE1_IMPLEMENTACION.md`.
- 12 tests en `manager/src/tests/`.

### Cambiado

- `manager/README.md` y `README.md` actualizados con la Fase 1.
- La autoalineación rota jugadores con fatiga alta.
- El motor usa 64 momentos (4 cuartos × 16) y calibra ≈5,0–5,3 goles por partido.
- El guardado usa un blob JSON dentro de SQLite para el MVP.

### Archivos

- `manager/run.py`
- `manager/src/*.py`
- `manager/src/tests/*.py`
- `manager/docs/07_FASE1_IMPLEMENTACION.md`

### Pruebas

```bash
cd manager
python3 -m pytest src/tests -q
```

Resultado: 12 tests superados.

---

## 2026-10-19 — Tercera ronda de posiciones (DHB y 1ª Andaluza)

### Añadido

- Nuevas posiciones desde **Deporte de la Isla**, **Deporte Alicante**, **El Castillo de San Fernando** y la **web oficial del CD Giner de los Ríos**.
- San Fernando DHB:
  - Lázaro Navas → portero.
  - Vicente Aguirrezabala → medio.
  - Javi Galindo → defensa.
  - Óscar Gago → delantero.
  - Pablo Silva, Carlos Ramírez, Juan Muiño, Julián Agenjo, Samuel Cortés, Raúl Narváez, Dani Sánchez, Álvaro Varela, Dani Aguilera y Juan García → posiciones de 2024-25/2023-24, con confianza Baja/Media y nota de temporada.
- Borja Valcarcel (Giner) → defensa.
- Peio Gárate (Jolaseta) → defensa lateral.
- Pedro Arques (San Vicente) → delantero.
- José Antonio Hurtado (1ª Andaluza) → defensa; Álvaro Romero → delantero; Rubén Ramos → portero.

### Cobertura

- **175 posiciones oficiales** (17,9%).
- **801 estimadas** (82,1%).
- **100 jugadores de campo con posición oficial**.
- **399 subposiciones Central/Lateral estimadas**.

## 2026-10-19 — Segunda ronda de posiciones

### Añadido

- Nuevas posiciones desde **8SPORTS.es**, **Canarias7**, **Diari de Terrassa**, **EuroHockey**, **Global Sports Archive**, **CAH** y **University of Pretoria**.
- Jugadores incorporados:
  - Tyler Tomsett y Manuel Silvetti (UD Taburiente) → delanteros.
  - Nil Trujillo (Egara 1935) y Àlex Aymerich (Vallès) → delanteros.
  - Josep Martin Gutes (CD Terrassa), Albert Serrahima y Nicolau Mustaros (Junior) → delanteros.
  - Jared Pazafcass (Junior) → defensa.
  - Joaquín Kruger (Sanse) → medio.
  - Rafael Villalonga (RC de Campo) → medio.
  - Ricardo Sánchez (RC de Campo) → defensa central.
- Ricardo Sánchez, con 30 goles, pasa de delantero estimado a **central**; el modelo lo valora con pesos defensivos (overall central 89,9, arquetipo Muro).
- Cobertura oficial: **153 perfiles** (15,7%); estimados: **823** (84,3%); jugadores de campo oficiales: **81**.

### Descartado

- Enrique Zorita (RC de Campo) → defensa: solo hay una fuente de 2019-20 y contradice su perfil goleador actual.
- Enrique González (RC de Campo) → defensa: GSA dice defensa, pero la plantilla oficial 2019-20 lo situaba como medio.
- Sebastián Wolansky (FC Barcelona) → defensa: posible confusión de identidad y club.
- Alex Brecha (Egara 1935) → medio/delantero: nombre ambiguo y perfil de invitado.

## 2026-10-19 — Búsqueda de posiciones en prensa y selección

### Añadido

- Revisión de las **actas oficiales de la RFEH**: confirman porteros y alineaciones, pero no la posición de los jugadores de campo (la columna P/J solo distingue portero/jugador).
- Nuevas posiciones desde **Diari de Terrassa**:
  - Jan Clapés Castells (Club Egara) → defensa.
  - Marco Aguirregomezcorta (Club Egara) → delantero.
  - Borja Soler (CD Terrassa) → delantero.
- Nuevas posiciones desde **Mundo Deportivo** (lista de la selección española 2025):
  - Bruno Font (Junior FC) → medio.
  - Ignacio Abajo, José Basterra y Álvaro Iglesias (RC de Campo) → delanteros.
- Script `tools/apply_positions.py` para aplicar posiciones nuevas al manifiesto con backup y modo `--dry-run`.
- Catálogo `tools/position_sources.csv` con fuentes, URLs, fecha y cobertura.
- Hoja **Fuentes posiciones** en el Excel, con URL y fecha por jugador.
- Columnas **URL posición** y **Fecha posición** en las hojas de jugadores.

### Cambiado

- Jan Clapés Castells pasa de delantero estimado a defensa.
- Bruno Font Abad pasa de delantero estimado a medio.
- La cobertura oficial sube de 135 a 142 perfiles; los estimados bajan de 841 a 834.

Historial de cambios del proyecto. Las fechas son las de la sesión de trabajo; los datos de competición tienen su propia fecha de corte.

---

## 2026-10-19 — Modelo avanzado, editor y documentación

### Añadido

- Modelo de **37 atributos** en seis grupos:
  - Técnica (7).
  - 3D y set pieces (10).
  - Táctica (5).
  - Física (5).
  - Mental (4).
  - Portero (6).
- Cinco **overalls posicionales**:
  - Portero, Central, Lateral, Medio y Delantero.
- **Arquetipos** por posición.
- **Polivalencia**, potencial y valor de mercado.
- **Especialistas de set pieces** por equipo:
  - Inyector, stopper, drag flicker, desviador, primer runner, portero de PC, tirador de stroke, portero de stroke, aéreo y faltas.
- **Perfil agregado de set pieces** por equipo:
  - PC ataque, PC defensa, stroke, parada de stroke y aerial.
- Atributos específicos para:
  - saque de penalty corner (`pc_injection`);
  - parada de PC (`pc_trap`);
  - tiro de PC / drag flick (`pc_flick`);
  - desvío (`pc_deflection`);
  - primer runner (`pc_first_runner`);
  - parada de PC del portero (`pc_gk_save`);
  - tiro de stroke (`stroke_shot`);
  - parada de stroke (`stroke_save`);
  - faltas, 16 yardas y córners (`free_hit`);
  - aerial (`aerial`);
  - 3D (`regate_3d`).
- **Editor de jugador** en el juego:
  - Cambio de posición.
  - Edición de los 37 atributos.
  - Recálculo de overall, potencial, valor, arquetipo y ratings de equipo.
  - Persistencia en `localStorage`.
  - Etiqueta **Ajuste manual** en la ficha.
  - Botón para quitar el ajuste manual.
- Excel ampliado:
  - Hojas de atributos, especialistas, equipos, diccionario y cobertura.
  - Imágenes preservadas.
- CSV `jugadores_atributos_2026_27.csv`.
- Documentación maestra en `docs/`.
- Scripts persistentes en `tools/`.

### Cambiado

- El overall ya no se calcula solo con goles.
- La tabla de jugadores muestra **Central/Lateral/Medio/Delantero/Portero**.
- El filtro de posición usa las subposiciones.
- La ficha del jugador muestra:
  - 37 atributos agrupados;
  - cinco overalls;
  - arquetipo;
  - especialistas;
  - botón de edición.
- La ficha de equipo muestra los especialistas.
- Los ratings de equipo usan `attackScore` y `defenseScore` derivados de atributos.
- El `scoutText` explica la posición y los especialistas.
- El Excel de jugadores incluye subposición, grupo, arquetipo, overall, potencial, valor, polivalencia, overalls y especialistas.

### Corregido

- Un central con goles ya no se clasifica como delantero.
- Bruno Àvila Gran (56 goles) se mantiene como Central, overall 84,2, arquetipo Muro.
- Iain Martin McFadden se mantiene como Central, overall 73,9, arquetipo Central constructor.
- Los porteros tienen atributos de portero altos y atributos de campo bajos.
- La subposición se marca como estimada cuando la fuente solo indica “Defensa”.

### Archivos

- `juego_hockey/index.html`
- `juego_hockey/README.md`
- `equipos_hockey_hierba_espana_masculino_2026_27_con_atributos.xlsx`
- `jugadores_atributos_2026_27.csv`
- `tools/build_attributes_v2.py`
- `tools/generate_game.py`
- `tools/build_excel_attributes.py`
- `tools/hockey_template.html`
- `docs/00_PROYECTO.md` … `docs/07_GUIA_JUEGO.md`

---

## 2026-10-18 — Formato real y posiciones

### Añadido

- Formato real DHA:
  - 12 equipos, 22 jornadas.
  - Final Four.
  - Descenso directo del 12º.
  - Playout del 11º contra el 2º elegible de DHB.
- Formato real DHB:
  - Dos grupos de 8.
  - Primera fase de 14 partidos.
  - Segunda fase Grupo A/B con 6 arrastrados + 8 cruzados.
  - Final Four.
  - Ascenso del 1º elegible.
  - Playout del 2º elegible.
  - Descenso de 15º y 16º.
- Clubes vinculados y elegibilidad.
- Proyección DHA 2027-28.
- Posiciones para 976 perfiles:
  - 135 oficiales.
  - 841 estimadas.
  - 72 porteros.
- Informe de ligas y informe de posiciones.
- PDF de ambos informes.

### Cambiado

- El juego pasó de un formato genérico a DHA/DHB real.
- La tabla de jugadores incorporó posición y fuente.
- El Excel incorporó posiciones y cobertura.

### Archivos

- `juego_hockey/index.html`
- `informe_sistema_ligas_DHA_DHB_2026_27.md`
- `informe_posiciones_DHA_DHB_2026_27.md`
- `equipos_hockey_hierba_espana_masculino_2026_27_con_posiciones.xlsx`
- `jugadores_posiciones_2026_27.csv`

---

## 2026-10-17 — Juego HTML y datos base

### Añadido

- Lista única de clubes de DHA, DHB y primeras autonómicas.
- Plantillas con jugadores e invitados.
- Imágenes de jugadores.
- Juego HTML con:
  - Inicio.
  - Equipos.
  - Jugadores.
  - Simulador.
  - Conclusiones.
- Valoraciones iniciales basadas en goles.
- Excel y CSV de equipos y jugadores.

### Cambiado

- Se excluyeron filiales y duplicados.
- Se añadió San Fernando 1ª Andaluza.
- Se normalizaron nombres y equipos.

---

## 2026-10-16 — Investigación inicial

### Añadido

- Investigación del sistema de ligas DHA/DHB.
- Recopilación de fuentes RFEH, clubes y prensa.
- Primer listado de equipos.
- Primer análisis de posiciones.

---

## Plantilla para futuros cambios

```markdown
## AAAA-MM-DD — Título

### Añadido
- ...

### Cambiado
- ...

### Corregido
- ...

### Eliminado
- ...

### Archivos
- ...

### Pruebas
- ...
```
