"""Persistencia SQLite de la partida (Fase 1).

El estado completo se guarda como JSON en una tabla `saves`. Es una solución
pragmática para el MVP: permite guardar/cargar sin acoplar la UI al esquema
completo de 41 tablas, que se irá normalizando en fases posteriores.
"""

from __future__ import annotations

import csv
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from .models import GameState, StaffMember
from .runtime import project_root

DEFAULT_DB = project_root() / "manager" / "saves" / "manager.db"


def _connect(path: Path | str = DEFAULT_DB) -> sqlite3.Connection:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS saves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            club_id TEXT NOT NULL,
            season TEXT NOT NULL,
            round INTEGER NOT NULL,
            updated_at TEXT NOT NULL,
            state_json TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def save_game(state: GameState, name: str | None = None, path: Path | str = DEFAULT_DB) -> str:
    name = name or f"{state.user_team.name} · {state.season} · J{state.round}"
    payload = json.dumps(state.to_dict(), ensure_ascii=False, separators=(",", ":"))
    now = datetime.now().isoformat(timespec="seconds")
    conn = _connect(path)
    try:
        conn.execute(
            """
            INSERT INTO saves (name, club_id, season, round, updated_at, state_json)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                club_id=excluded.club_id, season=excluded.season, round=excluded.round,
                updated_at=excluded.updated_at, state_json=excluded.state_json
        """,
            (name, state.club_id, state.season, state.round, now, payload),
        )
        conn.commit()
    finally:
        conn.close()
    return name


def list_saves(path: Path | str = DEFAULT_DB) -> list[dict]:
    conn = _connect(path)
    try:
        rows = conn.execute(
            "SELECT id, name, club_id, season, round, updated_at FROM saves ORDER BY updated_at DESC"
        ).fetchall()
    finally:
        conn.close()
    keys = ["id", "name", "club_id", "season", "round", "updated_at"]
    return [dict(zip(keys, r)) for r in rows]


def _backfill_communities(state: GameState) -> None:
    """Rellena la comunidad en partidas antiguas sin reescribir sus datos."""
    if all(team.community for team in state.teams.values()):
        return
    try:
        from .data_loader import load_clubs

        clubs, _ = load_clubs()
    except Exception:
        return
    for team_id, team in state.teams.items():
        if not team.community:
            team.community = clubs.get(team_id, {}).get("community", "")


def _backfill_media(state: GameState) -> None:
    """Rellena fotos en partidas antiguas creadas antes de guardar media."""
    if not any(not p.photo for t in state.teams.values() for p in t.players) and not any(
        not p.photo for p in state.free_agents
    ):
        return
    try:
        from .data_loader import load_teams

        teams, _, _ = load_teams()
    except Exception:
        return
    by_id: dict[str, tuple[str, str]] = {}
    by_name: dict[tuple[str, str], tuple[str, str]] = {}
    for team in teams.values():
        for player in team.players:
            media = (player.photo, player.photo_remote)
            by_id[player.id] = media
            by_name[(team.name.casefold(), player.name.casefold())] = media
    for team in state.teams.values():
        for player in team.players + team.youth:
            if player.photo:
                continue
            media = by_id.get(player.id) or by_name.get((team.name.casefold(), player.name.casefold()))
            if media:
                player.photo, player.photo_remote = media
    for player in state.free_agents:
        if player.photo:
            continue
        media = by_id.get(player.id) or by_name.get((player.team_name.casefold(), player.name.casefold()))
        if media:
            player.photo, player.photo_remote = media


def _backfill_leagues(state: GameState) -> None:
    """Rellena la categoría de jugadores de partidas anteriores."""
    from .competitions import DEFAULT_REGIONAL_LEAGUE

    for team in state.teams.values():
        for player in team.players + team.youth:
            if not player.league:
                player.league = team.league
    for player in state.free_agents:
        if not player.league:
            player.league = DEFAULT_REGIONAL_LEAGUE


