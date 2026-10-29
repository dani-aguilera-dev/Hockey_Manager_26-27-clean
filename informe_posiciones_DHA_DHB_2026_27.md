# Posiciones de los jugadores de DHA y DHB 2026-27

## Investigación, fuentes y cobertura

**Fecha de cierre:** 19/10/2026  
**Alcance:** 976 perfiles de DHA, DHB y 1ª Andaluza (Club Hockey San Fernando)  
**Objetivo:** asignar una posición a todos los jugadores y distinguir claramente entre posición oficial y posición estimada.

---
> **Actualización 19/10/2026:** el proyecto incorpora un modelo de **37 atributos** y **cinco overalls posicionales**. La posición base sigue siendo la de este informe, pero la valoración del jugador ya no depende de los goles: un central con muchos goles sigue siendo central. La subposición Central/Lateral se estima cuando la fuente solo indica "Defensa". Ver [`docs/02_MODELO_ATRIBUTOS.md`](docs/02_MODELO_ATRIBUTOS.md).

> **Actualización de cobertura (19/10/2026):** se han añadido posiciones desde Diari de Terrassa, Mundo Deportivo, EuroHockey, Global Sports Archive, CAH, 8SPORTS.es, Canarias7 y University of Pretoria. La cobertura oficial pasa a **175 perfiles** (17,9%) y los estimados bajan a **801** (82,1%). Cambios destacados: Jan Clapés (Club Egara) a defensa, Bruno Font (Junior FC) a medio, Ricardo Sánchez (RC de Campo) a defensa pese a sus 30 goles y Joaquín Kruger (Sanse) a medio. Las tablas de este informe ya reflejan estas cifras.


## Resumen ejecutivo

- **976 perfiles** con posición asignada.
- **175 posiciones oficiales** (17,9%): proceden de webs de clubes, actas de la RFEH y prensa.
- **801 posiciones estimadas** (82,1%): calculadas por rol y peso goleador de cada jugador dentro de su equipo.
- **72 porteros** identificados, en su mayoría a partir de las actas oficiales de la RFEH.
- Distribución: **400 defensas, 242 medios, 253 delanteros, 75 porteros y 6 mixtos**.

La conclusión principal es que **no existe una fuente pública completa de posiciones para todos los jugadores de DHA y DHB**. La RFEH publica plantillas, edades y goles, pero no la posición. Por eso el proyecto combina tres capas: datos oficiales de clubes, porteros oficiales de las actas y estimación por rol y goles para el resto.

---

## 1. Fuentes utilizadas

### 1.1. Webs oficiales de clubes

| Club | Jugadores con posición | Fuente |
|---|---:|---|
| Atlètic Terrassa HC | 18 | https://athc.cat/divisio-dhonor-masculi/ |
| Club Egara (DHA) | 18 | https://egara.es/divisio-dhonor-masculi-3/ |
| Egara 1935 (DHB) | 15 | https://egara.es/divisio-dhonor-masculi-b/ |
| RC Polo (DHA) | 17 | https://hockeyteams.rcpolo.com/teams/dhma |
| CD Terrassa | 3 | Prensa: Diari de Terrassa (Pere Jufresa, Iain McFadden, Víctor Guerra, Carlos Bultà) |

Las webs de Atlètic Terrassa y Club Egara publican la plantilla con posiciones en catalán: **Porter, Defensa, Migcampista, Davanter**. Se han traducido a **Portero, Defensa, Medio, Delantero**. La web de RC Polo usa una API pública con posiciones en español y también aporta dorsales, año de nacimiento y biografía.

### 1.2. Actas oficiales de la RFEH

Se han descargado y procesado **562 actas oficiales** de partidos de DHA y DHB de las temporadas 2025-26 y 2026-27. En el PDF del acta, la columna **P** identifica al portero y la columna **J** al jugador de campo. Se han extraído **75 nombres de porteros**, de los que 72 se han podido cruzar con los perfiles actuales.

Esta es la fuente más fiable para la posición de portero, porque procede del acta oficial del partido. No distingue defensa, medio o delantero.

### 1.3. Prensa y crónicas

La crónica de Diari de Terrassa sobre el CD Terrassa 2026-27 identifica a:
- **Pere Jufresa** como portero.
- **Iain McFadden** como defensor.
- **Víctor Guerra** como defensor.
- **Carlos Bultà** como migcampista.

Se han incorporado como posiciones oficiales de prensa.

### 1.4. Estimación por rol y goles

