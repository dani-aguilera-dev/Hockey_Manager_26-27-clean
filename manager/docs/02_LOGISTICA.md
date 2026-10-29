# Logística, viajes y calendario

**Objetivo:** que la logística sea una mecánica central del juego, no un detalle decorativo. Cada desplazamiento tiene coste, tiempo, fatiga y consecuencias deportivas.

---

## 1. Por qué la logística importa en el hockey español

- **Canarias:** la UD Taburiente debe volar a la península para casi todos los partidos. Son dos días de viaje, hotel y fatiga.
- **Cádiz:** San Fernando está lejos de Cataluña y Madrid; los desplazamientos son largos.
- **Cantabria y País Vasco:** distancias medias, pero con calendario congestionado.
- **Clúster catalán:** Terrassa, Sant Cugat, Barcelona, Mataró y Castelldefels están a poca distancia; el bus es suficiente.
- **Clúster madrileño:** RC de Campo, Sanse, Pozuelo, Las Rozas y Giner comparten área metropolitana.
- **Valencia y Alicante:** tren/bus a Madrid y Cataluña.
- **Superficies:** water-based, sand-dressed, sand-filled. Cambian el bote, la velocidad y el riesgo de lesión.

La logística afecta a:

- fatiga y recuperación;
- entrenamientos perdidos;
- moral del grupo;
- presupuesto;
- elección de alineación;
- riesgo de lesión;
- rendimiento en el partido.

---

## 2. Datos de club

Cada club tiene:

```json
{
  "city": "Las Palmas de Gran Canaria",
  "airport": "LPA",
  "train": "No",
  "preferred_mode": "flight",
  "stadium": {
    "surface": "sand-dressed",
    "capacity": 500
  },
  "logistics_notes": "Todos los desplazamientos a la península requieren vuelo y traslado."
}
```

Las ciudades tienen coordenadas para calcular distancias:

```json
{"id":"terrassa","lat":41.563,"lon":2.010,"airport":"BCN","train":"Terrassa"}
```

---

## 3. Cálculo de distancia y modo

### 3.1. Distancia

```
d = 2R * asin(sqrt(
      sin²((lat2-lat1)/2)
    + cos(lat1)*cos(lat2)*sin²((lon2-lon1)/2)
))
```

- `R = 6371 km`.

### 3.2. Modo recomendado

| Condición | Modo |
|---|---|
| Isla (LPA) o distancia > 700 km | Avión |
| 350-700 km y hay tren directo | Tren |
| 80-350 km | Bus |
| < 80 km | Bus / coche |
| Mismo clúster | Bus |

La elección final puede ser manual: el jugador puede pagar más para volar y reducir fatiga, o ahorrar con bus y asumir cansancio.

---

## 4. Coste y fatiga

### 4.1. Coste estimado

```
coste = distancia * coste_km_modo
      + hotel_noches * coste_hotel
      + comidas * coste_comida
      + tasas_aeropuerto (si vuelo)
      + autobús_local
```

Valores de referencia (modelo, no datos reales):

| Concepto | Coste |
|---|---:|
| Bus | 1,20 €/km |
| Tren | 0,18 €/km por jugador (grupo) |
| Avión | 90-180 € por persona |
| Hotel 3* | 70 €/persona/noche |
| Hotel 4* | 110 €/persona/noche |
| Comida | 25 €/persona/día |
| Autobús local | 250 €/día |

### 4.2. Fatiga

```
fatiga_viaje = horas_viaje * 0.06
             + noches_hotel * 0.08
             + (modo == "avión" ? 0.05 : 0)
             + (salida_mismo_día ? 0.10 : 0)
             - recuperacion * 0.05
```

Se expresa en puntos de fatiga (0-1) que se suman a la fatiga del partido.

### 4.3. Pérdida de entrenamiento

| Viaje | Sesiones perdidas |
|---|---|
| < 2 h | 0 |
| 2-4 h | 1 |
| 4-8 h | 1-2 |
| Vuelo + hotel | 2-3 |

### 4.4. Moral

- Un viaje cómodo y bien planificado: +1 moral.
- Un viaje caótico (retraso, hotel malo, llegada tarde): -2 moral.
- Un viaje largo antes de un partido importante: riesgo de -1.

---

## 5. Planificador de viaje

Antes de cada partido fuera de casa, el juego ofrece 2-4 opciones:

| Opción | Coste | Fatiga | Entrenamiento | Riesgo |
|---|---|---|---|---|
| Bus y vuelta el mismo día | Bajo | Alta | 1 sesión | Lesión / mal rendimiento |
| Bus y hotel 1 noche | Medio | Media | 1 sesión | Bajo |
| Tren y hotel 1 noche | Medio | Baja | 1 sesión | Bajo |
| Avión y hotel 1 noche | Alto | Baja | 1-2 sesiones | Bajo |
| Avión y hotel 2 noches | Muy alto | Muy baja | 2 sesiones | Muy bajo |

El jugador elige. El club tiene un presupuesto; gastar de más puede enfadar a la junta; gastar de menos puede costar puntos.

