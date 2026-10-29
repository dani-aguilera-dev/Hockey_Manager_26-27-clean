# Interfaz de texto

**Principio:** sin gráficos, sin 2D, sin 3D. La interfaz es texto, tablas y decisiones. La inmersión viene de la información, la narrativa y las consecuencias.

---

## 1. Formato

Dos opciones válidas:

1. **CLI/TUI en terminal** con Python + `rich` (recomendado para el MVP).
2. **Web de texto** con HTML mínimo y formularios, sin canvas ni animaciones.

El motor es independiente de la UI. La primera versión será una CLI/TUI.

---

## 2. Pantalla de inicio

```
============================================================
  HOCKEY MANAGER ESPAÑA 2026-27
  Liga IATI · DHA · DHB · Primera Andaluza
============================================================

  1. Nueva partida
  2. Cargar partida
  3. Editor de datos
  4. Ajustes
  5. Salir

  > _
```

---

## 3. Selección de club

```
ELIGE TU CLUB

Liga: [DHA] [DHB] [1ª Andaluza] [Todos]

#   Club                          Ciudad            Estadio                 Dificultad
1   Real Club de Campo            Madrid            Campo de Hockey          Muy alta
2   Atlètic Terrassa HC           Terrassa          Can Salas                Alta
3   RC Polo                       Barcelona         Eduardo Dualde           Alta
4   Club Egara                    Terrassa          Pla del Bon Aire         Alta
5   Junior FC                     Sant Cugat        Camp Junior FC           Alta
6   CD Terrassa Hockey            Matadepera        Les Pedritxes            Media
...
29  Club de Hockey San Fernando   San Fernando      IMD Pablo Negre          Baja

[Enter] ver dossier   [F] filtrar   [Esc] volver
```

### Dossier de club

```
CD TERRASSA HOCKEY
Fundado en 1910 · Matadepera (Barcelona) · Rojo y blanco
Estadio: Les Pedritxes - Camp C1 · 1.200 (estimada) · water-based

HISTORIA
Fundado en 1910, es el club de hockey más antiguo de España...

JUNTA
Objetivo: Top 6 y consolidar el proyecto
Presión: media · Paciencia: 3/5
Presupuesto de fichajes: 300.000 €
Masa salarial: 650.000 €

LOGÍSTICA
Aeropuerto: BCN · Tren: Terrassa · Modo habitual: bus
Cluster catalán: desplazamientos cortos.

[Enter] aceptar el puesto   [Esc] volver
```

---

## 4. Dashboard

```
MIÉRCOLES 23/09/2026                    CD TERRASSA · DHA
----------------------------------------------------------------
Próximo partido:  Club Egara vs CD Terrassa · sábado 26/09 · 15:00
Posición: 8º/12 · 3 pts · Forma: E V D
Presupuesto: 300.000 € · Balance: -12.400 €
Moral: 12/20 · Cohesión: 14/20 · Junta: 65/100
----------------------------------------------------------------
INBOX (3)
  [J] La junta espera el top 6
  [P] Rueda de prensa previa
  [M] Oferta por Iain McFadden
----------------------------------------------------------------
[P] Plantilla  [T] Táctica  [E] Entrenamiento  [C] Calendario
[L] Logística  [F] Finanzas  [M] Mercado  [S] Staff  [I] Inbox
[Enter] continuar / avanzar día
```

---

## 5. Plantilla

```
PLANTILLA · 24 jugadores · 16 convocados

#   Jugador                     Pos     Edad  Overall  Forma  Fatiga  Moral  Estado
1   Sergio Salas Medina         POR      29    74,2    7,1    12%     Bueno  Titular
2   Iain Martin McFadden        CEN      24    73,9    7,0    18%     Bueno  Titular
3   Carlos Bultà Aranda         MED      19    69,5    6,8    22%     Alto   Rotación
...
```

Teclas:

- `Enter`: ficha del jugador.
- `C`: convocatoria.
- `O`: ordenar.
- `F`: filtrar por posición/estado.
- `Esc`: volver.

### Ficha de jugador

```
IAIN MARTIN MCFADDEN
Central · 24 años · CD Terrassa · 0 goles
Overall central: 73,9 · Potencial: 75,9 · Valor: 740.000 €
Arquetipo: Central constructor · Polivalencia: 1,6
Especialista: stopper de PC, faltas

ATRIBUTOS
Técnica        Control 68 · Pase 76 · Conducción 71 · Golpeo 63
3D/set pieces  PC saque 68 · PC parado 80 · PC tiro 72 · Stroke 66
Táctica        Cobertura 78 · Posicionamiento 75 · Primer runner 74
Física         Velocidad 62 · Fuerza 70 · Resistencia 72
Mental         Decisiones 74 · Concentración 71 · Liderazgo 65
Portero        Reflejos 34 · Blocaje 33

CONTRATO
Hasta 30/06/2028 · 24.000 €/año · Rol: titular
Moral: 15/20 · Fatiga: 18% · Estado: disponible
```

