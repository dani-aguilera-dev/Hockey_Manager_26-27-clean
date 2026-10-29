"""Interfaz de texto del Hockey Manager (Fase 1).

Sin gráficos: tablas, decisiones y comentario textual. El motor y la
persistencia son independientes de esta capa.
"""

from __future__ import annotations

import random
import textwrap
from datetime import date
from pathlib import Path

from .calendar import league_table
from .cup import ROUND_NAMES, cup_next_user_fixture, cup_round_fixtures, cup_status_text
from .data_loader import dha_teams, load_clubs, load_teams
from .finance import financial_summary, sponsor_income
from .logistics import travel_options
from .market import (
    STAFF_LABELS,
    accept_incoming_offer,
    asking_price,
    fire_staff,
    generate_incoming_offers,
    hire_staff,
    make_transfer_offer,
    market_players,
    market_window,
    market_window_text,
    reject_incoming_offer,
    renew_contract,
    scout_range,
    staff_candidates,
)
from .models import FORMATION_SLOTS, GameState, PlayerState, TeamState
from .persistence import DEFAULT_DB, list_saves, load_game, save_game
from .press import answer_press, mark_press_done, press_questions
from .season import (
    ensure_week_training,
    finish_live_round,
    make_lineup,
    new_game,
    play_round,
    prepare_live_round,
    season_summary,
)
from .training import (
    DAYS,
    PLAN_PRESETS,
    SESSION_ORDER,
    SESSION_TYPES,
    apply_training_plan,
    auto_plan,
    format_plan,
    plan_name,
)
from .youth import promote_youth, release_youth

W = 100
WEEKDAYS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MONTHS = [
    "",
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]
POS_ORDER = {"Portero": 0, "Central": 1, "Lateral": 2, "Medio": 3, "Delantero": 4, "Polivalente": 5}


def header(title: str):
    print("\n" + "=" * W)
    print(title.center(W))
    print("=" * W)


def section(title: str):
    print("\n" + title)
    print("-" * W)


def line():
    print("-" * W)


def money(n: int | float) -> str:
    return f"{int(round(n)):,}".replace(",", ".") + " €"


def fmt_date(iso: str) -> str:
    try:
        d = date.fromisoformat(iso)
    except Exception:
        return iso
    return f"{WEEKDAYS[d.weekday()].capitalize()} {d.day:02d}/{d.month:02d}/{d.year}"


def short(s: str, n: int) -> str:
    s = str(s)
    return s if len(s) <= n else s[: n - 3] + "..."


