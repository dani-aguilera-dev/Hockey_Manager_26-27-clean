# Audio e idioma

## Audio del partido

`web/frontend/src/lib/matchAudio.ts` genera el ambiente con Web Audio, sin
samples externos ni licencias que revisar:

- **Ambiente:** ruido filtrado en bucle, volumen bajo.
- **Silbato:** dos tonos con envolvente para faltas, tarjetas, PC, protestas y
  juego peligroso.
- **Golpe:** ráfaga de ruido con filtro de banda para tiros, PC, stroke,
  paradas y entradas al círculo.
- **Gol:** ruido de celebración más silbato.

El audio está **apagado por defecto**. El botón “Ambiente off/on” del partido
en directo lo activa con un gesto del usuario y guarda la preferencia en
`localStorage` (`hm_audio`).

Evidencia E2E:

```json
{"momentum":"0","audioToggle":true}
```

Límites: no hay mezcla por pistas ni ducking, y no se ha hecho una escucha
manual en todos los dispositivos. Es ambiente procedural, no comentario de voz.

## Idioma

`web/frontend/src/lib/i18n.tsx` añade un contexto de idioma `es`/`en`:

- Traduce la navegación completa (45 enlaces), los títulos de grupo, la barra
  superior, la navegación móvil y la guía “Tu primera semana”.
- Traduce las pantallas principales: **plantilla, mercado, táctica, previa,
  informe del partido, ajustes, jugador, equipo, entrenamiento, finanzas,
  junta, noticias, prensa y trabajo**, incluidas etiquetas, botones, filtros,
  estados vacíos y textos de ayuda.
- El selector está en **Ajustes → Idioma / Language**.
- Persiste en `localStorage` (`hm_lang`) y actualiza
  `document.documentElement.lang`.
- El contenido editorial (noticias, prensa, textos de eventos) sigue en
  español.

Evidencia E2E:

```json
{"i18nEnglish":true,"i18nPersisted":true,"i18nSpanish":true}
```

Suite específica de las pantallas principales:

```bash
npm run test:e2e:i18n
```

```json
{"options":true,"squad":true,"market":true,"tactics":true,"match":true,"report":true,"player":true,"team":true,"training":true,"finance":true,"board":true,"news":true,"press":true,"jobs":true,"spanishRestored":true,"ok":true,"suite":"i18n","ms":14396}
```

## Por qué es parcial

Una traducción completa exige extraer cientos de cadenas de las 50+ pantallas
y de los textos generados por el motor. Se han traducido la navegación, la
guía inicial y catorce pantallas principales; el resto de pantallas y los
textos editoriales/datos siguen en español. Se declara **PASS parcial / FAIL
traducción completa** en `docs/48`.