---

## 6. Táctica

```
TÁCTICA · CD TERRASSA

Formación: [4-3-3]
Mentalidad: [Equilibrada]
Presión: [Media]     Bloque: [Medio]
Anchura: [Normal]    Tempo: [Normal]
Pase: [Mixto]        Rutina PC: [Directa]

ONCE INICIAL
POR  Sergio Salas
LAT  Víctor Guerra        CEN  Iain McFadden
CEN  Joan Bultà           LAT  Guillem Cortina
MED  Carlos Bultà         MED  Pol Calonge
MED  Marc Miró
DEL  Borja Soler          DEL  Aleix Vericat
DEL  Joan Miro

ESPECIALISTAS
Inyector: Pol Calonge · Stopper: Iain McFadden
Drag flicker: Joan Miro · Desviador: Aleix Vericat
Primer runner: Guillem Cortina · Portero PC: Sergio Salas
Stroke: Enric Miralles · Portero stroke: Sergio Salas
Aéreo: Borja Soler · Faltas: Iain McFadden

[G] guardar  [A] autoalineación  [S] set pieces  [Esc] volver
```

---

## 7. Entrenamiento

```
PLAN SEMANAL · semana del 21/09/2026

Lunes      Recuperación       Suave    —
Martes     Físico             Alta     Resistencia
Miércoles  Táctico            Media    Pressing
Jueves     Set pieces         Media    PC defensivo
Viernes    Activación         Suave    —
Sábado     PARTIDO
Domingo    Descanso           —        —

Carga semanal: 72% · Riesgo de lesión: medio
Moral del grupo: 12/20 · Cohesión: 14/20

[A] añadir sesión  [E] editar  [R] recomendar  [Esc] volver
```

---

## 8. Calendario y clasificación

```
CALENDARIO · DHA

J1  20/09  CD Terrassa 1-2 Atlètic Terrassa
J2  26/09  Club Egara vs CD Terrassa
J3  03/10  CD Terrassa vs RC Polo
...

CLASIFICACIÓN
#   Equipo                     PJ  G  E  P  GF  GC  DG  PTS
1   Real Club de Campo         5   4  1  0  18   6  +12  13
2   Atlètic Terrassa           5   4  0  1  15   7   +8  12
...
```

---

## 9. Club y estadio

```
CD TERRASSA HOCKEY
Fundado en 1910 · Matadepera · 1.200 socios (modelo)

ESTADIO
Les Pedritxes - Camp C1
Ctra. Terrassa a Talamanca, km 5,6
Superficie: water-based · Capacidad: 1.200 (estimada)
Instalaciones: 2 campos, gimnasio, médico, vídeo, cantera 4/5

PALMARÉS
...

HISTORIA
...
```

---

## 10. Finanzas

```
FINANZAS · temporada 2026-27

Ingresos             Gasto
Taquilla   45.000    Salarios      420.000
Socios     60.000    Viajes         38.000
Patrocinio 80.000    Hoteles        12.000
Subvención 20.000    Instalaciones  25.000
                     Cantera        18.000
Balance: -48.000 €

Presupuesto de fichajes: 300.000 €
Masa salarial: 650.000 €
Alerta: el gasto en viajes supera el 15% del presupuesto.
```

---

## 11. Mercado y ojeadores

```
MERCADO · ventana de verano

Jugador                     Club                 Pos     Edad  Valor      Interés
Bruno Font Abad             Junior FC            MED      21    1.180.000  Ojeado
Tyler Tomsett               UD Taburiente        DEL      24      820.000  Informe
...

OFERTA POR IAIN MCFADDEN
Club: RC Polo · Oferta: 650.000 € · Valor: 740.000 €
[R] rechazar  [C] contraoferta  [A] aceptar
```

---

## 12. Staff

```
CUERPO TÉCNICO

Entrenador principal     Ignasi Torras        Liderazgo 16 · Táctica 15
Segundo entrenador       Xavi Lleonart        Táctica 17 · Análisis 16
Entrenador de porteros   ...                  Porteros 15
Preparador físico        ...                  Físico 16
Fisioterapeuta           ...                  Rehabilitación 15
Ojeador                  ...                  Evaluación 14
Team manager             ...                  Logística 17
```