def ask(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        raise SystemExit(0)


def pause(msg: str = "Pulsa Enter para continuar..."):
    ask(msg)


def wrap(text: str, width: int = W, indent: str = "") -> str:
    return "\n".join(textwrap.wrap(text, width=width, initial_indent=indent, subsequent_indent=indent))


def status(p: PlayerState) -> str:
    if p.injury > 0:
        return f"Lesionado ({p.injury})"
    if p.suspension > 0:
        return f"Sancionado ({p.suspension})"
    return "Disponible"


def difficulty(expectation: str) -> str:
    e = expectation.lower()
    if "título" in e or "final four" in e:
        return "Muy alta"
    if "top 4" in e:
        return "Alta"
    if "top 6" in e or "consolidar" in e:
        return "Media"
    if "permanencia" in e or "salvación" in e:
        return "Baja"
    return "Media"


class GameUI:
    def __init__(self, db_path: str | Path = DEFAULT_DB):
        self.db_path = Path(db_path)
        self.clubs_by_id, self.cities = load_clubs()
        self.state: GameState | None = None

    # ------------------------------------------------------------------ inicio
    def run(self):
        while True:
            header("HOCKEY MANAGER ESPAÑA 2026-27")
            print("  Liga IATI · DHA · DHB · Primera Andaluza")
            print("\n  1. Nueva partida")
            print("  2. Cargar partida")
            print("  3. Salir")
            op = ask("\n  > ")
            if op == "1":
                self.new_game_flow()
            elif op == "2":
                self.load_flow()
            elif op == "3":
                print("\nHasta la próxima temporada.")
                return

    def new_game_flow(self):
        manager = ask("Nombre del entrenador (Enter = Entrenador): ") or "Entrenador"
        team = self.choose_club()
        if not team:
            return
        raw_seed = ask("\nSemilla aleatoria (Enter = aleatoria): ")
        seed = int(raw_seed) if raw_seed.isdigit() else None
        print(f"\nCreando partida con {team.name}...")
        self.state = new_game(team.id, manager, seed)
        self.dashboard()

    def load_flow(self):
        saves = list_saves(self.db_path)
        if not saves:
            print("\nNo hay partidas guardadas.")
            pause()
            return
        section("PARTIDAS GUARDADAS")
        print(f"{'#':>3}  {'Nombre':<44} {'Club':<30} {'J':>3}  Actualizado")
        for s in saves:
            print(
                f"{s['id']:>3}  {short(s['name'], 44):<44} {short(s['club_id'], 30):<30} {s['round']:>3}  {s['updated_at']}"
            )
        raw = ask("\nNúmero o nombre de la partida (Enter = volver): ")
        if not raw:
            return
        try:
            self.state = load_game(raw, self.db_path)
        except Exception as e:
            print(f"\nNo se pudo cargar: {e}")
            pause()
            return
        print(f"\nPartida cargada: {self.state.user_team.name} · J{self.state.round}")
        if self.state.phase == "season_end":
            self.season_end_screen()
        else:
            self.dashboard()

    # ------------------------------------------------------------- club
    def choose_club(self) -> TeamState | None:
        teams, _, _ = load_teams()
        while True:
            league_choice = ask("Liga: [D] DHA · [H] DHB (Enter = DHA): ").lower()
            if league_choice in ("v",):
                return None
            league = "DHB" if league_choice in ("h", "dhb") else "DHA"
            clubs = sorted([t for t in teams.values() if t.league == league], key=lambda t: t.name)
            section(f"ELIGE TU CLUB · {league}")
            print(f"{'#':>3}  {'Club':<36} {'Ciudad':<18} {'Estadio':<30} {'Exigencia':<10}")
            line()
            for i, t in enumerate(clubs, 1):
                club = self.clubs_by_id.get(t.id, {})
                stadium = club.get("stadium", {}).get("name", t.stadium_name)
                print(
                    f"{i:>3}  {short(t.name, 36):<36} {short(t.city, 18):<18} {short(stadium, 30):<30} {difficulty(t.board_expectation):<10}"
                )
            raw = ask("\nNúmero de club (Enter = volver, L = cambiar liga): ")
            if not raw:
                return None
            if raw.lower() == "l":
                continue
            if not raw.isdigit() or not (1 <= int(raw) <= len(clubs)):
                print("Opción no válida.")
                continue
            team = clubs[int(raw) - 1]
            self.show_dossier(team)
            ok = ask("\n[Enter] aceptar el puesto   [V] volver: ").lower()
            if ok in ("", "s", "enter"):
                return team

    def show_dossier(self, team: TeamState):
        club = self.clubs_by_id.get(team.id, {})
        st = club.get("stadium", {})
        fin = club.get("finances", {})
        board = club.get("board", {})
        logi = club.get("logistics", {})
        line, _ = team.auto_lineup()
        attack, defense = team.lineup_strength(line)
        top = sorted(team.players, key=lambda p: p.overall, reverse=True)[:3]
        header(team.name.upper())
        print(f"{club.get('full_name', team.name)} · Fundado en {club.get('founded', '?')} · {team.city}")
        print(f"Colores: {', '.join(club.get('colors', [])) or '—'} · Liga: {team.league}")
        print(
            f"Estadio: {st.get('name', team.stadium_name)} · {st.get('capacity', team.stadium_capacity)} espectadores · {st.get('surface', '—')}"
        )
        section("HISTORIA")
        print(wrap(club.get("history", "Sin historia registrada.")))
        section("JUNTA DIRECTIVA")
        print(f"Objetivo: {board.get('expectation', team.board_expectation)}")
        print(f"Presión: {board.get('pressure', '—')} · Paciencia: {board.get('patience', '—')}/5")
        print(
            f"Presupuesto de fichajes: {money(fin.get('transfer_budget', team.budget))} · Masa salarial: {money(fin.get('wage_budget', team.wage_budget))}"
        )
        print(f"Segundo entrenador: {team.assistant_rating}/100 · Mánager: {team.manager_rating}/100")
        section("LOGÍSTICA")
        print(
            f"Aeropuerto: {logi.get('airport', '—')} · Tren: {logi.get('train', '—')} · Modo habitual: {logi.get('preferred_mode', '—')}"
        )
        print(wrap(logi.get("notes", ""), indent="  "))
        section("PLANTILLA")
        print(
            f"{len(team.players)} fichas · {len(team.squad)} jugadores de plantilla · Fuerza estimada: ataque {attack:.1f} / defensa {defense:.1f}"
        )
        print("Jugadores clave:")
        for p in top:
            print(f"  · {p.name:<34} {p.subposition:<10} OVR {p.overall:>4.1f} · {p.archetype}")
        if club.get("rivalries"):
            print(f"Rivalidades: {', '.join(club['rivalries'])}")

    # ------------------------------------------------------------- dashboard
    def dashboard(self):
        while self.state and self.state.phase == "regular":
            self.print_dashboard()
            print("\n  1. Jugar próximo partido")
            print("  2. Plantilla y ficha de jugador")
            print("  3. Táctica y once inicial")
            print("  4. Calendario y clasificación")
            print("  5. Club y estadio")
            print("  6. Finanzas")
            print("  7. Logística")
            print("  8. Guardar partida")
            print("  9. Salir")
            print("  E. Entrenamiento semanal")
            print("  S. Staff y junta directiva")
            print("  M. Mercado y contratos")
            print("  C. Copa del Rey")
            print("  P. Rueda de prensa")
            print("  K. Cantera")
            print("  A. Simular jornada (auto)")
            op = ask("\n  > ").lower()
            if op == "1":
                self.matchday()
            elif op == "2":
                self.squad_screen()
            elif op == "3":
                self.tactics_screen()
            elif op == "4":
                self.calendar_screen()
            elif op == "5":
                self.club_screen()
            elif op == "6":
                self.finances_screen()
            elif op == "7":
                self.logistics_screen()
            elif op == "8":
                self.save_flow()
            elif op == "9":
                self.exit_flow()
                return
            elif op == "e":
                self.training_screen()
            elif op == "s":
                self.staff_screen()
            elif op == "m":
                self.market_screen()
            elif op == "c":
                self.cup_screen()
            elif op == "p":
                self.press_screen()
            elif op == "k":
                self.cantera_screen()
            elif op == "a":
                self.auto_round()
            else:
                print("Opción no válida.")
        if self.state and self.state.phase == "season_end":
            self.season_end_screen()

    def print_dashboard(self):
        s = self.state
        t = s.user_team
        comp_label = f"{s.competition} · Grupo {s.dhb_group}" if s.competition == "DHB" else s.competition
        header(f"DASHBOARD · {fmt_date(s.date)} · {t.name.upper()} · {comp_label}")
        fx = s.next_user_fixture()
        if fx:
            home = s.teams[fx.home_id]
            away = s.teams[fx.away_id]
            rival = away if home.id == t.id else home
            venue = "casa" if home.id == t.id else "fuera"
            print(f"Próximo partido:  {home.name} vs {away.name}")
            print(
                f"Jornada {fx.round} · {fmt_date(fx.date)} · {venue} · {rival.stadium_name if venue == 'fuera' else t.stadium_name}"
            )
        else:
            print("Próximo partido:  temporada regular finalizada")
        table = s.table()
        pos = next((i for i, x in enumerate(table, 1) if x.id == t.id), 0)
        print(
            f"Posición: {pos}º/{len(table)} · {t.points} pts · {t.played} PJ · {t.won}G {t.drawn}E {t.lost}P · GF {t.goals_for} / GC {t.goals_against}"
        )
        print(
            f"Forma: {self.form_string()} · Moral: {t.morale}/20 · Junta: {t.board_confidence}/100 · Afición: {t.fan_confidence}/100"
        )
        mg = t.management_profile()
        print(
            f"Gestión: {mg['score']:.0f}/100 (bonus {mg['bonus']:+.1f}) · Cohesión: {t.cohesion}/20 · Mánager: {t.manager_rating}/100 · Junta: {t.board_confidence}/100"
        )
        print(f"Presión de la junta: {t.board_pressure} · Paciencia: {t.board_patience}/5")
        if s.week_trained:
            print(
                f"Entrenamiento: planificado ({plan_name(s.weekly_plan)}) · Preparación rival +{t.prep_bonus:.1f} · Segundo entrenador {t.assistant_rating}/100"
            )
        else:
            print(f"Entrenamiento: pendiente · [E] planificar la semana · Segundo entrenador {t.assistant_rating}/100")
        print(f"Copa del Rey: {cup_status_text(s)}")
        print(
            f"Caja: {money(t.budget)} · Fichajes: {money(t.transfer_budget)} · Salarios: {money(t.player_wage_bill())} + staff {money(t.staff_wage_bill())}"
        )
        inj = sum(1 for p in t.players if p.injury > 0)
        sus = sum(1 for p in t.players if p.suspension > 0)
        print(
            f"Bajas: {inj} lesionados · {sus} sancionados · Fatiga media: {sum(p.fatigue for p in t.players) / max(1, len(t.players)):.1f}%"
        )
        section("INBOX")
        for msg in s.inbox[-3:]:
            print(f"  [{msg.get('date', '')}] {msg.get('from', '')}: {msg.get('subject', '')}")
            print(f"      {short(msg.get('body', ''), 110)}")

    def form_string(self) -> str:
        s = self.state
        played = [f for f in s.fixtures if f.phase == "regular" and f.played and s.club_id in (f.home_id, f.away_id)]
        played.sort(key=lambda f: f.round)
        out = []
        for f in played[-5:]:
            gf = f.home_goals if f.home_id == s.club_id else f.away_goals
            ga = f.away_goals if f.home_id == s.club_id else f.home_goals
            out.append("V" if gf > ga else ("E" if gf == ga else "D"))
        return " ".join(out) if out else "—"

    # ------------------------------------------------------------- plantilla
    def squad_screen(self):
        s = self.state
        t = s.user_team
        while True:
            header(f"PLANTILLA · {t.name.upper()}")
            players = sorted(t.players, key=lambda p: (POS_ORDER.get(p.subposition, 9), -p.overall))
            print(
                f"{'#':>3}  {'Jugador':<34} {'Pos':<10} {'Edad':>4} {'OVR':>5} {'Forma':>5} {'Fatiga':>6} {'Moral':>5}  Estado"
            )
            line()
            for i, p in enumerate(players, 1):
                print(
                    f"{i:>3}  {short(p.name, 34):<34} {p.subposition:<10} {p.age:>4} {p.overall:>5.1f} {p.form:>5.1f} {p.fatigue:>5.0f}% {p.morale:>5}  {status(p)}"
                )
            raw = ask("\nNúmero para ficha · V volver: ").lower()
            if raw in ("v", ""):
                return
            if raw.isdigit() and 1 <= int(raw) <= len(players):
                self.player_detail(players[int(raw) - 1])
            else:
                print("Opción no válida.")

    def player_detail(self, p: PlayerState):
        t = self.state.user_team
        header(f"FICHA · {p.name.upper()}")
        print(f"{p.subposition} · {p.age} años · {t.name} · {p.perfil} · {p.archetype}")
        print(
            f"Overall: {p.overall:.1f} · Potencial: {p.potential:.1f} · Valor: {money(p.value)} · Polivalencia: {p.polivalencia:.1f}"
        )
        if p.overalls:
            print("Overalls por posición: " + " · ".join(f"{k} {v:.1f}" for k, v in p.overalls.items()))
        print(
            f"Temporada: {p.apps} PJ · {p.season_goals} goles · {p.season_assists} asistencias · Rating {p.rating:.2f}"
        )
        print(f"Estado: {status(p)} · Fatiga: {p.fatigue:.0f}% · Moral: {p.morale}/20 · Forma: {p.form:.1f}")
        groups = [
            ("TÉCNICA", ["control", "pase", "conduccion", "golpeo", "flick", "regate_3d", "definicion"]),
            (
                "AÉREA / SET PIECES",
                [
                    "aerial",
                    "pc_injection",
                    "pc_trap",
                    "pc_flick",
                    "pc_deflection",
                    "pc_first_runner",
                    "pc_gk_save",
                    "stroke_shot",
                    "stroke_save",
                    "free_hit",
                ],
            ),
            ("TÁCTICA", ["posicionamiento", "pressing", "cobertura", "transicion", "desmarque"]),
            ("FÍSICA", ["velocidad", "resistencia", "fuerza", "agilidad", "coordinacion"]),
            ("MENTAL", ["decisiones", "concentracion", "competitividad", "liderazgo"]),
            ("PORTERO", ["reflejos", "blocaje", "distribucion", "uno_vs_uno", "alto", "rebote_gk"]),
        ]
        for title, keys in groups:
            vals = [f"{k.replace('_', ' ').title()} {p.attributes.get(k, 0)}" for k in keys if k in p.attributes]
            if vals:
                section(title)
                print(wrap(" · ".join(vals)))
        pause()

    # ------------------------------------------------------------- táctica
    def tactics_screen(self):
        s = self.state
        t = s.user_team
        while True:
            header(f"TÁCTICA · {t.name.upper()}")
            tac = t.tactics
            print(
                f"Formación: {tac.formation} · Mentalidad: {tac.mentality.replace('_', ' ')} · Presión: {tac.press.replace('_', ' ')}"
            )
            print(
                f"Bloque: {tac.block.replace('_', ' ')} · Anchura: {tac.width.replace('_', ' ')} · Tempo: {tac.tempo.replace('_', ' ')} · Pase: {tac.passing.replace('_', ' ')} · PC: {tac.pc_routine.replace('_', ' ')}"
            )
            line, bench = make_lineup(t, s.manual_lineup or None)
            section("ONCE INICIAL")
            slots = FORMATION_SLOTS.get(tac.formation, FORMATION_SLOTS["4-3-3"])
            for i, slot in enumerate(slots):
                p = line[i] if i < len(line) else None
                if p:
                    print(f"  {slot:<4} {p.name:<36} OVR {p.overall:>4.1f} · Fatiga {p.fatigue:>3.0f}% · {status(p)}")
            print("\nBANQUILLO: " + ", ".join(p.name for p in bench[:7]))
            spec = t.specialists(line)
            section("ESPECIALISTAS")
            labels = {
                "pc_injector": "Inyector PC",
                "pc_stopper": "Stopper PC",
                "pc_flicker": "Drag flicker",
                "pc_deflector": "Desviador PC",
                "pc_first_runner": "Primer runner",
                "pc_goalkeeper": "Portero PC",
                "stroke_taker": "Stroke",
                "stroke_goalkeeper": "Portero stroke",
                "free_hit_taker": "Faltas",
            }
            for k, label in labels.items():
                p = spec.get(k)
                print(f"  {label:<16}: {p.name if p else '—'}")
            print("\n  1. Formación   2. Mentalidad   3. Presión   4. Bloque   5. Anchura")
            print("  6. Tempo       7. Pase         8. Rutina PC  9. Autoalineación  10. Elegir once manual")
            print("  V. Volver")
            op = ask("\n  > ").lower()
            if op == "1":
                tac.formation = self.choose_option("Formación", list(FORMATION_SLOTS), tac.formation)
            elif op == "2":
                tac.mentality = self.choose_option(
                    "Mentalidad",
                    ["muy_defensiva", "defensiva", "equilibrada", "ofensiva", "muy_ofensiva"],
                    tac.mentality,
                )
            elif op == "3":
                tac.press = self.choose_option("Presión", ["baja", "media", "alta", "muy_alta"], tac.press)
            elif op == "4":
                tac.block = self.choose_option("Bloque", ["bajo", "medio", "alto"], tac.block)
            elif op == "5":
                tac.width = self.choose_option("Anchura", ["estrecha", "normal", "ancha"], tac.width)
            elif op == "6":
                tac.tempo = self.choose_option("Tempo", ["lento", "normal", "rapido"], tac.tempo)
            elif op == "7":
                tac.passing = self.choose_option("Pase", ["corto", "mixto", "directo"], tac.passing)
            elif op == "8":
                tac.pc_routine = self.choose_option(
                    "Rutina PC", ["directa", "slip_izquierda", "slip_derecha", "desvio", "rebote"], tac.pc_routine
                )
            elif op == "9":
                s.manual_lineup = []
                print("Once automático activado.")
            elif op == "10":
                ids = self.choose_lineup(t, s.manual_lineup)
                if ids:
                    s.manual_lineup = ids
                    print("Once manual guardado para el próximo partido.")
            elif op in ("v", ""):
                return

    def choose_option(self, title: str, options: list[str], current: str) -> str:
        section(title.upper())
        for i, opt in enumerate(options, 1):
            mark = "  <-- actual" if opt == current else ""
            print(f"  {i}. {opt.replace('_', ' ')}{mark}")
        raw = ask("Opción (Enter = mantener): ")
        if not raw:
            return current
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print("Opción no válida.")
        return current

    def choose_lineup(self, team: TeamState, current_ids: list[str] | None = None) -> list[str] | None:
        available = team.available_players
        if len(available) < 11:
            print(f"\nSolo hay {len(available)} jugadores disponibles. Se usará la autoalineación.")
            pause()
            return None
        players = sorted(available, key=lambda p: (POS_ORDER.get(p.subposition, 9), -p.overall))
        current = set(current_ids or [])
        section("ELIGE EL ONCE INICIAL")
        print(f"{'#':>3}  {'Jugador':<34} {'Pos':<10} {'OVR':>5} {'Fatiga':>6}  Estado")
        line()
        for i, p in enumerate(players, 1):
            mark = "*" if p.id in current else " "
            print(
                f"{mark}{i:>2}  {short(p.name, 34):<34} {p.subposition:<10} {p.overall:>5.1f} {p.fatigue:>5.0f}%  {status(p)}"
            )
        raw = ask("\nEscribe 11 números separados por comas (A = auto, V = volver): ").strip()
        if raw.lower() in ("v", "", "a"):
            return None
        try:
            nums = [int(x.strip()) for x in raw.split(",") if x.strip()]
        except ValueError:
            print("Formato no válido.")
            pause()
            return None
        if len(nums) != 11 or len(set(nums)) != 11 or any(n < 1 or n > len(players) for n in nums):
            print("Debes elegir exactamente 11 jugadores distintos de la lista.")
            pause()
            return None
        return [players[n - 1].id for n in nums]

    # ------------------------------------------------------------- calendario
    def calendar_screen(self):
        s = self.state
        t = s.user_team
        header(f"CALENDARIO Y CLASIFICACIÓN · {t.name.upper()}")
        comp_label = f"{s.competition} · Grupo {s.dhb_group}" if s.competition == "DHB" else s.competition
        section(f"CLASIFICACIÓN {comp_label}")
        table = s.table()
        print(f"{'#':>3}  {'Equipo':<38} {'PJ':>3} {'G':>3} {'E':>3} {'P':>3} {'GF':>3} {'GC':>3} {'DG':>4} {'PTS':>4}")
        line()
        for i, x in enumerate(table, 1):
            print(
                f"{i:>3}  {short(x.name, 38):<38} {x.played:>3} {x.won:>3} {x.drawn:>3} {x.lost:>3} {x.goals_for:>3} {x.goals_against:>3} {x.goals_for - x.goals_against:>+4} {x.points:>4}"
            )
        section("CALENDARIO DEL EQUIPO")
        user_fx = [f for f in s.fixtures if f.phase == "regular" and t.id in (f.home_id, f.away_id)]
        user_fx.sort(key=lambda f: f.round)
        for f in user_fx:
            home = s.teams[f.home_id].name
            away = s.teams[f.away_id].name
            if f.played:
                res = f"{f.home_goals}-{f.away_goals}"
            else:
                res = "vs"
            marker = (
                " <<< próximo" if not f.played and s.next_user_fixture() and f.id == s.next_user_fixture().id else ""
            )
            print(
                f"  J{f.round:>2}  {fmt_date(f.date):<24} {short(home, 30):<30} {res:^7} {short(away, 30):<30}{marker}"
            )
        pause()

    def club_screen(self):
        self.show_dossier(self.state.user_team)
        pause()

    # ------------------------------------------------------------- finanzas
    def finances_screen(self):
        s = self.state
        t = s.user_team
        fin = financial_summary(t)
        header(f"FINANZAS · {t.name.upper()} · {s.season}")
        print(f"Caja actual:             {money(fin['cash'])}")
        print(f"Presupuesto de fichajes: {money(fin['transfer_budget'])}")
        print(
            f"Masa salarial anual:     {money(fin['annual_wage_bill'])}  (jugadores {money(fin['player_wage_bill'])} + staff {money(fin['staff_wage_bill'])})"
        )
        print(
            f"Coste salarial/jornada:  {money(fin['round_player_wages'] + fin['round_staff_wages'])}  (jugadores {money(fin['round_player_wages'])} + staff {money(fin['round_staff_wages'])})"
        )
        print(f"Patrocinio/jornada:      {money(fin['sponsor_round'])}")
        section("BALANCE DE TEMPORADA")
        print(f"  Taquilla:              {money(fin['gate'])}")
        print(f"  Patrocinio:            {money(fin['sponsor'])}")
        print(f"  Salarios jugadores:    {money(fin['player_wages'])}")
        print(f"  Salarios staff:        {money(fin['staff_wages'])}")
        print(f"  Viajes:                {money(fin['travel'])}")
        print(f"  Balance:               {money(fin['net'])}")
        print(f"  Confianza junta:       {t.board_confidence}/100 · Afición: {t.fan_confidence}/100")
        print(f"  Objetivo:              {t.board_expectation}")
        if fin["cash"] < 0:
            print("\nALERTA: la caja está en negativo. La junta puede perder la paciencia.")
        elif fin["net"] < 0:
            print("\nAviso: el balance de temporada es negativo; vigila salarios y viajes.")
        section("ÚLTIMOS MOVIMIENTOS")
        if fin["entries"]:
            for e in fin["entries"]:
                print(
                    f"  J{e['round']:>2}: taquilla {money(e['gate'])} + patrocinio {money(e['sponsor'])} - salarios {money(e['wages'])} - viajes {money(e['travel'])} = {money(e['net'])} · caja {money(e['cash_after'])}"
                )
        else:
            print("  Todavía no se ha cerrado ninguna jornada.")
        pause()

    def staff_screen(self):
        t = self.state.user_team
        roles = STAFF_LABELS
        while True:
            header(f"STAFF Y JUNTA · {t.name.upper()}")
            section("STAFF TÉCNICO")
            print(f"{'Rol':<26} {'Nombre':<28} {'Rating':>6} {'Salario':>10}  Fuente")
            line()
            for m in t.staff:
                print(
                    f"{roles.get(m.role, m.role):<26} {short(m.name, 28):<28} {m.rating:>6} {money(m.salary):>10}  {m.source} ({m.confidence})"
                )
            section("EFECTOS DEL STAFF")
            print(f"  Plan automático / charla: segundo entrenador {t.staff_rating('assistant')}/100")
            print(f"  Entrenamiento físico y prevención: preparador {t.staff_rating('fitness_coach')}/100")
            print(f"  Recuperación y lesiones: fisioterapeuta {t.staff_rating('physio')}/100")
            print(f"  Vídeo y preparación del rival: analista {t.staff_rating('performance_analyst')}/100")
            print(f"  Porteros y set pieces: entrenador de porteros {t.staff_rating('gk_coach')}/100")
            section("JUNTA DIRECTIVA")
            print(f"{'Cargo':<22} {'Nombre':<34} Fuente")
            line()
            board_roles = {
                "presidente": "Presidente",
                "vicepresidente": "Vicepresidente",
                "secretario": "Secretario",
                "tesorero": "Tesorero",
                "vocal_hockey": "Vocal de hockey",
                "vocal_social": "Vocal social",
            }
            for m in t.board:
                print(f"{board_roles.get(m.role, m.role):<22} {short(m.name, 34):<34} {m.source} ({m.confidence})")
            print(
                f"\n  Objetivo: {t.board_expectation} · Confianza: {t.board_confidence}/100 · Presión: {t.board_pressure} · Paciencia: {t.board_patience}/5"
            )
            print("\n  [H] Contratar staff   [F] Despedir staff   [V] Volver")
            op = ask("  > ").lower()
            if op in ("v", ""):
                return
            if op == "h":
                self.hire_staff_flow()
            elif op == "f":
                self.fire_staff_flow()

    def hire_staff_flow(self):
        t = self.state.user_team
        free_roles = [r for r in STAFF_LABELS if not any(m.role == r for m in t.staff)]
        if not free_roles:
            print("\nTodos los roles están cubiertos. Despide a alguien antes de contratar.")
            pause()
            return
        section("CONTRATAR STAFF")
        for i, role in enumerate(free_roles, 1):
            print(f"  {i}. {STAFF_LABELS[role]}")
        raw = ask("Rol (Enter = volver): ")
        if not raw.isdigit() or not (1 <= int(raw) <= len(free_roles)):
            return
        role = free_roles[int(raw) - 1]
        rng = random.Random(self.state.seed * 1000 + self.state.round * 61 + len(t.staff))
        candidates = staff_candidates(t, role, rng)
        section(f"CANDIDATOS · {STAFF_LABELS[role]}")
        for i, c in enumerate(candidates, 1):
            print(
                f"  {i}. {c.name:<28} rating {c.rating:>3} · salario {money(c.salary):>10} · contrato {c.contract_until}"
            )
        raw = ask("Elige candidato (Enter = volver): ")
        if not raw.isdigit() or not (1 <= int(raw) <= len(candidates)):
            return
        candidate = candidates[int(raw) - 1]
        result = hire_staff(self.state, candidate)
        print("\n" + result["message"])
        pause()

    def fire_staff_flow(self):
        t = self.state.user_team
        if not t.staff:
            print("\nNo hay staff que despedir.")
            pause()
            return
        section("DESPEDIR STAFF")
        for i, m in enumerate(t.staff, 1):
            print(f"  {i}. {STAFF_LABELS.get(m.role, m.role):<26} {m.name:<28} {money(m.salary)}")
        raw = ask("Número (Enter = volver): ")
        if not raw.isdigit() or not (1 <= int(raw) <= len(t.staff)):
            return
        member = t.staff[int(raw) - 1]
        ok = ask(f"¿Despedir a {member.name}? (s/n): ").lower()
        if ok not in ("s", "si", "sí"):
            return
        result = fire_staff(self.state, member.role)
        print("\n" + result["message"])
        pause()

    # ------------------------------------------------------------- mercado
    def market_screen(self):
        s = self.state
        t = s.user_team
        while True:
            header(f"MERCADO Y CONTRATOS · {market_window_text(s)}")
            print(
                f"Caja: {money(t.budget)} · Fichajes: {money(t.transfer_budget)} · Salarios: {money(t.player_wage_bill())} + staff {money(t.staff_wage_bill())}"
            )
            if market_window(s) == "cerrado":
                print("\nEl mercado está cerrado. Se abre antes del primer partido y en la jornada 12.")
                pause()
                return
            print("\n  1. Buscar jugadores")
            print(f"  2. Ofertas recibidas ({len(s.transfer_offers)})")
            print("  3. Renovar contratos")
            print("  4. Staff: contratar / despedir")
            print("  V. Volver")
            op = ask("\n  > ").lower()
            if op in ("v", ""):
                return
            if op == "1":
                self.market_search()
            elif op == "2":
                self.market_offers()
            elif op == "3":
                self.market_renewals()
            elif op == "4":
                self.staff_screen()

    def market_search(self):
        s = self.state
        t = s.user_team
        default_max = max(100000, int(t.transfer_budget / 0.70))
        raw = ask(f"Valor máximo de mercado (Enter = {money(default_max)}): ")
        max_value = int(raw) if raw.isdigit() else default_max
        pos_map = {"POR": "Portero", "CEN": "Central", "LAT": "Lateral", "MED": "Medio", "DEL": "Delantero"}
        pos_raw = ask("Posición POR/CEN/LAT/MED/DEL (Enter = todas): ").upper()
        position = pos_map.get(pos_raw)
        players = market_players(s, limit=30, max_value=max_value, position=position)
        if not players:
            print("\nNo hay jugadores que cumplan ese filtro.")
            pause()
            return
        section(f"JUGADORES DISPONIBLES · {market_window_text(s)}")
        print(f"{'#':>3}  {'Jugador':<30} {'Club':<26} {'Pos':<9} {'Edad':>4} {'OVR':>7} {'Precio':>10} {'Salario':>9}")
        line()
        scout = t.staff_rating("scout")
        for i, p in enumerate(players, 1):
            club = (
                "Agente libre"
                if any(y.id == p.id for y in s.free_agents)
                else next((x.name for x in s.teams.values() if any(y.id == p.id for y in x.players)), "—")
            )
            print(
                f"{i:>3}  {short(p.name, 30):<30} {short(club, 26):<26} {p.subposition:<9} {p.age:>4} {scout_range(p, scout):>7} {money(asking_price(p)):>10} {money(p.salary):>9}"
            )
        raw = ask("\nNúmero para ver informe (Enter = volver): ")
        if raw.isdigit() and 1 <= int(raw) <= len(players):
            self.market_player_detail(players[int(raw) - 1])

    def market_player_detail(self, player):
        s = self.state
        t = s.user_team
        club = (
            "Agente libre"
            if any(y.id == player.id for y in s.free_agents)
            else next((x.name for x in s.teams.values() if any(y.id == player.id for y in x.players)), "—")
        )
        scout = t.staff_rating("scout")
        header(f"INFORME DE OJEADOR · {player.name.upper()}")
        print(f"{player.subposition} · {player.age} años · {club}")
        print(
            f"Overall estimado: {scout_range(player, scout)} · Valor: {money(player.value)} · Precio de salida: {money(asking_price(player))}"
        )
        print(f"Salario actual: {money(player.salary)} · Contrato: {player.contract_until}")
        print(f"Ojeador: {scout}/100 · Cuanto mejor sea, más estrecho es el margen.")
        print("\n  [O] Hacer oferta   [V] Volver")
        if ask("  > ").lower() not in ("o", "oferta"):
            return
        default_fee = min(asking_price(player), t.transfer_budget)
        raw_fee = ask(f"Traspaso (Enter = {money(default_fee)}): ")
        fee = int(raw_fee) if raw_fee.isdigit() else default_fee
        default_salary = max(int(player.salary * 1.30), player.salary + 3000)
        raw_salary = ask(f"Salario anual (Enter = {money(default_salary)}): ")
        salary = int(raw_salary) if raw_salary.isdigit() else default_salary
        raw_years = ask("Años de contrato (Enter = 3): ")
        years = int(raw_years) if raw_years.isdigit() else 3
        result = make_transfer_offer(self.state, player.id, fee, salary, years)
        print("\n" + result["message"])
        pause()

    def market_offers(self):
        s = self.state
        offers = generate_incoming_offers(s)
        header("OFERTAS RECIBIDAS")
        if not offers:
            print("No hay ofertas pendientes.")
            pause()
            return
        for i, o in enumerate(offers, 1):
            print(
                f"  {i}. {o['player_name']:<30} de {o['from_club_name']:<26} · {money(o['fee'])} · salario {money(o['salary'])} · {o['years']} años"
            )
        raw = ask("\nNúmero de oferta (Enter = volver): ")
        if not raw.isdigit() or not (1 <= int(raw) <= len(offers)):
            return
        offer = offers[int(raw) - 1]
        action = ask("[A] aceptar · [R] rechazar · Enter = volver: ").lower()
        if action == "a":
            result = accept_incoming_offer(s, offer["id"])
            print("\n" + result["message"])
        elif action == "r":
            reject_incoming_offer(s, offer["id"])
            print("\nOferta rechazada.")
        pause()

    def market_renewals(self):
        s = self.state
        t = s.user_team
        players = sorted(t.players, key=lambda p: (p.contract_until, -p.overall))
        header("RENOVAR CONTRATOS")
        print(f"{'#':>3}  {'Jugador':<30} {'Pos':<9} {'Edad':>4} {'OVR':>5} {'Salario':>10} {'Contrato':<12}")
        line()
        for i, p in enumerate(players, 1):
            print(
                f"{i:>3}  {short(p.name, 30):<30} {p.subposition:<9} {p.age:>4} {p.overall:>5.1f} {money(p.salary):>10} {p.contract_until:<12}"
            )
        raw = ask("\nNúmero para renovar (Enter = volver): ")
        if not raw.isdigit() or not (1 <= int(raw) <= len(players)):
            return
        player = players[int(raw) - 1]
        default_salary = max(int(player.salary * 1.20), player.salary + 3000)
        raw_salary = ask(f"Nuevo salario (Enter = {money(default_salary)}): ")
        salary = int(raw_salary) if raw_salary.isdigit() else default_salary
        raw_years = ask("Años (Enter = 3): ")
        years = int(raw_years) if raw_years.isdigit() else 3
        result = renew_contract(s, player.id, salary, years)
        print("\n" + result["message"])
        pause()

    # ------------------------------------------------------------- cantera
    def cantera_screen(self):
        t = self.state.user_team
        while True:
            header(f"CANTERA · {t.name.upper()}")
            print(f"Academia: {t.academy_rating}/100 · {len(t.youth)} juveniles · {t.community}")
            if not t.youth:
                print("\nNo hay jugadores en la cantera. Llegarán nuevas generaciones al final de temporada.")
                pause()
                return
            print(
                f"{'#':>3}  {'Jugador':<28} {'Cat':<7} {'Pos':<9} {'Edad':>4} {'OVR':>5} {'Potencial':>9} {'Contrato':<12}"
            )
            line()
            for i, p in enumerate(t.youth, 1):
                print(
                    f"{i:>3}  {short(p.name, 28):<28} {p.youth_category:<7} {p.subposition:<9} {p.age:>4} {p.overall:>5.1f} {p.potential:>9.1f} {p.contract_until:<12}"
                )
            print("\n  [P] Promover al primer equipo   [R] Liberar   [V] Volver")
            op = ask("  > ").lower()
            if op in ("v", ""):
                return
            if op in ("p", "r"):
                raw = ask("Número de jugador: ")
                if not raw.isdigit() or not (1 <= int(raw) <= len(t.youth)):
                    continue
                p = t.youth[int(raw) - 1]
                if op == "p":
                    ok, msg = promote_youth(t, p.id)
                else:
                    ok, msg = release_youth(t, p.id)
                print("\n" + msg)
                pause()

    # ------------------------------------------------------------- prensa
    def press_screen(self):
        s = self.state
        if s.press_done_round == s.round:
            header("PRENSA · RUEDA COMPLETADA")
            for item in s.press_history[-3:]:
                print(f"  J{item['round']}: {item['headline']}")
            pause()
            return
        header("RUEDA DE PRENSA")
        for q in press_questions(s):
            print(f"\n  {q['question']}")
            for i, (label, _, _) in enumerate(q["options"], 1):
                print(f"    {i}. {label}")
            raw = ask("  Respuesta (Enter = 1): ")
            idx = int(raw) - 1 if raw.isdigit() and 1 <= int(raw) <= len(q["options"]) else 0
            result = answer_press(s, q["id"], idx)
            print(f"  → {result['message']}")
        mark_press_done(s)
        pause()

    # ------------------------------------------------------------- copa
    def cup_screen(self):
        s = self.state
        while True:
            header(f"COPA DEL REY · {cup_status_text(s)}")
            if not s.cup_active:
                if s.cup_winner_id in s.teams:
                    print(f"Campeón: {s.teams[s.cup_winner_id].name}")
                else:
                    print("La Copa se sortea al terminar la primera vuelta (jornada 11).")
                    print("Participan los 8 mejores equipos de DHA. No hay equipos de DHB.")
                pause()
                return
            fixtures = cup_round_fixtures(s)
            section(f"{ROUND_NAMES.get(s.cup_round, 'Ronda')} · {len(fixtures)} partidos")
            for f in fixtures:
                h = s.teams.get(f.home_id)
                a = s.teams.get(f.away_id)
                score = f"{f.home_goals}-{f.away_goals}" if f.played else "vs"
                print(f"  {short(h.name if h else '—', 32):<32} {score:^7} {short(a.name if a else '—', 32)}")
            user_fx = cup_next_user_fixture(s)
            if user_fx:
                print(f"\nTu partido: {s.teams[user_fx.home_id].name} vs {s.teams[user_fx.away_id].name}")
            elif s.club_id not in [f.home_id for f in fixtures] + [f.away_id for f in fixtures]:
                print("\nTu equipo ya no está en la Copa.")
            print("\n  [J] Jugar ronda   [S] Simular ronda   [A] Simular copa entera   [V] Volver")
            op = ask("  > ").lower()
            if op in ("v", ""):
                return
            if op == "a":
                from .season import simulate_cup_remaining

                simulate_cup_remaining(s)
                print("\nCopa completada.")
                pause()
                continue
            if op in ("j", "s"):
                from .season import simulate_cup_round

                payload = simulate_cup_round(s, s.manual_lineup or None)
                if payload:
                    self.print_cup_report(payload)
                    pause()
                else:
                    print("\nRonda simulada.")
                    pause()
                continue

    def print_cup_report(self, p: dict):
        header(f"COPA · {p['home_name'].upper()} {p['home_goals']}-{p['away_goals']} {p['away_name'].upper()}")
        print(f"{fmt_date(p['date'])} · {p['result']} ({p['user_goals']}-{p['user_against']})")
        for e in p.get("events", []):
            if e.get("type") in ("goal", "card", "injury", "substitution"):
                print(f"  {e.get('minute', 0):02d}' {e.get('text', '')}")

    # ------------------------------------------------------------- partido
    def matchday(self):
        s = self.state
        t = s.user_team
        fx = s.next_user_fixture()
        if not fx:
            print("No hay partido pendiente.")
            pause()
            return
        if not s.week_trained:
            report = ensure_week_training(s)
            if report:
                print("\nEl segundo entrenador ha aplicado el plan automático de la semana:")
                print(f"  {report['message']}")
        while True:
            home = s.teams[fx.home_id]
            away = s.teams[fx.away_id]
            rival = away if home.id == t.id else home
            header(f"PREVIA · JORNADA {fx.round} · {fmt_date(fx.date)}")
            print(f"{home.name} vs {away.name}")
            print(f"Estadio: {home.stadium_name} · {home.city}")
            pos = next((i for i, x in enumerate(s.table(), 1) if x.id == rival.id), 0)
            print(
                f"Rival: {rival.name} · {pos}º · {rival.points} pts · GF {rival.goals_for} / GC {rival.goals_against} · Moral {rival.morale}/20"
            )
            mg = t.management_profile()
            print(
                f"Tu gestión: {mg['score']:.0f}/100 (bonus {mg['bonus']:+.1f}) · Cohesión {t.cohesion}/20 · Mánager {t.manager_rating}/100"
            )
            line, bench = make_lineup(t, s.manual_lineup or None)
            section("ONCE INICIAL")
            slots = FORMATION_SLOTS.get(t.tactics.formation, FORMATION_SLOTS["4-3-3"])
            for i, slot in enumerate(slots):
                p = line[i] if i < len(line) else None
                print(
                    f"  {slot:<4} {p.name if p else '—':<36} "
                    + (f"OVR {p.overall:>4.1f} · Fatiga {p.fatigue:>3.0f}%" if p else "")
                )
            print("\nBANQUILLO: " + ", ".join(p.name for p in bench[:7]))
            print("\n[Enter] jugar en directo   [R] simulación rápida   [M] once manual   [T] táctica   [V] volver")
            op = ask("  > ").lower()
            if op in ("v",):
                return
            if op == "t":
                self.tactics_screen()
                continue
            if op == "m":
                ids = self.choose_lineup(t, s.manual_lineup)
                if ids:
                    s.manual_lineup = ids
                continue
            if op == "r":
                live = False
                break
            if op not in ("", "j", "d"):
                print("Opción no válida.")
                continue
            live = True
            break
        # viaje
        travel_id = None
        if fx.away_id == t.id:
            opts = travel_options(t, home, self.cities, squad_size=18)
            section("VIAJE")
            for i, o in enumerate(opts, 1):
                print(
                    f"  {i}. {o['label']:<26} {o['mode']:<7} {o['distance_km']:>5} km · {money(o['cost']):>10} · fatiga +{o['fatigue'] * 100:.0f}% · {o['hotel_nights']} noche(s)"
                )
                print(f"     {o['notes']}")
            default = next((i for i, o in enumerate(opts, 1) if o["id"] == "equilibrado"), 1)
            raw = ask(f"\nElige viaje (Enter = {default}): ")
            idx = int(raw) if raw.isdigit() and 1 <= int(raw) <= len(opts) else default
            chosen = opts[idx - 1]
            if chosen["cost"] > t.budget:
                print(
                    f"\nAviso: el viaje cuesta {money(chosen['cost'])} y el presupuesto es {money(t.budget)}. Se elegirá la opción más barata."
                )
                chosen = min(opts, key=lambda o: o["cost"])
            travel_id = chosen["id"]
            print(
                f"Viaje elegido: {chosen['label']} · {money(chosen['cost'])} · fatiga +{chosen['fatigue'] * 100:.0f}%"
            )
        else:
            print("\nPartido en casa: sin desplazamiento.")
        confirm = ask("\n¿Jugar el partido? (s/n): ").lower()
        if confirm not in ("s", "si", "sí", ""):
            return
        if live:
            self.live_match(travel_id)
            return
        payload = play_round(s, user_lineup_ids=s.manual_lineup or None, travel_option_id=travel_id)
        if not payload:
            print("No se pudo simular el partido.")
            pause()
            return
        self.print_match_report(payload)
        pause()

    # ------------------------------------------------------------- partido en directo
    def live_match(self, travel_id: str | None):
        s = self.state
        try:
            ctx = prepare_live_round(s, user_lineup_ids=s.manual_lineup or None, travel_option_id=travel_id)
        except Exception as e:
            print(f"No se pudo preparar el partido en directo: {e}")
            pause()
            return
        engine = ctx.engine
        home = s.teams[ctx.fixture.home_id]
        away = s.teams[ctx.fixture.away_id]
        user_side = ctx.user_side
        header(f"PARTIDO EN DIRECTO · {home.name.upper()} vs {away.name.upper()}")
        print(f"{fmt_date(ctx.fixture.date)} · Jornada {ctx.fixture.round} · {home.stadium_name}")
        print("El resto de la jornada ya se ha simulado. Tu partido se juega ahora.")
        print("Controles: Enter = avanzar · M = minuto a minuto · E = estadísticas · J = jugadores")
        print("           T = táctica · S = cambio · A = simular resto")
        mode = "quarter"
        talked = False
        while not engine.finished:
            if engine.quarter == 3 and not talked:
                self.halftime_talk(ctx)
                talked = True
            if engine.moment_in_quarter == 0:
                self.live_score_line(engine)
                op = ask(
                    "\n[Enter] cuarto completo · [M] minuto a minuto · [E] stats · [J] jugadores · [T] táctica · [S] cambio · [A] resto: "
                ).lower()
                if op == "m":
                    mode = "moment"
                elif op == "e":
                    self.live_stats(ctx)
                    continue
                elif op == "j":
                    self.live_players(ctx)
                    continue
                elif op == "t":
                    self.live_tactics(ctx)
                    continue
                elif op == "s":
                    self.live_substitution(ctx)
                    continue
                elif op == "a":
                    while not engine.finished:
                        engine.advance_quarter()
                    break
                else:
                    mode = "quarter"
            if mode == "moment":
                events = engine.advance_moment()
                self.live_events(events)
                if engine.finished:
                    break
                self.live_score_line(engine)
                if engine.moment_in_quarter == 0:
                    self.live_quarter_summary(engine)
                    continue
                while True:
                    op = ask(
                        "\n[Enter] siguiente · [C] cuarto completo · [E] stats · [J] jugadores · [T] táctica · [S] cambio · [A] resto: "
                    ).lower()
                    if op in ("", "n", "siguiente"):
                        break
                    if op == "c":
                        mode = "quarter"
                        break
                    if op == "e":
                        self.live_stats(ctx)
                        continue
                    if op == "j":
                        self.live_players(ctx)
                        continue
                    if op == "t":
                        self.live_tactics(ctx)
                        continue
                    if op == "s":
                        self.live_substitution(ctx)
                        continue
                    if op == "a":
                        while not engine.finished:
                            engine.advance_quarter()
                        break
                    print("Opción no válida.")
                if engine.finished:
                    break
                continue
            # modo cuarto
            events = engine.advance_quarter()
            self.live_events(events)
            if not engine.finished:
                self.live_quarter_summary(engine)
        payload = finish_live_round(s, ctx)
        self.print_match_report(payload)
        pause()

    def halftime_talk(self, ctx):
        engine = ctx.engine
        side = ctx.user_side
        team = self.state.user_team
        header("CHARLA DE VESTUARIO · DESCANSO")
        home = self.state.teams[engine.home.id]
        away = self.state.teams[engine.away.id]
        print(f"{home.name} {engine.score[0]}-{engine.score[1]} {away.name}")
        diff = engine.score[side] - engine.score[1 - side]
        situation = "vais por delante" if diff > 0 else ("vais empatando" if diff == 0 else "vais por detrás")
        avg_fat = sum(p.fatigue for p in engine._lineup(side)) / max(1, len(engine._lineup(side)))
        print(
            f"En el vestuario: {situation}. Moral {team.morale}/20 · Fatiga media {avg_fat:.0f}% · Segundo entrenador {team.assistant_rating}/100"
        )
        print("\n  1. Arenga: motivar y subir la intensidad")
        print("  2. Calma: tranquilizar y ordenar")
        print("  3. Exigir: apretar y pedir más")
        print("  4. Confiar: dar confianza al grupo")
        print("  5. Delegar en el segundo entrenador")
        raw = ask("\n  > ").lower()
        styles = {"1": "arenga", "2": "calma", "3": "exigir", "4": "confiar", "5": "delegar"}
        style = styles.get(raw, "delegar")
        result = engine.apply_team_talk(side, style)
        print(f"\n  {result['message']}")
        print(f"  Efecto para el próximo cuarto: {result['bonus']:+.1f} · Moral {team.morale}/20")
        pause()

    def live_score_line(self, engine):
        home = self.state.teams[engine.home.id]
        away = self.state.teams[engine.away.id]
        if engine.finished:
            print(f"\n  FINAL · {home.name} {engine.score[0]}-{engine.score[1]} {away.name}")
        else:
            q = min(engine.quarter, 4)
            print(f"\n  {home.name} {engine.score[0]}-{engine.score[1]} {away.name} · {q}º cuarto · {engine.minute}'")

    def live_events(self, events: list[dict]):
        key_types = {
            "goal",
            "pc",
            "stroke",
            "save",
            "card",
            "injury",
            "substitution",
            "chance",
            "circle_entry",
            "talk",
            "tactic",
        }
        prefix = {
            "goal": ">>> ",
            "save": "  ! ",
            "card": "  # ",
            "injury": "  + ",
            "substitution": "  -> ",
            "pc": "  PC ",
            "stroke": "  ST ",
            "talk": "  [Charla] ",
            "tactic": "  [Ajuste] ",
        }
        shown = False
        for e in events:
            if e.get("type") not in key_types:
                continue
            shown = True
            print(f"  {e.get('minute', 0):02d}' {prefix.get(e.get('type'), '  · ')}{e.get('text', '')}")
        if not shown:
            return

    def live_quarter_summary(self, engine):
        q = max(1, engine.quarter - 1)
        home = self.state.teams[engine.home.id]
        away = self.state.teams[engine.away.id]
        section(f"FIN DEL {q}º CUARTO · {home.name} {engine.score[0]}-{engine.score[1]} {away.name}")
        hs, as_ = engine.stats[0], engine.stats[1]
        print(
            f"  Posesión {hs.get('possession', 0)}%-{as_.get('possession', 0)}% · Tiros {hs.get('shots', 0)}-{as_.get('shots', 0)} · PC {hs.get('pc', 0)}-{as_.get('pc', 0)} · Paradas {hs.get('saves', 0)}-{as_.get('saves', 0)}"
        )
        hm = home.management_profile(engine.home_lineup)
        am = away.management_profile(engine.away_lineup)
        print(
            f"  Gestión local {hm['score']:.0f}/100 ({hm['bonus']:+.1f}) · visitante {am['score']:.0f}/100 ({am['bonus']:+.1f})"
        )
        print(
            f"  Lectura táctica: local +{engine.tactical_matchup_bonus(0):.1f} · visitante +{engine.tactical_matchup_bonus(1):.1f}"
        )

    def live_stats(self, ctx):
        engine = ctx.engine
        home = self.state.teams[engine.home.id]
        away = self.state.teams[engine.away.id]
        header("ESTADÍSTICAS EN DIRECTO")
        self.live_score_line(engine)
        hs, as_ = engine.stats[0], engine.stats[1]
        rows = [
            ("Posesión", f"{hs.get('possession', 0)}%", f"{as_.get('possession', 0)}%"),
            ("Tiros", hs.get("shots", 0), as_.get("shots", 0)),
            ("Tiros a puerta", hs.get("shots_on_target", 0), as_.get("shots_on_target", 0)),
            ("Penalty corners", hs.get("pc", 0), as_.get("pc", 0)),
            ("Goles de PC", hs.get("pc_goals", 0), as_.get("pc_goals", 0)),
            ("Strokes", hs.get("strokes", 0), as_.get("strokes", 0)),
            ("Paradas", hs.get("saves", 0), as_.get("saves", 0)),
            (
                "Tarjetas V/A/R",
                f"{hs.get('green', 0)}/{hs.get('yellow', 0)}/{hs.get('red', 0)}",
                f"{as_.get('green', 0)}/{as_.get('yellow', 0)}/{as_.get('red', 0)}",
            ),
            ("Entradas al círculo", hs.get("circle_entries", 0), as_.get("circle_entries", 0)),
            (
                "Pases completados",
                f"{hs.get('passes_completed', 0)}/{hs.get('passes', 0)}",
                f"{as_.get('passes_completed', 0)}/{as_.get('passes', 0)}",
            ),
        ]
        print(f"{'Estadística':<24} {short(home.name, 28):>28} {short(away.name, 28):>28}")
        for label, hv, av in rows:
            print(f"{label:<24} {str(hv):>28} {str(av):>28}")
        hm = home.management_profile(engine.home_lineup)
        am = away.management_profile(engine.away_lineup)
        print(f"\nGestión local: {hm['score']:.0f}/100 · bonus {hm['bonus']:+.2f} · cohesión {home.cohesion}/20")
        print(f"Gestión visitante: {am['score']:.0f}/100 · bonus {am['bonus']:+.2f} · cohesión {away.cohesion}/20")
        print(
            f"Lectura táctica: local +{engine.tactical_matchup_bonus(0):.1f} · visitante +{engine.tactical_matchup_bonus(1):.1f}"
        )
        pause()

    def live_players(self, ctx):
        engine = ctx.engine
        side = ctx.user_side
        team = self.state.user_team
        header(f"JUGADORES EN DIRECTO · {team.name.upper()}")
        rows = engine.player_live_rows(side)
        print(
            f"{'#':>3}  {'Jugador':<34} {'Pos':<9} {'Min':>3} {'G':>2} {'A':>2} {'S':>2} {'Tarj':>4} {'Rating':>6} {'Fatiga':>6}"
        )
        line()
        for i, r in enumerate(rows, 1):
            cards = f"{r['green']}/{r['yellow']}/{r['red']}"
            print(
                f"{i:>3}  {short(r['name'], 34):<34} {r['position']:<9} {r['minutes']:>3} {r['goals']:>2} {r['assists']:>2} {r['shots']:>2} {cards:>4} {r['rating']:>6.2f} {r['fatigue']:>5.0f}%"
            )
        print(
            f"\nCambios usados: {engine._subs[side]}/5 · Gestión: {team.management_score(engine._lineup(side)):.0f}/100"
        )
        section("BANQUILLO")
        for i, r in enumerate(engine.bench_live_rows(side), 1):
            state_txt = "LES" if r["injury"] > 0 else ("SAN" if r["suspension"] > 0 else "OK")
            print(
                f"  {i:>2}. {short(r['name'], 34):<34} {r['position']:<9} OVR {r['overall']:>4.1f} · fatiga {r['fatigue']:>5.0f}% · {state_txt}"
            )
        opp_team = self.state.teams[engine.away.id] if side == 0 else self.state.teams[engine.home.id]
        section(f"RIVAL · {opp_team.name.upper()}")
        print(f"{'#':>3}  {'Jugador':<34} {'Pos':<9} {'Min':>3} {'G':>2} {'A':>2} {'Rating':>6} {'Fatiga':>6}")
        for i, r in enumerate(engine.player_live_rows(1 - side), 1):
            print(
                f"{i:>3}  {short(r['name'], 34):<34} {r['position']:<9} {r['minutes']:>3} {r['goals']:>2} {r['assists']:>2} {r['rating']:>6.2f} {r['fatigue']:>5.0f}%"
            )
        pause()

    def live_tactics(self, ctx):
        engine = ctx.engine
        side = ctx.user_side
        t = self.state.user_team
        opp = self.state.teams[engine.away.id] if side == 0 else self.state.teams[engine.home.id]
        while True:
            header("TÁCTICA EN DIRECTO")
            tac = t.tactics
            print(
                f"Formación: {tac.formation} · Mentalidad: {tac.mentality.replace('_', ' ')} · Presión: {tac.press.replace('_', ' ')}"
            )
            print(
                f"Bloque: {tac.block.replace('_', ' ')} · Anchura: {tac.width.replace('_', ' ')} · Tempo: {tac.tempo.replace('_', ' ')} · Pase: {tac.passing.replace('_', ' ')} · PC: {tac.pc_routine.replace('_', ' ')}"
            )
            print(
                f"Lectura táctica actual: +{engine.tactical_matchup_bonus(side):.1f} · Gestión: {t.management_score(engine._lineup(side)):.0f}/100"
            )
            print("\n  1. Formación   2. Mentalidad   3. Presión   4. Bloque   5. Anchura")
            print("  6. Tempo       7. Pase         8. Rutina PC   V. Volver")
            op = ask("\n  > ").lower()
            if op in ("v", ""):
                return
            if op == "1":
                tac.formation = self.choose_option("Formación", list(FORMATION_SLOTS), tac.formation)
            elif op == "2":
                tac.mentality = self.choose_option(
                    "Mentalidad",
                    ["muy_defensiva", "defensiva", "equilibrada", "ofensiva", "muy_ofensiva"],
                    tac.mentality,
                )
            elif op == "3":
                tac.press = self.choose_option("Presión", ["baja", "media", "alta", "muy_alta"], tac.press)
            elif op == "4":
                tac.block = self.choose_option("Bloque", ["bajo", "medio", "alto"], tac.block)
            elif op == "5":
                tac.width = self.choose_option("Anchura", ["estrecha", "normal", "ancha"], tac.width)
            elif op == "6":
                tac.tempo = self.choose_option("Tempo", ["lento", "normal", "rapido"], tac.tempo)
            elif op == "7":
                tac.passing = self.choose_option("Pase", ["corto", "mixto", "directo"], tac.passing)
            elif op == "8":
                tac.pc_routine = self.choose_option(
                    "Rutina PC", ["directa", "slip_izquierda", "slip_derecha", "desvio", "rebote"], tac.pc_routine
                )
            print(
                f"\nTáctica actualizada. Lectura táctica: +{engine.tactical_matchup_bonus(side):.1f}. El efecto se aplica desde el próximo momento."
            )

    def live_substitution(self, ctx):
        engine = ctx.engine
        side = ctx.user_side
        header("CAMBIO EN DIRECTO")
        rows = engine.player_live_rows(side)
        bench = engine.bench_live_rows(side)
        print(f"{'#':>3}  {'Jugador en el campo':<36} {'Pos':<9} {'Min':>3} {'Rating':>6} {'Fatiga':>6} {'Goles':>5}")
        line()
        for i, r in enumerate(rows, 1):
            print(
                f"{i:>3}  {short(r['name'], 36):<36} {r['position']:<9} {r['minutes']:>3} {r['rating']:>6.2f} {r['fatigue']:>5.0f}% {r['goals']:>5}"
            )
        section("BANQUILLO")
        for i, r in enumerate(bench, 1):
            state_txt = "LES" if r["injury"] > 0 else ("SAN" if r["suspension"] > 0 else "OK")
            print(
                f"  {i:>2}. {short(r['name'], 36):<36} {r['position']:<9} OVR {r['overall']:>4.1f} · fatiga {r['fatigue']:>5.0f}% · {state_txt}"
            )
        print(f"\nCambios disponibles: {5 - engine._subs[side]}/5")
        raw_out = ask("Número del jugador que SALE (V = volver): ")
        if raw_out.lower() in ("v", ""):
            return
        raw_in = ask("Número del jugador que ENTRA: ")
        if not raw_out.isdigit() or not raw_in.isdigit():
            print("Selección no válida.")
            return
        io, ii = int(raw_out), int(raw_in)
        if not (1 <= io <= len(rows)) or not (1 <= ii <= len(bench)):
            print("Número fuera de rango.")
            return
        ok, msg = engine.manual_substitute(side, rows[io - 1]["id"], bench[ii - 1]["id"], coaching=True)
        print(("\n" + msg) if ok else f"\nNo se pudo hacer el cambio: {msg}")

    def print_match_report(self, p: dict):
        header(f"RESULTADO · {p['home_name'].upper()} {p['home_goals']}-{p['away_goals']} {p['away_name'].upper()}")
        print(f"{fmt_date(p['date'])} · Jornada {p['round']} · Asistencia: {p.get('attendance', 0)}")
        print(f"Perspectiva: {p['result']} ({p['user_goals']}-{p['user_against']})")
        section("COMENTARIO")
        key_types = {
            "goal",
            "pc",
            "stroke",
            "save",
            "card",
            "injury",
            "substitution",
            "chance",
            "circle_entry",
            "talk",
            "tactic",
        }
        events = [e for e in p.get("events", []) if e.get("type") in key_types]
        current_q = None
        for e in events:
            if e.get("quarter") != current_q:
                current_q = e.get("quarter")
                print(f"\n  --- Cuarto {current_q} ---")
            prefix = {
                "goal": ">>> ",
                "save": "  ! ",
                "card": "  # ",
                "injury": "  + ",
                "substitution": "  -> ",
                "pc": "  PC ",
                "stroke": "  ST ",
                "talk": "  [Charla] ",
                "tactic": "  [Ajuste] ",
            }.get(e.get("type"), "  · ")
            print(f"  {e.get('minute', 0):02d}' {prefix}{e.get('text', '')}")
        if not events:
            print("  Partido sin incidencias destacadas.")
        if p.get("shootout"):
            so = p["shootout"]
            print(
                f"\n  Shootout: {so.get('home_score')}-{so.get('away_score')} · Ganador: {self.state.teams[so['winner_id']].name}"
            )
        section("ESTADÍSTICAS")
        hs, as_ = p.get("home_stats", {}), p.get("away_stats", {})
        rows = [
            ("Posesión", f"{hs.get('possession', 0)}%", f"{as_.get('possession', 0)}%"),
            ("Tiros", hs.get("shots", 0), as_.get("shots", 0)),
            ("Tiros a puerta", hs.get("shots_on_target", 0), as_.get("shots_on_target", 0)),
            ("Penalty corners", hs.get("pc", 0), as_.get("pc", 0)),
            ("Goles de PC", hs.get("pc_goals", 0), as_.get("pc_goals", 0)),
            ("Strokes", hs.get("strokes", 0), as_.get("strokes", 0)),
            ("Paradas", hs.get("saves", 0), as_.get("saves", 0)),
            (
                "Tarjetas V/A/R",
                f"{hs.get('green', 0)}/{hs.get('yellow', 0)}/{hs.get('red', 0)}",
                f"{as_.get('green', 0)}/{as_.get('yellow', 0)}/{as_.get('red', 0)}",
            ),
            ("Entradas al círculo", hs.get("circle_entries", 0), as_.get("circle_entries", 0)),
            (
                "Pases completados",
                f"{hs.get('passes_completed', 0)}/{hs.get('passes', 0)}",
                f"{as_.get('passes_completed', 0)}/{as_.get('passes', 0)}",
            ),
        ]
        print(f"{'Estadística':<24} {short(p['home_name'], 28):>28} {short(p['away_name'], 28):>28}")
        for label, hv, av in rows:
            print(f"{label:<24} {str(hv):>28} {str(av):>28}")
        section("GESTIÓN")
        hm = p.get("home_management") or {}
        am = p.get("away_management") or {}
        print(
            f"  {short(p['home_name'], 32):<32} gestión {hm.get('score', 0):>5.1f}/100 · bonus {hm.get('bonus', 0):+.2f} · cohesión {self.state.teams[p['home_id']].cohesion}/20"
        )
        print(
            f"  {short(p['away_name'], 32):<32} gestión {am.get('score', 0):>5.1f}/100 · bonus {am.get('bonus', 0):+.2f} · cohesión {self.state.teams[p['away_id']].cohesion}/20"
        )
        print(f"  Preparación del rival: +{p.get('prep_bonus', 0):.1f}")
        section("RATINGS DEL EQUIPO")
        ratings = p.get("ratings", {})
        for name, r in sorted(ratings.items(), key=lambda x: -x[1])[:8]:
            print(f"  {name:<38} {r:>5.2f}")
        section("INCIDENCIAS")
        inc = [e for e in p.get("events", []) if e.get("type") in ("injury", "card")]
        if inc:
            for e in inc:
                print(f"  {e.get('minute', 0):02d}' {e.get('text', '')}")
        else:
            print("  Sin lesiones ni tarjetas.")
        tr = p.get("travel") or {}
        if tr:
            section("VIAJE")
            print(
                f"  {tr.get('from')} → {tr.get('to')} · {tr.get('mode')} · {tr.get('distance_km')} km · {tr.get('hotel_nights')} noche(s) · coste {money(tr.get('cost', 0))} · fatiga +{tr.get('fatigue_add', 0)}"
            )
        section("OTROS RESULTADOS")
        for f in self.state.fixtures:
            if (
                f.phase == "regular"
                and f.round == p["round"]
                and f.played
                and self.state.club_id not in (f.home_id, f.away_id)
            ):
                print(
                    f"  {short(self.state.teams[f.home_id].name, 34):<34} {f.home_goals}-{f.away_goals} {short(self.state.teams[f.away_id].name, 34)}"
                )
        nxt = self.state.next_user_fixture()
        if nxt:
            print(
                f"\nPróximo partido: {self.state.teams[nxt.home_id].name} vs {self.state.teams[nxt.away_id].name} · {fmt_date(nxt.date)}"
            )
        else:
            print("\nTemporada regular finalizada.")

    def auto_round(self):
        s = self.state
        s.manual_lineup = []
        payload = play_round(s, user_lineup_ids=None, travel_option_id="equilibrado")
        if payload:
            print(
                f"\nJ{payload['round']}: {payload['home_name']} {payload['home_goals']}-{payload['away_goals']} {payload['away_name']} · {payload['result']}"
            )
            table = s.table()
            pos = next((i for i, t in enumerate(table, 1) if t.id == s.club_id), 0)
            print(f"Posición: {pos}º · {s.user_team.points} pts")
        pause()

    # ------------------------------------------------------------- guardar / salir
    def save_flow(self):
        default = f"{self.state.user_team.name} · {self.state.season} · J{self.state.round}"
        name = ask(f"Nombre de la partida (Enter = {default}): ") or default
        try:
            save_game(self.state, name, self.db_path)
            print(f"Partida guardada: {name}")
        except Exception as e:
            print(f"No se pudo guardar: {e}")
        pause()

    def exit_flow(self):
        raw = ask("¿Guardar antes de salir? (s/n): ").lower()
        if raw in ("s", "si", "sí"):
            self.save_flow()

    # ------------------------------------------------------------- fin de temporada
    def season_end_screen(self):
        s = self.state
        summ = season_summary(s)
        header(f"FIN DE TEMPORADA · {s.season}")
        print(f"Campeón de {summ.get('competition', s.competition)}: {summ.get('champion') or '—'}")
        print(f"Campeón de Copa: {summ.get('cup_winner') or '—'}")
        if summ.get("cup_third"):
            print(f"Tercer puesto de Copa: {summ.get('cup_third')}")
        print(f"Campeón de EHL: {summ.get('ehl_winner') or '—'}")
        print(f"Tu club: {s.user_team.name} · Posición: {summ.get('user_position')}º/{len(summ.get('table', []))}")
        mg = s.user_team.management_profile()
        print(
            f"Gestión final: {mg['score']:.1f}/100 (bonus {mg['bonus']:+.2f}) · Cohesión {s.user_team.cohesion}/20 · Mánager {s.user_team.manager_rating}/100"
        )
        br = summ.get("board_review") or {}
        if br:
            section("REVISIÓN DE LA JUNTA")
            print(
                f"  Objetivo: {br.get('target')}º · Posición: {br.get('position')}º · {'Cumplido' if br.get('met') else 'No cumplido'}"
            )
            print(
                f"  Confianza: {br.get('confidence_before')} → {br.get('confidence_after')}/100 · Presupuesto de fichajes: {money(br.get('transfer_budget_after', 0))}"
            )
            print(f"  {br.get('message', '')}")
        group_txt = f" · Grupo {summ.get('group')}" if summ.get("competition") == "DHB" else ""
        section(f"CLASIFICACIÓN FINAL{group_txt}")
        print(f"{'#':>3}  {'Equipo':<40} {'PJ':>3} {'G':>3} {'E':>3} {'P':>3} {'GF':>3} {'GC':>3} {'DG':>4} {'PTS':>4}")
        for row in summ.get("table", []):
            print(
                f"{row['position']:>3}  {short(row['team'], 40):<40} {row['played']:>3} {row['won']:>3} {row['drawn']:>3} {row['lost']:>3} {row['gf']:>3} {row['ga']:>3} {row['gd']:>+4} {row['points']:>4}"
            )
        f4 = summ.get("final4") or {}
        if f4.get("semifinals"):
            section("FINAL FOUR")
            for i, sf in enumerate(f4.get("semifinals", []), 1):
                h = s.teams.get(sf.get("home_id"), None)
                a = s.teams.get(sf.get("away_id"), None)
                print(
                    f"  SF{i}: {h.name if h else '—'} {sf.get('home_goals')}-{sf.get('away_goals')} {a.name if a else '—'} · pasa {s.teams[sf['winner_id']].name if sf.get('winner_id') in s.teams else '—'}"
                )
            fin = f4.get("final") or {}
            if fin:
                h = s.teams.get(fin.get("home_id"), None)
                a = s.teams.get(fin.get("away_id"), None)
                print(
                    f"  FINAL: {h.name if h else '—'} {fin.get('home_goals')}-{fin.get('away_goals')} {a.name if a else '—'} · campeón {s.teams[f4['champion_id']].name if f4.get('champion_id') in s.teams else '—'}"
                )
        section("ASCENSOS Y DESCENSOS")
        print(f"  Ascienden: {', '.join(summ.get('promoted', [])) or '—'}")
        print(f"  Descienden: {', '.join(summ.get('relegated', [])) or '—'}")
        p = summ.get("playout") or {}
        if p:
            h = s.teams.get(p.get("home_id"), None)
            a = s.teams.get(p.get("away_id"), None)
            print(
                f"  PLAYOUT: {h.name if h else '—'} {p.get('home_goals')}-{p.get('away_goals')} {a.name if a else '—'}"
            )
            if p.get("stays_id"):
                print(
                    f"    El 11º clasificado mantiene la plaza; desciende el 12º: {summ.get('direct_relegated') or '—'}."
                )
            else:
                promoted = s.teams.get(p.get("promoted_id"), None)
                relegated = s.teams.get(p.get("relegated_id"), None)
                print(
                    f"    Asciende {promoted.name if promoted else '—'}; desciende {relegated.name if relegated else '—'}. El 12º también baja: {summ.get('direct_relegated') or '—'}."
                )
            print(f"    {p.get('note', '')}")
        rets = summ.get("retirements", [])
        if rets:
            section("RETIROS")
            for r in sorted(rets, key=lambda x: -x.get("overall", 0))[:10]:
                print(f"  {r['player']:<34} {r['club']:<30} {r['age']:>2} años · OVR {r['overall']:>4.1f}")
        section("MÁXIMOS GOLEADORES")
        for i, sc in enumerate(summ.get("top_scorers", [])[:10], 1):
            print(
                f"  {i:>2}. {sc['player']:<38} {sc['team']:<34} {sc['goals']:>3} goles · {sc['assists']:>2} asistencias"
            )
        print("\n  [C] Continuar siguiente temporada   [G] Guardar partida   [N] Nueva partida   [S] Salir")
        op = ask("  > ").lower()
        if op == "c":
            from .season import advance_to_next_season

            advance_to_next_season(s)
            self.dashboard()
        elif op == "g":
            self.save_flow()
            self.season_end_screen()
        elif op == "n":
            self.new_game_flow()
        else:
            print("\nFin de la Fase 1. Gracias por jugar.")
            raise SystemExit(0)