### Ejemplo: Taburiente → Terrassa

- Distancia: ~2.100 km.
- Modo: avión LPA → BCN + bus a Terrassa.
- Duración: 5-6 h puerta a puerta.
- Hotel: 2 noches.
- Coste: 18 personas × (150 € vuelo + 2×90 € hotel + 3×30 € comidas) + 500 € bus ≈ 7.000-8.000 €.
- Fatiga: alta si se viaja el mismo día; media con dos noches.
- Entrenamiento: se pierden 2 sesiones.
- Consecuencia: el equipo canario suele rotar y salir más conservador.

### Ejemplo: Terrassa → Barcelona

- Distancia: ~30 km.
- Modo: bus.
- Duración: 45 min.
- Hotel: 0.
- Coste: ~200 €.
- Fatiga: mínima.
- Entrenamiento: no se pierde.

---

## 6. Logística de partido en casa

No todo es viaje. En casa hay que gestionar:

- **Campo:** preparación, riego, superficie, iluminación.
- **Taquilla:** aforo, precios, socios, invitados.
- **Seguridad:** personal, protocolo, aforo.
- **Hostelería:** comida, bebida, palco.
- **Voluntarios:** personas necesarias.
- **Árbitros:** desplazamiento y honorarios.
- **Prensa:** sala, wifi, acreditaciones.
- **Médicos:** ambulancia, fisio, botiquín.
- **Equipación:** lavandería, material, sticks, bolas.

Cada partido en casa genera ingresos y gastos. Un club con estadio grande y buena afición puede financiar mejor los viajes.

---

## 7. Calendario y congestión

- DHA: 22 jornadas + Final Four + playout.
- DHB: 22 partidos + Final Four.
- Algunas jornadas se acumulan con Copa o aplazamientos.
- El juego debe avisar de:

  - 3 partidos en 8 días;
  - viaje largo entre dos partidos;
  - jugadores con fatiga alta;
  - riesgo de lesión.

### Regla de descanso

```
días_descanso = fecha_partido - fecha_partido_anterior
fatiga_extra = max(0, 4 - días_descanso) * 0.05
```

---

## 8. Clima y superficie

### Clima

| Clima | Efecto |
|---|---|
| Sol | Normal |
| Lluvia | Bola más rápida, más errores, resbalones |
| Viento | Aerial y pases largos más difíciles |
| Calor | Fatiga +10-20% |
| Frío | Menos fatiga, más rigidez |

### Superficie

| Superficie | Efecto |
|---|---|
| Water-based | Bola rápida, menos lesiones, más técnica |
| Sand-dressed | Intermedia |
| Sand-filled | Bola más lenta, más desgaste |
| Natural | Irregular, más lesiones |

La familiaridad con la superficie da una pequeña ventaja local.

---

## 9. Impacto en la gestión

La logística obliga a elegir:

- **Rotar** antes de un viaje largo.
- **Reservar** jugadores para el partido importante.
- **Invertir** en un hotel mejor o en un vuelo directo.
- **Ahorrar** en viajes para fichar.
- **Priorizar** la liga o la Copa.
- **Gestionar** la moral de los que no viajan.

Un club canario necesita planificación a largo plazo; un club catalán puede rotar menos y entrenar más.

---

## 10. Implementación

### Archivos

- `manager/data/cities.json`: coordenadas y hubs.
- `manager/data/clubs.json`: ciudad, aeropuerto, modo preferido.
- `manager/src/logistics.py`: distancia, coste, fatiga, opciones.
- Tabla `travel_plans` en SQLite.

### Funciones

```python
def haversine_km(a, b): ...
def recommend_mode(distance_km, has_train, is_island): ...
def travel_options(club, rival, date, squad_size): ...
def travel_cost(option, squad_size): ...
def travel_fatigue(option, player): ...
def apply_travel_effects(state, option): ...
```

### Salida de ejemplo

```
PRÓXIMO PARTIDO: UD Taburiente vs RC Polo
Sede: Siete Palmas (Las Palmas)
Viaje del rival: RC Polo → Las Palmas
  Opción A: vuelo directo BCN-LPA + hotel 2 noches · 7.800 € · fatiga 0.18
  Opción B: vuelo + escala + hotel 1 noche · 6.100 € · fatiga 0.28
  Opción C: vuelo el mismo día · 4.900 € · fatiga 0.42 (riesgo alto)
```

---

## 11. Balance

La logística no debe ser un impuesto imposible. Objetivos:

- Un club medio de DHA dedica 8-15% de su presupuesto a viajes.
- Un club canario puede llegar al 20-30%.
- La fatiga de viaje debe notarse, pero no decidir todos los partidos.
- El jugador debe poder elegir entre coste y rendimiento.

Se calibrará con simulaciones de temporada completa.

---

## 12. Próximos pasos

1. Implementar `logistics.py` con distancias y opciones.
2. Integrar viajes en el calendario semanal.
3. Añadir fatiga de viaje al motor de partido.
4. Añadir coste de viaje a las finanzas.
5. Probar una temporada con Taburiente y San Fernando.
