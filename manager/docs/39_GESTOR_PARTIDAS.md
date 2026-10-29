# Gestor de partidas guardadas

**Estado:** implementado (2026-10-28).

## Acceso

El gestor está disponible desde:

- **Menú principal:** botón `Gestionar partidas`.
- **Partida en curso:** icono de carpeta en la barra superior.
- **Pantalla de carga:** botón `Gestionar`.
- Ruta directa: `/app/saves`.

## Acciones

Cada partida guardada permite:

- **Cargar:** restaura la partida y entra al dashboard.
- **Renombrar:** cambia el nombre sin alterar el estado guardado. El nombre debe ser único.
- **Eliminar:** borra la partida de SQLite después de confirmar. Si es la partida actual, el juego sigue en memoria hasta que se vuelva a guardar.
- **Buscar:** filtra por nombre, club o temporada.

## API

- `GET /api/load` · lista las partidas.
- `PATCH /api/saves` · `{ "name": "...", "new_name": "..." }`.
- `DELETE /api/saves` · `{ "name": "..." }`.

La lógica de persistencia vive en `manager/src/persistence.py` (`rename_save`, `delete_save`). La pantalla React está en `manager/web/frontend/src/pages/SaveManager.tsx`.

## Pruebas

- `test_saves_can_be_renamed_and_deleted` en `test_persistence.py`.
- `test_api_save_manager_rename_and_delete` en `test_api.py`.