---

## 13. Médico

```
PARTE MÉDICO

Jugador               Lesión              Estado        Vuelta
Víctor Guerra         Esguince tobillo   Rehabilitación 2 semanas
Joan Bultà            Sobrecarga         Descanso       3 días
```

---

## 14. Junta y prensa

```
JUNTA DIRECTIVA

Objetivo: Top 6 y consolidar el proyecto
Confianza: 65/100 · Paciencia: 3/5
Mensaje: "La temporada es larga, pero necesitamos resultados pronto."

PRENSA
"¿Cómo valora el inicio de temporada?"
  1. "Estamos construyendo."
  2. "El objetivo es ganar cada partido."
  3. "No hablo de objetivos individuales."
```

---

## 15. Logística

```
PRÓXIMO PARTIDO: Club Egara vs CD Terrassa · 26/09 · 15:00
Distancia: 6 km · Modo: bus · Coste: 180 € · Fatiga: 0,01

Opciones:
A) Bus, salida 13:30, vuelta tras el partido · 180 € · fatiga 0,01
B) Bus, salida 11:00, comida en club · 260 € · fatiga 0,00
C) Coche particular · 60 € · fatiga 0,02

[Enter] elegir
```

Para Taburiente:

```
PRÓXIMO PARTIDO: UD Taburiente vs RC Polo · 04/10 · 12:00
Rival: RC Polo → Las Palmas
A) Vuelo BCN-LPA + 2 noches · 7.800 € · fatiga 0,18
B) Vuelo con escala + 1 noche · 6.100 € · fatiga 0,28
C) Vuelo mismo día · 4.900 € · fatiga 0,42 (riesgo alto)
```

---

## 16. Día de partido

### 16.1. Pre-partido

```
CLUB EGARA vs CD TERRASSA
Pla del Bon Aire · 26/09/2026 · 15:00
Superficie: water-based · Clima: sol · 22°C

TU ONCE
...

RIVAL
Formación: 4-3-3 · Presión alta · PC directa
Peligro: Bruno Àvila (PC), Pol Torres (desmarque)
Bajas: ...

[Enter] comenzar partido   [T] táctica   [L] logística
```

### 16.2. Durante el partido

```
CLUB EGARA 1 - 2 CD TERRASSA
12'  PC para Egara. Bruno Àvila saca, Pol Torres para, Àlex Broto tira... ¡parada de Salas!
18'  Gol del CD Terrassa. Borja Soler define cruzado.
...
```

Teclas:

- `Espacio`: siguiente fase.
- `S`: cambiar jugador.
- `T`: ajustar táctica.
- `P`: pausa.
- `F`: estadísticas.

### 16.3. Post-partido

```
RESULTADO: CLUB EGARA 1 - 2 CD TERRASSA
MVP: Borja Soler (8,4)
Goles: Soler (18'), Miró (54') / Àvila (39', PC)
Posesión: 47-53 · PC: 4-3 · Tarjetas: 2-1
Fatiga media: 68% · Lesiones: ninguna

La junta está satisfecha. La afición canta el nombre de Soler.
```

---

## 17. Inbox y decisiones

```
INBOX

[JUNTA] La junta espera el top 6
[PRENSA] Rueda de prensa previa al derbi
[MERCADO] Oferta del RC Polo por Iain McFadden
[MÉDICO] Parte de Víctor Guerra
[AFICIÓN] La afición pide más intensidad

[Enter] abrir   [R] responder   [Esc] volver
```

Las decisiones pueden tener:

- respuesta inmediata;
- efectos en moral, junta, afición o mercado;
- consecuencias diferidas.

---

## 18. Guardado

```
GUARDAR PARTIDA
Nombre: [CD Terrassa - temporada 2026-27]
Ranura: [1]
[G] guardar  [Esc] cancelar
```

Formato:

- SQLite (`manager/saves/<id>.db`).
- JSON de metadatos (`manager/saves/<id>.json`).
- Seed y versión para reproducibilidad.

---

## 19. Accesibilidad

- Texto de alto contraste.
- Sin dependencia de color.
- Tablas legibles en 80 columnas.
- Comandos alternativos por número.
- Modo `--no-color`.
- Guardado automático configurable.

---

## 20. Próximos pasos

1. Implementar el prototipo CLI con dashboard, club, plantilla y partido.
2. Añadir navegación por teclado.
3. Añadir inbox y decisiones.
4. Añadir logística y finanzas.
5. Probar con un club de DHA y uno de DHB.