def _backfill_staff(state: GameState) -> None:
    """Añade el cuerpo técnico de iSquad a partidas antiguas."""
    if all(team.staff and any(m.role == "head_coach" for m in team.staff) for team in state.teams.values()):
        return
    path = project_root() / "manager" / "data" / "staff_isquad.json"
    data = {}
    if path.exists():
        try:
            import json

            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    for team in state.teams.values():
        scraped = data.get(team.id, {}).get("staff", [])
        if not scraped:
            continue
        if not any(m.role == "head_coach" for m in team.staff):
            head = next((row for row in scraped if row.get("role") == "head_coach"), None)
            if head:
                team.staff.append(
                    StaffMember(**{k: v for k, v in head.items() if k in StaffMember.__dataclass_fields__})
                )
        if not team.staff:
            team.staff = [
                StaffMember(**{k: v for k, v in row.items() if k in StaffMember.__dataclass_fields__})
                for row in scraped
            ]
    # Los equipos internacionales y las partidas más antiguas pueden no tener
    # un head coach registrado. El juego necesita uno para que el staff sea
    # coherente en todas las ligas.
    for team in state.teams.values():
        if not any(member.role == "head_coach" for member in team.staff):
            team.staff.append(
                StaffMember(
                    role="head_coach",
                    name=f"Entrenador {team.name}",
                    rating=max(50, min(85, team.assistant_rating)),
                    salary=0,
                    source="modelo",
                    confidence="baja",
                )
            )


