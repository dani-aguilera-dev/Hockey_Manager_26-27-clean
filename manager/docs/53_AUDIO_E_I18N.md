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
- El selector está en **Ajustes → Idioma / Language**.
- Persiste en `localStorage` (`hm_lang`) y actualiza
  `document.documentElement.lang`.
- El contenido editorial (noticias, prensa, textos de eventos) sigue en
  español.

Evidencia E2E:

```json
{"i18nEnglish":true,"i18nPersisted":true,"i18nSpanish":true}
```

## Por qué es parcial

Una traducción completa exige extraer cientos de cadenas de las 50+ pantallas
y de los textos generados por el motor. Se ha traducido la capa de navegación
y la guía inicial, que es lo que un usuario necesita para orientarse; el resto
se declara **PASS parcial / FAIL traducción completa** en `docs/48`.