Para los jugadores sin fuente oficial se usa un modelo transparente:
1. Se toman los goles de iSquad como proxy de participación ofensiva.
2. Dentro de cada equipo, se calcula el percentil de goles de cada jugador.
3. Se asigna:
   - **Delantero** al 30% con más goles.
   - **Medio** al 35% intermedio.
   - **Defensa** al 35% con menos goles.
4. Los porteros oficiales se excluyen de esta distribución.
5. La confianza es **Media** si el percentil es extremo (≥0,80 o ≤0,20) y **Baja** en el resto. Los invitados siempre tienen confianza Baja.

**Limitación:** es una estimación, no una posición real. Un defensa con mucho gol puede aparecer como delantero, y un medio con pocos goles puede aparecer como defensa. Sirve para que el juego tenga una distribución coherente, no para un informe profesional. El modelo de atributos posterior separa la posición de los goles y evita que un central goleador se valore como delantero.

---

## 2. Cobertura

### 2.1. Por fuente

| Fuente | Perfiles | % |
|---|---:|---:|
| Estimada por rol y goles | 801 | 82,1% |
| Acta oficial RFEH (porteros) | 64 | 6,6% |
| Web oficial Club Egara | 33 | 3,4% |
| Web oficial Atlètic Terrassa | 18 | 1,8% |
| Web oficial RC Polo | 17 | 1,7% |
| Prensa (Diari de Terrassa) | 6 | 0,6% |
| Mundo Deportivo (selección 2025) | 4 | 0,4% |
| EuroHockey (selección sub-21) | 3 | 0,3% |
| Global Sports Archive | 2 | 0,2% |
| Diari de Terrassa | 2 | 0,2% |
| Canarias7 | 1 | 0,1% |
| Confederación Argentina de Hockey | 1 | 0,1% |
| 8SPORTS.es | 1 | 0,1% |
| University of Pretoria | 1 | 0,1% |
| Deporte de la Isla | 19 | 1,9% |
| Deporte Alicante | 1 | 0,1% |
| El Castillo de San Fernando | 1 | 0,1% |
| Web oficial CD Giner de los Ríos | 1 | 0,1% |
| **Total** | **976** | **100%** |

### 2.2. Por liga

| Liga | Oficiales | Estimadas | Total |
|---|---:|---:|---:|
| DHA | 103 | 309 | 412 |
| DHB | 68 | 468 | 536 |
| 1ª Andaluza | 4 | 24 | 28 |
| **Total** | **175** | **801** | **976** |

### 2.3. Distribución de posiciones

| Posición | Perfiles |
|---|---:|
| Defensa | 400 |
| Delantero | 253 |
| Medio | 242 |
| Portero | 75 |
| Medio/Delantero | 4 |
| Defensa/Medio | 2 |

### 2.4. Cobertura por equipo

| Liga | Equipo | Total | Oficiales | Estimadas | Porteros |
|---|---|---:|---:|---:|---:|
| DHA | Atlètic Terrassa HC | 28 | 18 | 10 | 2 |
| DHA | CD Terrassa Hockey | 38 | 8 | 30 | 3 |
| DHA | CH Carpesa | 32 | 3 | 29 | 3 |
| DHA | Club Egara | 51 | 21 | 30 | 3 |
| DHA | FC Barcelona | 26 | 1 | 25 | 1 |
| DHA | Junior FC | 35 | 9 | 26 | 5 |
| DHA | RC Polo | 40 | 19 | 21 | 4 |
| DHA | Real Club de Campo | 33 | 8 | 25 | 3 |
| DHA | RS Tenis | 33 | 4 | 29 | 4 |
| DHA | Sanse Complutense | 43 | 5 | 38 | 4 |
| DHA | Sardinero HC | 33 | 3 | 30 | 3 |
| DHA | UD Taburiente | 20 | 4 | 16 | 2 |
| DHB | AD Rimas | 34 | 1 | 33 | 1 |
| DHB | Aticos CH San Fernando | 37 | 16 | 21 | 2 |
| DHB | Castelldefels HC | 26 | 1 | 25 | 1 |
| DHB | CD Giner de los Ríos | 28 | 3 | 25 | 2 |
| DHB | CHM Las Rozas | 39 | 2 | 37 | 2 |
| DHB | Egara 1935 | 48 | 16 | 32 | 2 |
| DHB | HC Sant Cugat | 28 | 3 | 25 | 3 |
| DHB | Iluro HC | 25 | 1 | 24 | 1 |
| DHB | Línia 22 | 27 | 7 | 20 | 7 |
| DHB | Pedralbes HC | 29 | 2 | 27 | 2 |
| DHB | Pozuelo | 36 | 1 | 35 | 1 |
| DHB | RC Jolaseta | 32 | 4 | 28 | 3 |
| DHB | Real Sociedad 1927 | 42 | 2 | 40 | 2 |
| DHB | SPV | 34 | 3 | 31 | 3 |
| DHB | UA-San Vicente | 40 | 3 | 37 | 2 |
| DHB | Vallès Esportiu | 31 | 3 | 28 | 2 |
| 1ª And. | San Fernando | 28 | 4 | 24 | 2 |