def _backfill_ratings(state: GameState) -> None:
    """Migra partidas antiguas al modelo de ratings por división."""
    if state.event_flags.get("ratings_v3"):
        return
    from .competitions import DEFAULT_REGIONAL_LEAGUE
    from .data_loader import TOOLS, norm

    path = TOOLS / "player_attributes_v2.csv"
    if not path.exists():
        return
    with path.open(encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    team_rows = {}
    for row in rows:
        key = (str(row.get("equipo", "")).strip(), str(row.get("jugador", "")).strip())
        team_rows[key] = row
    free_rows = {}
    for row in rows:
        if str(row.get("liga", "")).strip() in (DEFAULT_REGIONAL_LEAGUE, "1ª Andaluza"):
            free_rows.setdefault(norm(str(row.get("jugador", "")).strip()), row)
    for team in state.teams.values():
        for player in team.players:
            row = team_rows.get((team.name, player.name))
            if row:
                _apply_rating_row(player, row)
    for player in state.free_agents:
        row = free_rows.get(norm(player.name))
        if row:
            _apply_rating_row(player, row)
    state.event_flags["ratings_v3"] = True


def _apply_rating_row(player, row) -> None:
    try:
        player.overall = float(row.get("overall") or player.overall)
        player.potential = float(row.get("potential") or player.potential)
        player.value = int(float(row.get("value") or player.value))
        player.polivalencia = float(row.get("polivalencia") or player.polivalencia)
    except (TypeError, ValueError):
        pass
    attrs = {}
    for key, value in row.items():
        if key.startswith("attr_"):
            try:
                attrs[key[5:]] = int(float(value or 50))
            except (TypeError, ValueError):
                attrs[key[5:]] = 50
    if attrs:
        player.attributes = attrs
    overalls = {}
    for pos, column in (
        ("Portero", "overall_portero"),
        ("Central", "overall_central"),
        ("Lateral", "overall_lateral"),
        ("Medio", "overall_medio"),
        ("Delantero", "overall_delantero"),
    ):
        try:
            overalls[pos] = float(row.get(column) or 0)
        except (TypeError, ValueError):
            overalls[pos] = 0.0
    if overalls:
        player.overalls = overalls
    for field in ("position_group", "subposicion", "archetype", "perfil"):
        value = row.get(field)
        if value:
            setattr(player, field, str(value))


def _backfill_lower_agents(state: GameState) -> None:
    """Añade agentes libres autonómicos a partidas antiguas sin duplicarlos."""
    from .competitions import DEFAULT_REGIONAL_LEAGUE, REGIONAL_CODES
    from .data_loader import load_lower_division_free_agents, norm

    lower_codes = REGIONAL_CODES - {DEFAULT_REGIONAL_LEAGUE}
    if any(player.league in lower_codes for player in state.free_agents):
        return
    assigned = {norm(player.name) for team in state.teams.values() for player in team.players}
    assigned.update(norm(player.name) for player in state.free_agents)
    for player in load_lower_division_free_agents():
        key = norm(player.name)
        if not key or key in assigned:
            continue
        assigned.add(key)
        player.team_name = "Agente libre"
        state.free_agents.append(player)


def backfill_state(state: GameState) -> GameState:
    """Compatibilidad con partidas guardadas antes de comunidad/fotos."""
    _backfill_communities(state)
    _backfill_media(state)
    _backfill_leagues(state)
    _backfill_staff(state)
    _backfill_ratings(state)
    _backfill_lower_agents(state)
    return state


def load_game(name_or_id: str | int, path: Path | str = DEFAULT_DB) -> GameState:
    conn = _connect(path)
    try:
        if isinstance(name_or_id, int) or str(name_or_id).isdigit():
            row = conn.execute("SELECT state_json FROM saves WHERE id=?", (int(name_or_id),)).fetchone()
        else:
            row = conn.execute("SELECT state_json FROM saves WHERE name=?", (str(name_or_id),)).fetchone()
    finally:
        conn.close()
    if not row:
        raise KeyError(f"No existe la partida: {name_or_id}")
    state = GameState.from_dict(json.loads(row[0]))
    _backfill_communities(state)
    _backfill_media(state)
    _backfill_leagues(state)
    _backfill_staff(state)
    _backfill_ratings(state)
    _backfill_lower_agents(state)
    return state


def delete_save(name_or_id: str | int, path: Path | str = DEFAULT_DB) -> bool:
    conn = _connect(path)
    try:
        if isinstance(name_or_id, int) or str(name_or_id).isdigit():
            cur = conn.execute("DELETE FROM saves WHERE id=?", (int(name_or_id),))
        else:
            cur = conn.execute("DELETE FROM saves WHERE name=?", (str(name_or_id),))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def rename_save(name_or_id: str | int, new_name: str, path: Path | str = DEFAULT_DB) -> str:
    """Renombra una partida sin tocar su estado.

    Devuelve el nombre nuevo. Lanza ``KeyError`` si la partida original no
    existe y ``ValueError`` si el nombre nuevo ya está ocupado.
    """
    new_name = str(new_name or "").strip()
    if not new_name:
        raise ValueError("El nombre nuevo no puede estar vacío.")
    conn = _connect(path)
    try:
        if isinstance(name_or_id, int) or str(name_or_id).isdigit():
            row = conn.execute("SELECT id, name FROM saves WHERE id=?", (int(name_or_id),)).fetchone()
        else:
            row = conn.execute("SELECT id, name FROM saves WHERE name=?", (str(name_or_id),)).fetchone()
        if not row:
            raise KeyError(f"No existe la partida: {name_or_id}")
        save_id, old_name = row
        if old_name == new_name:
            return new_name
        exists = conn.execute("SELECT 1 FROM saves WHERE name=? AND id<>?", (new_name, save_id)).fetchone()
        if exists:
            raise ValueError("Ya existe una partida con ese nombre.")
        now = datetime.now().isoformat(timespec="seconds")
        conn.execute("UPDATE saves SET name=?, updated_at=? WHERE id=?", (new_name, now, save_id))
        conn.commit()
        return new_name
    finally:
        conn.close()


def export_json(state: GameState, path: Path | str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.to_dict(), ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def import_json(path: Path | str) -> GameState:
    state = GameState.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
    _backfill_communities(state)
    _backfill_media(state)
    _backfill_leagues(state)
    _backfill_staff(state)
    _backfill_ratings(state)
    _backfill_lower_agents(state)
    return state
