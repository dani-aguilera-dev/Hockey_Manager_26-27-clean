# Hockey Manager España 2026-27 — Visión y arquitectura

**Estado:** diseño inicial.
**Tipo de juego:** gestión y entrenador, solo texto, sin gráficos.
**Base de datos:** 29 clubes, 976 perfiles, 37 atributos, ligas DHA/DHB/1ª Andaluza.
**Inspiración:** arquitectura de Football Manager, adaptada al hockey hierba y a la logística real de los clubes españoles.

---

## 1. Visión

Queremos un juego de gestión de hockey hierba en el que el jugador sea **entrenador y gestor de un club**, no un selector de jugadores en una tabla. El juego debe transmitir:

- que entrenar y elegir bien importa;
- que la logística y el calendario condicionan la temporada;
- que cada club tiene una historia, un estadio, una afición y una forma de entender el hockey;
- que las decisiones tienen consecuencias a corto y largo plazo;
- que el texto puede ser tan inmersivo como un motor gráfico.

El jugador empieza en un club de DHA, DHB o Primera Andaluza, con una plantilla, un cuerpo técnico, un presupuesto y una junta directiva. Su objetivo es sobrevivir, crecer y dejar huella.

### Pilares

1. **Datos con contexto.** Cada jugador tiene 37 atributos, posición, arquetipo y especialistas. Cada club tiene historia, estadio, ciudad, presupuesto y logística.
2. **Partido explicable.** El motor de partido genera eventos de texto comprensibles: por qué se concedió un PC, quién lo tiró, quién lo paró, por qué se agotó el equipo.
3. **Logística de verdad.** Viajes, hoteles, comidas, fatiga, recuperación y coste. No todos los desplazamientos cuestan lo mismo.
4. **Set pieces.** El penalty corner y el stroke son mini-juegos dentro del partido, con roles y especialistas.
5. **Mundo vivo.** La junta, la afición, la prensa, los agentes y los otros entrenadores reaccionan.
6. **Solo texto.** Sin 2D, sin 3D, sin animaciones. La información y la narrativa son la interfaz.

### No objetivos del MVP

- Motor gráfico 2D/3D.
- Física de bola en tiempo real.
- Multijugador online.
- Datos oficiales en vivo.
- Copa del Rey, EHL y competiciones europeas completas.
- Hockey femenino y categorías juveniles (fase posterior).

---

## 2. Qué imitamos de Football Manager

Football Manager es una referencia de **simulación de mundo + motor de partido + interfaz de gestión**. Su arquitectura pública y sus artículos técnicos permiten extraer estas ideas:

### 2.1. Motor de partido

- Los jugadores deciden **cada fracción de segundo** (FM habla de “slices” de un cuarto de segundo).
- Cada decisión se basa en **atributos**, contexto, táctica y estado del partido.
- El motor tiene **niveles de detalle**: partido completo para el equipo del jugador, simulación rápida para el resto.
- La IA de los entrenadores rivales ajusta táctica y cambios.
- Los árbitros y el VAR forman parte del motor.
- La fatiga, la moral y la dinámica afectan al rendimiento.

### 2.2. Mundo

- Base de datos relacional de clubes, jugadores, staff, competiciones y contratos.
- Desarrollo de jugadores por edad, entrenamiento, instalaciones y minutos.
- Mercado de fichajes como **máquina de estados**: oferta → respuesta del club → contrato → respuesta del jugador.
- Objetivos de la junta directiva y reputación del entrenador.
- Moral, dinámica de vestuario, promesas y minutos.
- Ojeadores, informes y conocimiento parcial del mercado.
- Lesiones, sanciones y condición física.

### 2.3. Interfaz

- Pantallas de datos, inbox, informes, tácticas, entrenamiento, finanzas y mercado.
- Información filtrada: no todo se sabe desde el principio.
- Decisiones con consecuencias y trazabilidad.

### 2.4. Qué cambiamos

| Football Manager | Nuestro juego |
|---|---|
| Fútbol 11, 90 minutos, 3 cambios (o 5) | Hockey hierba, 4×15, cambios rodantes |
| Motor 2D/3D a 40 Hz | Motor de texto por fases de 20-30 segundos |
| Offside, corners, penales | PC, stroke, 16 yardas, córner largo, self-pass, aerial, 3D |
| Campos de fútbol | Campos de hockey, superficies y desgaste |
| Viajes genéricos | Logística detallada: bus/tren/avión, hotel, comidas, fatiga |
| Base de datos de 50+ países | 29 clubes españoles, 976 perfiles |
| Atributos de fútbol | 37 atributos de hockey y 5 overalls posicionales |
| Sin especialistas de set pieces | Inyector, stopper, drag flicker, desviador, primer runner, portero de PC, stroke |

