# Selector de nueva partida por países y divisiones

**Estado:** implementado (2026-10-28).

## Flujo

La pantalla `/app/new` tiene dos niveles:

1. **País:** España, Países Bajos, Bélgica, Alemania, Inglaterra, Argentina e India.
2. **División:** dentro del país seleccionado, cada competición aparece con su logo/escudo, número de clubes y nivel de referencia.

Después se elige el club y se confirma la partida.

## Logos

Los archivos están en `manager/web/static/league-logos/`:

- `es.png` · España (DHA y DHB).
- `es-an.png` · Andalucía (1ª Andaluza).
- `es-pv.png` · Liga Norte (referencia vasca).
- `es-md.png` · Comunidad de Madrid (1ª Madrid).
- `es-ga.png` · Galicia (1ª Galicia).
- `es-cn.png` · Canarias (1ª Canarias).
- `es-vc.png` · Comunidad Valenciana (1ª FHCV).
- `es-ct.png` · Cataluña (Superlliga y Primera Catalana).
- `nl.png`, `be.png`, `de.png`, `gb-eng.png`, `ar.png`, `in.png` · ligas internacionales.

La bandera/escudo de cada división se usa como imagen de referencia de la liga. El selector mantiene el nombre de la competición y el número de clubes para evitar ambigüedades.

## Implementación

- `manager/web/frontend/src/pages/NewGame.tsx`: agrupación por país, pestañas de país y pestañas de división.
- `manager/web/frontend/src/styles.css`: estilos de pestañas, logos y banner de liga.
- `manager/web/static/league-logos/*.png`: imágenes de referencia.

## Pruebas

- La SPA compila con TypeScript y Vite.
- Los assets se sirven desde `/static/league-logos/`.
- El catálogo conserva las 16 competiciones y sus clubes.
