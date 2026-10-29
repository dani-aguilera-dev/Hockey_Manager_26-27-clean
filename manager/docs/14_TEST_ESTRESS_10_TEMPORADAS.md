# Test de estrés: 10 temporadas con mercado y retiros

**Fecha:** 2026-10-21.
**Club:** CD Terrassa Hockey.
**Semilla:** 9182.
**Motor:** Python + SQLite, sin servidor.
**Alcance:** 10 temporadas completas, entrenamiento automático, mercado de verano e invierno, agentes libres, Copa, EHL, DHB de dos fases, retiradas y multi-temporada.

---

## 1. Resultado general

- **10 temporadas simuladas:** 2026-27 → 2035-36.
- **Sin errores ni excepciones.**
- **41 movimientos de mercado registrados.**
- **29 retiradas registradas.**
- DHA y DHB mantuvieron **12 y 16 equipos**.
- Ningún equipo quedó por debajo de 18 jugadores.
- Tiempo de ejecución: **105,4 segundos**.

### Trayectoria del usuario

| Temporada | Liga | Posición |
|---|---|---:|
| 2026-27 | DHA | 10º |
| 2027-28 | DHA | 3º |
| 2028-29 | DHA | 9º |
| 2029-30 | DHA | 10º |
| 2030-31 | DHA | 9º |
| 2031-32 | DHA | 6º |
| 2032-33 | DHA | 5º |
| 2033-34 | DHA | 9º |
| 2034-35 | DHA | 8º |
| 2035-36 | DHA | 9º |

### Campeones

- DHA: UD Taburiente (2), Atlètic Terrassa, Real Sociedad 1927 (2), Real Club de Campo, Club Egara (2), Aticos San Fernando, SPV.
- Copa: UD Taburiente, Sanse Complutense, Real Club de Campo, Junior FC, Egara 1935, Aticos San Fernando, Real Sociedad 1927 (2), Atlètic Terrassa.
- EHL: UD Taburiente, Rot-Weiss Köln (3), SV Kampong (2), HC Bloemendaal (2), Royal Léopold, THC Hurley.

---

## 2. Fichajes más caros

| Temporada | Jornada | Jugador | OVR | Desde | Hacia | Precio |
|---|---:|---|---:|---|---|---:|
| 2026-27 | 12 | Lucas Gabriel Martini Menazzi | 85,3 | RC Jolaseta | Atlètic Terrassa | 446.250 € |
| 2026-27 | 1 | Alejandro Peña Martín | 85,9 | SPV | Club Egara | 408.000 € |
| 2026-27 | 1 | Ángel Sáenz de Santa María | 72,0 | RS Tenis | CD Terrassa | 382.500 € |
| 2026-27 | 1 | Biel Roca Durán | 71,0 | AD Rimas | RC Polo | 382.500 € |
| 2026-27 | 1 | Marco Moretto | 81,5 | Junior FC | Real Club de Campo | 364.594 € |
| 2027-28 | 1 | Alejandro Peña Martín | 85,9 | Club Egara | Junior FC | 318.750 € |
| 2028-29 | 1 | Pere Moran Marqués | 73,3 | Egara 1935 | Real Club de Campo | 263.845 € |
| 2035-36 | 1 | Álvaro Fuentes Lacal | 70,8 | Club Egara | Sanse Complutense | 153.000 € |
| 2026-27 | 12 | Mario Álvarez-Villabol Navarro | 90,4 | Pozuelo | UD Taburiente | 114.750 € |
| 2027-28 | 1 | Héctor Rodríguez Codejón | 83,9 | SPV | Sardinero | 89.250 € |

### Lectura

- El mercado ya mueve estrellas por encima de **400.000 €**.
- Alejandro Peña se movió dos veces: SPV → Egara → Junior.
- Mario Álvarez-Villabol (90,4) salió por 114.750 € porque el club comprador tenía un presupuesto bajo en la simulación; su valor de mercado era mayor.
- El club del usuario fichó a Ángel Sáenz por 382.500 €.
- Varios jugadores de DHB dieron el salto a DHA.

---

## 3. Agentes libres relevantes