---

## 3. Bucle de juego

### 3.1. Escala temporal

| Escala | Qué ocurre |
|---|---|
| **Partido** | Fases de 20-30 segundos de tiempo simulado; 4 cuartos; descansos. |
| **Día** | Entrenamiento, recuperación, viajes, mercado, inbox, reuniones. |
| **Semana** | Planificación de entrenamiento, viaje, alineación, rueda de prensa. |
| **Mes** | Finanzas, junta, dinámica, ojeadores, cantera. |
| **Temporada** | Liga, Final Four, playout, ascensos/descensos, objetivos. |
| **Carrera** | Varias temporadas, reputación, fichajes, cantera, historia. |

### 3.2. Ciclo semanal típico

```
Lunes      recuperación + análisis del partido + inbox
Martes     entrenamiento físico/técnico + ojeadores
Miércoles  entrenamiento táctico + set pieces
Jueves     entrenamiento + viaje (si toca)
Viernes    activación + rueda de prensa + viaje
Sábado     partido (o domingo)
Domingo    viaje de vuelta + recuperación
```

El calendario real de DHA/DHB manda. El juego no inventa jornadas: usa el calendario de la temporada.

### 3.3. Bucle de decisión

1. El juego muestra el **dashboard** con fecha, próximo partido, posición, moral, presupuesto y mensajes.
2. El jugador revisa el **inbox** y toma decisiones (junta, prensa, jugadores, mercado).
3. Planifica **entrenamiento** y **viaje**.
4. Elige **convocatoria, alineación, táctica y especialistas**.
5. Juega el **partido** o lo simula en modo rápido.
6. Recibe **informe post-partido**, ratings, lesiones, sanciones y reacciones.
7. La **junta**, la **afición** y la **prensa** actualizan su confianza.
8. Avanza el calendario.

---

## 4. Arquitectura de software

### 4.1. Capas

```
+-----------------------------------------------------------+
|  UI de texto (CLI/TUI)                                    |
|  Dashboard · Inbox · Plantilla · Táctica · Partido · ...   |
+-----------------------------+-----------------------------+
                              |
+-----------------------------v-----------------------------+
|  Aplicación / casos de uso                                |
|  Avanzar día · Jugar partido · Negociar · Entrenar · ...   |
+-----------------------------+-----------------------------+
                              |
+-----------------------------v-----------------------------+
|  Mundo (world engine)                                     |
|  Calendario · Competiciones · Finanzas · Contratos ·       |
|  Mercado · Moral · Junta · Prensa · Logística · Cantera    |
+-----------------------------+-----------------------------+
                              |
+-----------------------------v-----------------------------+
|  Motor de partido (match engine)                          |
|  Fases · Acciones · Set pieces · Árbitro · Fatiga · IA     |
+-----------------------------+-----------------------------+
                              |
+-----------------------------v-----------------------------+
|  Dominio y datos                                          |
|  Club · Jugador · Staff · Estadio · Atributos · Contratos   |
+-----------------------------+-----------------------------+
                              |
+-----------------------------v-----------------------------+
|  Persistencia                                             |
|  SQLite + JSON de datos + save game + seed determinista    |
+-----------------------------------------------------------+
```

### 4.2. Módulos

| Módulo | Responsabilidad |
|---|---|
| `domain` | Entidades y reglas puras: club, jugador, staff, contrato, táctica, evento. |
| `data` | Carga de clubes, ciudades, competiciones, atributos y plantillas. Validación de esquema. |
| `world` | Calendario, competiciones, finanzas, contratos, mercado, moral, junta, prensa, logística. |
| `match` | Simulación de partido, eventos, set pieces, árbitro, fatiga, ratings. |
| `ai` | Entrenadores rivales, juntas, agentes, mercado, selección de alineaciones. |
| `ui` | Pantallas de texto, comandos, inbox, visualización de datos. |
| `persistence` | SQLite, migraciones, guardado/carga, exportación JSON. |
| `tests` | Unitarios, integración, simulaciones largas, balance, determinismo. |

### 4.3. Principios técnicos

- **Determinismo:** misma semilla + mismas decisiones = mismo resultado.
- **Separación motor/UI:** el motor no sabe si se juega en CLI, web o test.
- **Datos fuera del código:** clubes, competiciones y atributos en JSON/SQLite.
- **Eventos como contrato:** todo lo que pasa en el partido y el mundo se registra como evento.
- **Explicabilidad:** cada evento debe poder rastrearse a atributos, táctica, fatiga y contexto.
- **Rendimiento:** la simulación rápida de partidos de IA debe resolverse en milisegundos.

### 4.4. Flujo de datos

