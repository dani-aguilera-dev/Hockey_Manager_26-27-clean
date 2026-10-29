# Niveles de liga, medias y fronteras

**Fecha:** 2026-10-28.

## 1. Objetivo

Que un equipo puntero de una categoría inferior no parezca mejor que el último de la categoría superior. La escala se construye de abajo arriba:

```text
DHA 74,8
  ↑
DHB 64,0
  ↑
1ª Andaluza 56,1
  ↑
ligas regionales 52,5–53,8
```

La Superlliga Catalana se trata como una liga regional de primer nivel, entre 1A y DHB: **59,0**.

## 2. Fronteras reales del juego

| Frontera | Equipo superior | Equipo inferior | Diferencia |
|---|---:|---:|---:|
| DHA / DHB | DHA min **67,86** | DHB max **67,53** | -0,33 |
| DHB / 1A | DHB min **60,23** | 1A max **60,22** | -0,01 |
| 1A / regionales | 1A min **53,92** | regional max **53,92–54,17** | ~0,00 |
| 1A / Superlliga | 1A max **60,22** | Superlliga min **58,28** | -1,94 |

El código recorta la media de cada equipo infractor después de generar las plantillas. No se cambian los jugadores ni se inventan nombres: solo se ajusta el nivel del bloque para respetar la frontera.

## 3. Ligas internacionales

La jerarquía se basa en tres señales:

1. **Ranking y resultados de selecciones FIH**: Países Bajos, Bélgica y Alemania ocupan la primera línea; Inglaterra, Argentina e India vienen después.
2. **Prestigio y profundidad de la liga doméstica**: la Hoofdklasse neerlandesa es la referencia europea; la liga belga y la Bundesliga tienen plantillas de primer nivel; la Premier Division inglesa es muy competitiva; el Metropolitano argentino y la Hockey India League concentran talento internacional.
3. **Profesionalización y presencia de internacionales**: no se usa el número de equipos como proxy de nivel.

| Liga | Media objetivo | Motivo |
|---|---:|---|
| Hoofdklasse (NED) | **84,0** | Mejor liga doméstica del mundo y base de la selección neerlandesa. |
| Belgian League (BEL) | **82,0** | Segunda potencia europea; clubes con internacionales de primer nivel. |
| Bundesliga (GER) | **81,0** | Liga alemana muy profunda y campeona del mundo 2026. |
| England Premier Division (ENG) | **79,0** | Liga física, profesionalizada y con clubes históricos. |
| Metropolitano (ARG) | **77,0** | Principal liga argentina; selección top y clubes con tradición. |
| Hockey India League (IND) | **76,0** | Liga de franquicias con internacionales; menor profundidad global que las europeas. |
| DHA (ESP) | **74,8** | Primera española; por debajo de las cinco grandes ligas, por encima de DHB. |
| DHB (ESP) | **64,0** | Segunda española; frontera con 1A en 59,90. |

Las plantillas reales de NED, BEL, GER e IND se calibran en bloque para que la media de la liga coincida con la tabla. Las plantillas generadas de ENG y ARG usan el mismo estándar.

## 4. Fuentes consultadas

- FIH World Rankings y resultados del Mundial 2026: <https://www.fih.hockey/>
- FIH Hockey Pro League: <https://www.fih.hockey/>
- Ranking de ligas domésticas de Ritual Hockey: <https://ritualhockey.com/en-us/blogs/news/top-best-field-hockey-leagues-in-the-world>
- Federaciones y webs de clubes usadas para las plantillas reales: KNHB, RBHA, hockey.de, England Hockey, CAH, Hockey India.

La tabla es una **estimación de diseño** para el simulador, no una clasificación oficial. La fuerza de una liga cambia por temporada y las plantillas reales pueden variar durante el mercado.

## 5. Implementación

- `manager/src/competitions.py`: `LEAGUE_RATING_TARGETS` y `Competition.standard`.
- `manager/src/international.py`: `_calibrate_league_means` para NED, BEL, GER, ENG, ARG e IND.
- `tools/build_attributes_v2.py`: desplazamiento por liga española y recorte por equipo para las fronteras DHA/DHB/1A/regionales.
- `manager/src/ratings.py`: estándares de estrellas relativas alineados con las nuevas medias.

## 6. Efecto en las estrellas

Un 69 en 1A ahora es **4,5★** (antes 5,0★); un 69 en DHB es **3,5★** (antes 4,0★). El mismo jugador sigue siendo más valioso en una categoría inferior, pero la escala ya no comprime DHA, DHB y 1A en el mismo rango.