| Temporada | Jugador | OVR | Destino |
|---|---|---:|---|
| 2026-27 | Álvaro Romero Cornejo | 80,8 | Real Club de Campo |
| 2026-27 | José María Arriaza Olvera | 78,1 | Sanse Complutense |
| 2027-28 | Jaime Arrieta Fuentes | 77,5 | CH Carpesa |
| 2027-28 | Álvaro Migueles Jiménez | 76,8 | Atlètic Terrassa |
| 2028-29 | Gonzalo Fernández Pérez-Arellano | 76,6 | Real Club de Campo |
| 2028-29 | Isaac Molina Gallego | 73,6 | Real Club de Campo |
| 2029-30 | Carlos Martínez García | 72,6 | HC Sant Cugat |
| 2029-30 | Diego Adrián Fernández Aragón | 72,3 | SPV |

---

## 4. Retiradas

Se registraron **29 retiradas** en 10 temporadas. Algunas destacadas:

| Temporada | Jugador | Club | Edad | OVR |
|---|---|---|---:|---:|
| 2026-27 | Guillermo Nevado Lucía | Pozuelo | 37 | 80,9 |
| 2026-27 | Federico Lionel Monja | Atlètic Terrassa | 34 | 78,8 |
| 2026-27 | José Antonio González Romero | Club Hockey Madrid | 37 | 77,9 |
| 2027-28 | Mario Álvarez-Villabol Navarro | UD Taburiente | 33 | 90,4 |
| 2028-29 | Juan Arronte Cabria | Pozuelo | 33 | 71,7 |
| 2029-30 | Borja Valcárcel-Resalt | CD Giner | 32 | 72,9 |
| 2030-31 | Guillermo Arnal López | HC Sant Cugat | 35 | 73,0 |
| 2031-32 | Héctor Ramón Marcilli Borges | Sanse Complutense | 35 | 72,3 |
| 2034-35 | Alejandro García Montenegro | SPV | 37 | 71,2 |

### Cómo funciona

- Los jugadores envejecen al final de cada temporada.
- La probabilidad de retirada sube con la edad:
  - 31-32 años: baja;
  - 33-34: media;
  - 35-36: alta;
  - 37+: muy alta;
  - 40+: retirada garantizada.
- La retirada se anuncia en el inbox si el jugador es importante o de tu club.
- Aparece en el resumen de temporada.
- Los clubes completan plantilla con canteranos.

---

## 5. Observaciones

### Lo que funciona

- Mercado, contratos, agentes libres y retiradas conviven sin romper plantillas.
- El mercado mueve estrellas por encima de 400.000 €.
- La edad empieza a penalizar el valor de mercado.
- Los equipos mantienen al menos 18 jugadores.
- DHB, Copa, EHL y multi-temporada funcionan durante 10 años.

### Lo que hay que ajustar

1. **Presupuesto del comprador:** un club con poca caja puede pagar menos que el valor de mercado de una estrella.
2. **Salarios:** algunos fichajes tienen salarios muy altos y otros muy bajos.
3. **Mercado IA:** los movimientos del test son directos, no negociaciones completas.
4. **EHL:** se simula, pero no se juega en directo.
5. **DHB → 1ª Andaluza:** no hay descenso porque esa liga no se simula.

---

## 6. Test con el mercado real del juego

Además del test de estrés con movimientos directos, ejecuté otro de 10 temporadas usando las funciones reales del juego:

- `generate_incoming_offers`
- `accept_incoming_offer`
- `make_transfer_offer`

Resultado:

- **17 movimientos registrados** (el mercado real es más selectivo que el test de estrés).
- Venta más cara: **Aleix Vericat Torres**, CD Terrassa → Atlètic Terrassa, **493.896 €**.
- El club del usuario fue campeón de DHA en **2035-36**.
- **34 retiradas** en 10 temporadas.
- Sin errores.

Esto confirma que los clubes IA ya respetan mejor su presupuesto y que las estrellas no se malvenden con tanta facilidad.

## 7. Conclusión

El núcleo aguanta **10 temporadas con mercado, retiradas, Copa, EHL, cantera y DHB**. No hay errores de ejecución.

El siguiente ajuste recomendado es **valorar mejor a las estrellas veteranas** y equilibrar salarios. Después, EHL interactiva y descenso a 1ª Andaluza.
