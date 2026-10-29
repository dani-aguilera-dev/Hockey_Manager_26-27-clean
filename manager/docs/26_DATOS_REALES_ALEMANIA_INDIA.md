# Datos reales de Alemania e India

**Estado:** integrado (2026-10-22).

## 1. Cobertura

| Liga | Clubes | Jugadores reales | Fotos locales | Escudos |
|---|---:|---:|---:|---:|
| 1. Feldhockey Bundesliga Herren | 12 | 318 | 318 | 12 |
| Hockey India League | 8 | 158 | 158 | 8 |

Las plantillas sustituyen a las generadas en las partidas nuevas de `GER` e
`IND`. Las partidas antiguas conservan sus datos.

## 2. Fuentes

### Alemania

Fuente principal: **Hockey Bundesliga / hockeybundesliga.de**, la web oficial
de la liga.

- Clubes: `https://www.hockeybundesliga.de/club/...`
- Plantilla 2026-27: página `1. Feldhockey Bundesliga Herren 26/27` de cada
  club, pestaña `Kader`.
- Fotos: retratos oficiales publicados en la ficha de cada jugador.
- Escudos: logo oficial del club en la cabecera del equipo.

Se descargaron 318 jugadores y 12 escudos. La liga alemana no publica la
demarcación en la ficha de plantilla; las posiciones se estiman por el orden
de la convocatoria y se marcan como tales en el modelo.

### India

Fuente principal: **Hockey India League**, web oficial.

- Equipos: `https://hockeyindialeague.com/teams/{equipo}/male`
- Plantillas: sección de jugadores por posición (Goalkeeper, Defender,
  Midfielder, Forward).
- Fotos: retrato oficial de cada jugador.
- Escudos: logo oficial de la franquicia.

Se descargaron 158 jugadores y 8 escudos. En India sí se usa la posición
publicada por la liga.

## 3. Limitaciones

- Alemania: posiciones estimadas; la fuente solo publica nombre y foto.
- India: liga corta de franquicias, no una liga nacional de clubes con
  pirámide.
- Las valoraciones (overall, atributos y estrellas) son estimaciones del
  modelo, no datos oficiales.
- Fotos y escudos pertenecen a sus clubes, ligas o autores. Para distribución
  pública hace falta permiso o material con licencia.

## 4. Archivos

```text
manager/data/international_real.json
manager/data/international.json
manager/src/international.py
manager/web/static/crests/ger-*.png
manager/web/static/crests/ind-*.png
jugadores/international/GER/*
jugadores/international/IND/*
```

## 5. Pruebas

- Las plantillas de GER e IND tienen al menos 18 jugadores.
- Todas las fotos referenciadas existen.
- Cada club tiene escudo local.
- Las ligas siguen siendo jugables, guardables y multi-temporada.

Resultado actual: **80 tests superados**.