```
clubs.json + players.csv + competitions.json
        │
        ▼
  data_loader.py  ──►  SQLite (save game)
        │
        ▼
  world_state  ──►  match_engine  ──►  events + stats
        │                                  │
        ▼                                  ▼
  UI de texto  ◄────────────────────  inbox + informes
```

---

## 5. Módulos de gestión

### 5.1. Club

Cada club tiene:

- identidad: nombre, ciudad, fundación, colores, apodo, historia;
- estadio: nombre, dirección, superficie, capacidad, instalaciones;
- afición: socios, expectativas, paciencia;
- junta: presupuesto, objetivos, confianza;
- cuerpo técnico: 13 roles;
- plantilla: jugadores, contratos, moral, lesiones;
- logística: aeropuerto, tren, modo de viaje, distancias;
- rivalidades y cultura deportiva.

### 5.2. Plantilla

- 16 convocados por partido: 11 titulares y hasta 5 suplentes.
- 11 titulares + suplentes rodantes.
- Posiciones: portero, central, lateral, medio, delantero, polivalente.
- Roles: portero clásico/moderno, central stopper/constructor, lateral defensivo/carrilero, medio creativo/box-to-box/defensivo, delantero área/espacio/apoyo.
- Especialistas: inyector, stopper, drag flicker, desviador, primer runner, portero de PC, tirador de stroke, portero de stroke, aéreo, faltas.
- Estado: forma, fatiga, moral, lesiones, sanciones, contrato.

### 5.3. Táctica

- Formación: 4-3-3, 3-4-3, 3-3-3-1, 4-4-2, 5-3-2, 3-2-1-4.
- Mentalidad: muy defensiva → muy ofensiva.
- Presión: baja, media, alta, muy alta.
- Bloque: bajo, medio, alto.
- Anchura: estrecha, normal, ancha.
- Tempo: lento, normal, rápido.
- Pase: corto, mixto, directo.
- Rutina de PC: directa, slip izquierda/derecha, desvío, rebote, ensayada.
- Instrucciones específicas: presión tras pérdida, salida en corto, juego directo, basculación, etc.

### 5.4. Entrenamiento

- Sesiones: recuperación, físico, técnico, táctico, set pieces, vídeo, descanso.
- Intensidad: suave, media, alta.
- Foco: atributos concretos (definición, PC, cobertura, etc.).
- Efectos: desarrollo, fatiga, riesgo de lesión, moral.
- Plan semanal con carga total; la carga excesiva penaliza el partido.

### 5.5. Desarrollo

- Edad, potencial, minutos, entrenamiento, instalaciones, calidad del staff.
- Curva de desarrollo: jóvenes crecen; veteranos declinan.
- Atributos ocultos hasta que se entrenan o se ojean.
- Lesiones y rehabilitación.

### 5.6. Moral y dinámica

- Moral individual (1-20), felicidad, relaciones.
- Cohesión, determinación y liderazgo del grupo.
- Factores: resultados, minutos, promesas, salarios, rol, conflictos, charlas.
- Estados: contento, neutro, molesto, quiere salir, líder, conflicto.
- Reuniones individuales y charlas de equipo.

### 5.7. Junta directiva

- Objetivos: ganar la liga, Final Four, top 8, permanencia, ascenso, play-off, sostenibilidad, cantera.
- Confianza: alta, media, baja.
- Paciencia: 1-5.
- Presupuesto: fichajes, salarios, operaciones.
- Reuniones trimestrales y evaluación de temporada.
- Dos fracasos consecutivos pueden costar el puesto.

### 5.8. Finanzas

- Ingresos: taquilla, socios, patrocinios, subvenciones, merchandising, traspasos.
- Gastos: salarios, staff, viajes, hoteles, comidas, instalaciones, médicos, cantera.
- Presupuesto de fichajes y masa salarial.
- Balance mensual; alertas de déficit.
- La logística es una partida real: un viaje a Canarias puede costar más que una semana de entrenamiento.

### 5.9. Mercado y contratos

- Ventanas de verano e invierno.
- Ofertas por jugadores y respuestas de clubes/jugadores.
- Contratos: duración, salario, prima, cláusula, rol.
- Agentes y rumores.
- Ojeadores: conocimiento parcial, informes con rango de atributos.
- Cantera: captación anual, promoción al primer equipo.

### 5.10. Prensa y afición

- Ruedas de prensa antes/después.
- Declaraciones que afectan a moral, afición y junta.
- Noticias generadas por resultados, fichajes, lesiones y conflictos.
- La afición valora esfuerzo, estilo y resultados.

---

## 6. Logística: el diferencial

La logística no es un adorno. En el hockey español hay:

- **Canarias**: cada desplazamiento a la península exige vuelo, traslado y hotel.
- **Cádiz**: viajes largos a Cataluña y Madrid.
- **Cantabria y País Vasco**: distancias medias, pero con calendario congestionado.
- **Clústeres catalán y madrileño**: desplazamientos cortos en bus.
- **Valencia y Alicante**: tren/bus a Madrid y Cataluña.
- **Superficies distintas**: water-based, sand-dressed, sand-filled; afectan al bote, la velocidad y la lesión.

El sistema de logística se detalla en `02_LOGISTICA.md`.

---

## 7. Motor de partido: resumen

El motor es de texto y se basa en **fases de posesión**:

- 4 cuartos de 15 minutos (FIH 2026/2027).
- Fases de 20-30 segundos simulados.
- Acciones: salida, progresión, pressing, tackle, intercepción, entrada al círculo, tiro, PC, stroke, aerial, 3D, falta, 16 yardas, córner largo, saque de banda.
- Resolución por atributos, táctica, fatiga, moral, localía, clima y superficie.
- Set pieces como subestados con roles.
- Eventos de texto, estadísticas, ratings y comentario.
- Simulación rápida para partidos de IA.

El diseño completo está en `01_MOTOR_PARTIDO.md`.

---

## 8. Interfaz de texto

Sin gráficos. Pantallas de texto con tablas, colores opcionales y comandos:

- Menú principal.
- Selección de club.
- Dashboard.
- Inbox.
- Plantilla.
- Táctica.
- Entrenamiento.
- Calendario.
- Clasificación.
- Club/Estadio.
- Finanzas.
- Mercado.
- Ojeadores.
- Staff.
- Médico.
- Junta.
- Prensa.
- Logística.
- Partido.

El diseño está en `04_UI_TEXTO.md`.

---

## 9. Persistencia y datos

- `manager/data/clubs.json`: 29 clubes con historia, estadio, instalaciones, finanzas, junta y logística.
- `manager/data/cities.json`: ciudades, coordenadas, aeropuertos y tren.
- `manager/data/competitions.json`: formatos DHA/DHB/1ª.
- `manager/data/tactical_roles.json`: formaciones y roles.
- `manager/data/staff_roles.json`: 13 roles.
- `manager/data/events.json`: plantillas de eventos.
- `manager/schema/schema.sql`: 41 tablas SQLite.
- `manager/saves/`: partidas guardadas.

---

## 10. Riesgos

| Riesgo | Mitigación |
|---|---|
| El motor de texto se queda corto | Empezar con fases y eventos; iterar con playtesting. |
| Los datos de clubes/estadios son incompletos | Marcar `data_quality` y `capacity_confidence`; permitir edición. |
| El juego se vuelve un Excel | Inbox, prensa, moral, narrativa y decisiones con consecuencias. |
| La logística es tediosa | Automatizar planes recomendados y mostrar solo decisiones relevantes. |
| El equilibrio de ligas es injusto | Simulaciones largas y ajuste de presupuestos/fatiga. |
| El motor es determinista y aburrido | Variedad de eventos, sorpresas, lesiones, clima, arbitraje. |
| Sin gráficos no hay inmersión | Texto de calidad, perfiles de club, rivalidades, historia. |

---

## 11. Próximo paso

1. Validar este diseño.
2. Implementar el prototipo de texto (`manager/src/prototype.py`).
3. Probar un ciclo de temporada con 29 clubes.
4. Ajustar el motor de partido y la logística.
5. Ampliar a mercado, cantera y multi-temporada.

## 12. Referencias de Football Manager

- Football Manager, *Match Engine AI in FM21*: slices de decisión, atributos, marcaje, portero y juego central. <https://www.footballmanager.com/news/match-engine-ai-fm21>
- Football Engine 2026 (proyecto open source que replica una arquitectura FM): separación MatchStepper / World Engine, transfers como FSM, staff, objetivos de junta, SQLite y datos JSON. <https://github.com/DeltaBitsSystem/FootballEngine>
- Football Manager, *Smarter Transfers, Squad Building and Finance*: IA de mercado, reputación, forma y finanzas. <https://www.footballmanager.com/features/smarter-transfers-squad-building-and-finance>
- Rock Paper Shotgun, *How Football Manager's transfer AI works*: mercado, inflación, contratos y percepción del jugador. <https://www.rockpapershotgun.com/football-manager-transfer-ai>
- Passion4FM, *How to Improve Player's Morale & Happiness in Football Manager*: moral, felicidad, minutos y dinámica. <https://www.passion4fm.com/how-to-improve-players-morale-happiness-in-football-manager/>

> Documentos relacionados: `01_MOTOR_PARTIDO.md`, `02_LOGISTICA.md`, `03_CLUBES_Y_ESTADIOS.md`, `04_UI_TEXTO.md`, `05_ROADMAP_Y_MVP.md`, `06_MODELO_DATOS.md`.
