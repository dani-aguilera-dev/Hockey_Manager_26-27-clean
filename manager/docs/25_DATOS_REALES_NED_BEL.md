# Datos reales de Países Bajos y Bélgica

**Estado:** integrado (2026-10-22).

## 1. Cobertura

| Liga | Clubes | Jugadores reales | Fotos locales | Escudos |
|---|---:|---:|---:|---:|
| Tulp Hoofdklasse Heren | 12 | 233 con foto + 13 altas de Schaerweijde sin foto | 233 | 12 |
| Belgian Hockey League | 12 | 241 | 241 | 12 |

Los datos sustituyen a las plantillas generadas de `NED` y `BEL` en las
partidas nuevas. Las partidas antiguas conservan sus plantillas.

## 2. Fuentes

### Bélgica

Fuente principal: **Carlsberg 0.0 Hockey League**, web oficial de la liga.

- Clubes: `https://carlsberg00hockeyleague.be/clubs/...`
- Plantillas masculinas: sección `Men` de cada club.
- Ficha de jugador: `https://carlsberg00hockeyleague.be/players/...`
- Datos usados: nombre, dorsal, fecha de nacimiento, nacionalidad, posición y
  fotografía.
- Escudos: imagen oficial del club publicada en su ficha de liga.

Se descargaron 241 fichas de jugador y 12 escudos. La web incluye también
cuerpo técnico y jugadoras; el importador filtra únicamente jugadores
masculinos por posición.

### Países Bajos

Fuente principal: **KNHB / hockey.nl** para la competición y los escudos, y las
webs oficiales de los clubes para plantillas y fotos.

- Competición y escudos: `https://www.hockey.nl/match-center` y API pública del
  Match Center (`app.hockeyweerelt.nl`).
- Amsterdam: `https://www.ahbc.nl/heren-1`
- Bloemendaal: `https://www.hcbloemendaal.nl/heren-1`
- Den Bosch: `https://www.hcdenbosch.nl/heren-1`
- HDM: `https://www.hdmonline.nl/index.php?page=selectie_H1&sid=1`
- Kampong: `https://www.kamponghockey.nl/heren-1`
- Klein Zwitserland: `https://www.kleinzwitserlandheren1.nl/player-profile/`
- Oranje-Rood: `https://www.hcoranje-rood.nl/heren-1---26/27`
- Pinoké: `https://www.pinoke.nl/heren-1`
- Rotterdam: `https://www.hcrotterdam.com/heren-1`
- SCHC: `https://www.schc.nl/heren-1`
- Schaerweijde: `https://www.schaerweijde-hockey.nl/heren-1`
- Tilburg: `https://www.hctilburg.com/h01-tulp-hoofdklasse-heren`

## 3. Limitaciones conocidas

- **HDM:** su página de selección publicada sigue siendo la de 2025-26. Se usa
  como base real, no como plantilla inventada, hasta que el club publique la
  2026-27.
- **Schaerweijde:** la web no publica una plantilla completa. Se incorporaron
  las altas y nombres públicos de 2026-27; el resto se completa con jugadores
  generados. No hay fotos de esos 13 nombres en la fuente oficial.
- **Posiciones:** se usan las que publica el club. En clubes que solo publican
  nombre, dorsal y foto, la posición se estima por orden de plantilla. Es una
  limitación de la fuente, no un dato oficial.
- **Valoraciones:** el overall y los atributos son una estimación del modelo a
  partir del nivel de liga y la posición. No son valoraciones oficiales.
- **Fotos:** algunas páginas usan la misma foto de equipo o una foto antigua.
  Se conserva la imagen publicada por el club.

## 4. Licencia y uso

Los escudos y las fotografías son propiedad de los clubes, la liga o sus
autores. Se han descargado para este proyecto personal/educativo y se citan las
fuentes. Para distribuir el juego públicamente o subirlo a una tienda hace falta
permiso expreso o sustituirlos por material con licencia.

## 5. Archivos

```text
manager/data/international_real.json
manager/data/international.json
manager/src/international.py
manager/web/static/crests/ned-*.jpg|png
manager/web/static/crests/bel-*.jpg|png|jpeg
jugadores/international/NED/*
jugadores/international/BEL/*
```

## 6. Pruebas

- Las plantillas reales tienen al menos 18 jugadores.
- Las fotos referenciadas existen en `jugadores/`.
- Cada club de NED y BEL tiene un escudo local.
- Las ligas siguen siendo jugables y guardables.
- Los tests españoles no se ven afectados.

Resultado actual: **80 tests superados**.
