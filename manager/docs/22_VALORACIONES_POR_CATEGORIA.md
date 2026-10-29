# Valoraciones por categoría

**Estado:** implementado (2026-10-22).

## 1. Referencias de Football Manager 24

Football Manager separa dos conceptos:

- **CA / Current Ability:** calidad absoluta actual del jugador.
- **PA / Potential Ability:** techo absoluto de desarrollo.
- **Estrellas:** valoración relativa al club/liga del usuario, no una medida absoluta.

Fuentes consultadas:

- [Sort It Out SI — Current Ability, Potential Ability and Star Ratings in FM24](https://sortitoutsi.net/content/67526/current-ability-potential-ability-and-star-ratings-in-football-manager)
- [FM Dossier — Star Ratings Explained](https://fmdossier.dev/guides/star-ratings-explained)
- [Passion4FM — Star Ratings](https://www.passion4fm.com/football-manager-guide-star-ratings/)
- [FM Scout — Current and Potential Ability Guide](https://www.fmscout.com/a-football-manager-current-and-potential-ability-guide.html)

La conclusión clave: un jugador de 4,5 estrellas en una categoría inferior puede bajar a 3 estrellas al ascender, aunque su calidad absoluta no cambie.

## 2. Modelo del juego

En Hockey Manager:

- `PlayerState.overall` = **CA** absoluto.
- `PlayerState.potential` = **PA** absoluto.
- `PlayerState.league` = categoría en la que compite actualmente.
- `overall` sigue mandando en el motor de partido.
- Las estrellas solo cambian la **lectura contextual** del jugador.

Esto evita falsear el rendimiento: un jugador no se vuelve mejor o peor por cambiar de liga. Lo que cambia es su nivel relativo dentro de esa liga.

## 3. Niveles de categoría

| Categoría | Nivel de referencia | Dispersión |
| --- | ---: | ---: |
| DHA | 72 | 8 |
| DHB | 62 | 8 |
| 1ª Andaluza | 48 | 8 |
| EHL | 86 | 8 |

Fórmula:

```text
estrellas = 3 + (overall - nivel_categoria) / dispersión
```

Se limita a 0,5–5 estrellas y se redondea a media estrella.

## 4. Ejemplos

| Overall | 1ª Andaluza | DHB | DHA |
| ---: | ---: | ---: | ---: |
| 60 | 4,5★ | 3,0★ | 1,5★ |
| 64 | 5,0★ | 3,5★ | 2,0★ |
| 69 | 5,0★ | 4,0★ | 2,5★ |
| 80 | 5,0★ | 5,0★ | 4,0★ |
| 88 | 5,0★ | 5,0★ | 5,0★ |

El potencial usa la misma escala:

```text
potencial 81 en 1ª Andaluza → 5,0★
potencial 81 en DHB → 5,0★
potencial 81 en DHA → 4,0★
```

## 5. Ascensos, descensos y traspasos

- Al ascender o descender un equipo, `sync_player_leagues` actualiza la categoría de todos sus jugadores.
- Al fichar o vender, el jugador recibe la categoría del nuevo club.
- Las estrellas se recalculan automáticamente sin tocar el overall.
- Las partidas antiguas rellenan `player.league` desde su equipo.

## 6. Dónde se ve

- **Plantilla:** estrellas junto al OVR.
- **Ficha de jugador:** OVR absoluto, nivel relativo, potencial y tier.
- **Mercado:** estrellas en la categoría actual y en el informe de ojeador.
- **Perfil de equipo:** columna de nivel en la plantilla.
- **Once probable:** estrellas contextuales.
- **Ficha de mercado:** horquilla de estrellas del ojeador.

## 7. Archivos

```text
manager/src/ratings.py
manager/src/models.py
manager/src/data_loader.py
manager/src/season.py
manager/src/market.py
manager/src/persistence.py
manager/src/tests/test_ratings.py
```

## 8. Pruebas

Se comprueba que:

- un 69 es 5★ en 1ª Andaluza, 4★ en DHB y 2,5★ en DHA;
- el potencial también es relativo;
- los jugadores cargados tienen su liga;
- al cambiar de liga cambian las estrellas;
- los agentes libres de 1ª Andaluza conservan su categoría.

Resultado actual: **80 tests superados**.

## 9. Limitaciones

- Los niveles 72/62/48/86 son **diseño del juego**, no datos oficiales.
- No hay reputación dinámica por temporada; el nivel de categoría es fijo.
- Las estrellas son relativas a la liga, no a la plantilla concreta del club.
- La horquilla del ojeador se sigue calculando desde el overall absoluto.
- El motor de partido usa el overall absoluto, no las estrellas.
