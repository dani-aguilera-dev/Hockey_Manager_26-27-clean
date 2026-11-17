# CI y calidad

El workflow de CI está preparado en `docs/ci_workflow.yml`.

## Por qué no está activo

El token OAuth usado para publicar el repositorio no tiene el scope `workflow`
de GitHub. GitHub rechaza cualquier push que cree o modifique
`.github/workflows/*.yml` sin ese permiso.

## Cómo activarlo

Con un token que tenga scope `workflow`:

```bash
mkdir -p .github/workflows
cp docs/ci_workflow.yml .github/workflows/ci.yml
git add .github/workflows/ci.yml
git commit -m "Activa CI"
git push
```

El workflow ejecuta:

- `ruff check src web`
- `python -m pytest src/tests -q --cov=src --cov=web --cov-report=term`
- `npm ci`
- `npm run build`

Cobertura local: 74% global con CLI legacy, 83% del núcleo web. Detalle en
`docs/51_COBERTURA_Y_E2E.md`.

## Gates locales ya verificados

```text
ruff check src web
All checks passed!

python3 -m pytest src/tests -q
351 passed
```

## Persistencia

Los saves nuevos se guardan comprimidos con zlib. La base de datos pasó de
**1,3 GB a 198 MB** con 190 partidas, manteniendo `PRAGMA integrity_check = ok`.

```bash
python3 scripts/compact_saves.py
python3 scripts/prune_saves.py --keep 50 --apply
```