**Lectura:** la cobertura oficial es alta en Atlètic Terrassa, Club Egara, Egara 1935 y RC Polo. CD Terrassa, Junior FC, RC de Campo, Sanse y Taburiente han mejorado gracias a la prensa local, la selección y bases de datos especializadas. En el resto, la posición oficial se limita al portero identificado en actas. En la 1ª Andaluza no hay fuente oficial y todas las posiciones son estimadas.

---

## 3. Integración en el juego

El juego HTML incorpora:

- **Columna “Pos.”** en la tabla de jugadores.
- **Filtro de posición**: Portero, Defensa, Medio, Delantero y Mixtos.
- **Etiqueta “est.”** en las posiciones estimadas.
- **Ficha del jugador** con posición, fuente y confianza.
- **Plantilla del equipo** con columna de posición.
- **Nota de cobertura** en la vista de jugadores: “175 posiciones oficiales · 801 estimadas por rol y goles”.

Las posiciones oficiales se muestran sin “est.”; las estimadas llevan “est.” y confianza Baja o Media.

---

## 4. Limitaciones

1. **No hay una fuente pública completa.** La RFEH no publica la posición en la plantilla de iSquad.
2. **La estimación por goles no distingue posiciones reales.** Un defensa ofensivo o un medio goleador pueden quedar clasificados como delanteros.
3. **Las actas identifican porteros, no defensas/medios/delanteros.**
4. **Las plantillas de los clubes pueden estar desactualizadas.** Algunos jugadores han cambiado de equipo o han dejado la liga; se han descartado las coincidencias débiles.
5. **Los nombres pueden variar** (Quim/Joaquim, Xavi/Xavier, Pepe/Josep, Ton/Anton). Se ha usado normalización y un diccionario de apodos.
6. **La 1ª Andaluza no tiene fuente oficial** y sus 28 perfiles son estimados.
7. **La posición es una foto fija a 19/10/2026.** Puede cambiar con fichajes, lesiones o cambios tácticos.

---

## 5. Recomendaciones

1. **Ampliar las webs de clubes** con plantillas y posiciones: FC Barcelona, Real Club de Campo, Junior FC, Sanse Complutense, RS Tenis, Sardinero HC, UD Taburiente, CH Carpesa y los clubes de DHB.
2. **Usar las actas de todos los partidos** para confirmar porteros y detectar cambios.
3. **Añadir una posición secundaria** para jugadores polivalentes (Defensa/Medio, Medio/Delantero).
4. **Cruzar con FIH/EHL** para internacionales.
5. **Revisar manualmente** los jugadores con más goles y posición estimada de defensa, y los defensas con muchos goles.
6. **Actualizar la posición** al inicio de cada temporada.

---

## 6. Archivos generados

- **Juego HTML actualizado:** `/home/daniel/hockey_espana/juego_hockey/index.html`
- **Excel con posiciones:** `/home/daniel/hockey_espana/equipos_hockey_hierba_espana_masculino_2026_27_con_posiciones.xlsx`
- **CSV de posiciones:** `/home/daniel/hockey_espana/jugadores_posiciones_2026_27.csv`
- **Este informe:** `/home/daniel/hockey_espana/informe_posiciones_DHA_DHB_2026_27.md`

---

## 7. Fuentes

- Atlètic Terrassa HC – plantilla DHA masculina: https://athc.cat/divisio-dhonor-masculi/
- Club Egara – plantilla DHA masculina: https://egara.es/divisio-dhonor-masculi-3/
- Club Egara – plantilla DHB masculina (Egara 1935): https://egara.es/divisio-dhonor-masculi-b/
- RC Polo – equipo DHA masculino: https://hockeyteams.rcpolo.com/teams/dhma
- RFEH – actas oficiales: https://resultadoshockey.isquad.es/
- RFEH – plantillas iSquad: https://resultadoshockey.isquad.es/equipo.php
- Diari de Terrassa – crónica del CD Terrassa 2026-27: https://www.diarideterrassa.com/esports/comenca-la-lliga-de-hockey-el-cd-terrassa-masculi-vol-creixer-sense-oblidar-don-ve.html
