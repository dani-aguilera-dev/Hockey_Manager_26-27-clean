"""Punto de entrada del Hockey Manager (Fase 1)."""

from __future__ import annotations

import argparse
import sys

from .competitions import COMPETITIONS
from .international import load_all_teams
from .persistence import DEFAULT_DB
from .regional import load_regional_teams
from .season import new_game, play_round, season_summary
from .ui import GameUI, money


def auto_season(club_id: str | None, manager: str, seed: int | None) -> int:
    teams, _, _ = load_all_teams()
    regional_teams, _, _ = load_regional_teams()
    teams.update(regional_teams)
    playable = sorted([t for t in teams.values() if t.league in COMPETITIONS], key=lambda t: (t.league, t.name))
    if club_id is None:
        club_id = next(t.id for t in playable if t.league == "DHA")
    if club_id not in teams or teams[club_id].league not in COMPETITIONS:
        print(f"Club no válido: {club_id}")
        print("Clubes disponibles:")
        for t in playable:
            print(f"  {t.id:<24} {t.league:<4} {t.name}")
        return 1
    state = new_game(club_id, manager, seed)
    print(f"Simulando temporada 2026-27 con {state.user_team.name} ({state.competition})...")
    for _ in range(state.total_rounds):
        p = play_round(state, user_lineup_ids=None, travel_option_id="equilibrado")
        if p:
            print(
                f"J{p['round']:>2}: {p['home_name']} {p['home_goals']}-{p['away_goals']} {p['away_name']} · {p['result']}"
            )
    summ = season_summary(state)
    print("\nCLASIFICACIÓN FINAL")
    print(f"{'#':>3}  {'Equipo':<40} {'PJ':>3} {'G':>3} {'E':>3} {'P':>3} {'GF':>3} {'GC':>3} {'DG':>4} {'PTS':>4}")
    for row in summ["table"]:
        print(
            f"{row['position']:>3}  {row['team']:<40} {row['played']:>3} {row['won']:>3} {row['drawn']:>3} {row['lost']:>3} {row['gf']:>3} {row['ga']:>3} {row['gd']:>+4} {row['points']:>4}"
        )
    print(f"\nCampeón: {summ.get('champion')}")
    print(f"Tu posición: {summ.get('user_position')}º/{len(summ.get('table', []))}")
    print("\nMÁXIMOS GOLEADORES")
    for i, sc in enumerate(summ["top_scorers"][:10], 1):
        print(f"{i:>2}. {sc['player']:<38} {sc['team']:<34} {sc['goals']:>3} goles")
    played = [f for f in state.fixtures if f.phase == "regular" and f.played]
    goals = sum(f.home_goals + f.away_goals for f in played)
    print(f"\nPartidos: {len(played)} · Goles: {goals} · Media: {goals / len(played):.2f} por partido")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hockey Manager 2026-27 · DHA, DHB y ligas internacionales")
    parser.add_argument("--auto", action="store_true", help="Simular una temporada completa sin interacción")
    parser.add_argument("--club", help="ID del club DHA (ej. cd-terrassa)")
    parser.add_argument("--manager", default="Entrenador", help="Nombre del entrenador")
    parser.add_argument("--seed", type=int, default=None, help="Semilla de la simulación")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Ruta de la base de datos SQLite")
    args = parser.parse_args(argv)
    if args.auto:
        return auto_season(args.club, args.manager, args.seed)
    ui = GameUI(args.db)
    try:
        ui.run()
    except SystemExit:
        raise
    except KeyboardInterrupt:
        print("\nPartida interrumpida.")
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
