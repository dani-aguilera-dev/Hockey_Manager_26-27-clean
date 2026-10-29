"""Motor de partido por fases para la Fase 1.

No es un motor físicas 2D/3D: simula momentos de juego y genera eventos
explicables a partir de los 37 atributos, la táctica, la fatiga y el contexto.
"""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass, field
from typing import Any

from . import rules
from .models import SLOT_TO_SUB, PlayerState, TeamState

HOME_ADVANTAGE_ATTACK = 4.0
HOME_ADVANTAGE_DEFENSE = 2.0
MOMENTS_PER_QUARTER = 16
QUARTER_MINUTES = rules.QUARTER_MINUTES
MOMENT_MINUTES = QUARTER_MINUTES / MOMENTS_PER_QUARTER


@dataclass
class MatchResult:
    home_id: str
    away_id: str
    home_goals: int
    away_goals: int
    events: list[dict[str, Any]] = field(default_factory=list)
    home_stats: dict[str, Any] = field(default_factory=dict)
    away_stats: dict[str, Any] = field(default_factory=dict)
    home_ratings: dict[str, float] = field(default_factory=dict)
    away_ratings: dict[str, float] = field(default_factory=dict)
    injuries: list[dict[str, Any]] = field(default_factory=list)
    cards: list[dict[str, Any]] = field(default_factory=list)
    player_minutes: dict[str, int] = field(default_factory=dict)
    shootout: dict[str, Any] = field(default_factory=dict)
    referee: dict[str, Any] = field(default_factory=dict)
    reviews: list[dict[str, Any]] = field(default_factory=list)
    added_time: dict[int, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def _weighted_choice(rng: random.Random, items: list[PlayerState], weights: list[float]) -> PlayerState:
    return rng.choices(items, weights=[max(0.1, w) for w in weights], k=1)[0]


def _mean(vals):
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals) if vals else 0.0


class MatchEngine:
    def __init__(
        self,
        home: TeamState,
        away: TeamState,
        rng: random.Random,
        *,
        neutral: bool = False,
        knockout: bool = False,
        home_lineup: list[PlayerState] | None = None,
        away_lineup: list[PlayerState] | None = None,
        home_bench: list[PlayerState] | None = None,
        away_bench: list[PlayerState] | None = None,
        detailed: bool = False,
        auto_sub_sides: set[int] | None = None,
        ai_sides: set[int] | None = None,
        auto_talk_sides: set[int] | None = None,
        match_date: str = "",
        opposition: dict[str, str] | None = None,
        opposition_side: int | None = None,
    ):
        self.home = home
        self.away = away
        self.rng = rng
        self.referee = dict(self.rng.choice(rules.REFEREE_PROFILES))
        self.match_date = match_date
        self.neutral = neutral
        self.knockout = knockout
        self.detailed = detailed
        self.home_lineup = home_lineup or home.auto_lineup()[0]
        self.away_lineup = away_lineup or away.auto_lineup()[0]
        self.home_bench = home_bench if home_bench is not None else home.auto_lineup()[1]
        self.away_bench = away_bench if away_bench is not None else away.auto_lineup()[1]
        self.home_spec = home.specialists(self.home_lineup)
        self.away_spec = away.specialists(self.away_lineup)
        self.home_starters = list(self.home_lineup)
        self.away_starters = list(self.away_lineup)
        self.played = {0: {p.id for p in self.home_lineup}, 1: {p.id for p in self.away_lineup}}
        self.score = [0, 0]
        self.events: list[dict[str, Any]] = []
        self.minute = 0
        self.quarter = 1
        self.zone = "middle"
        self.possession = 0  # 0 home, 1 away
        self.possession_counts = [0, 0]
        self.stats = {0: self._empty_stats(), 1: self._empty_stats()}
        self.player_stats: dict[str, dict[str, Any]] = {}
        self.player_minutes: dict[str, int] = {}
        for p in self.home_lineup + self.away_lineup:
            self.player_stats[p.id] = {
                "goals": 0,
                "assists": 0,
                "shots": 0,
                "saves": 0,
                "green": 0,
                "yellow": 0,
                "red": 0,
                "rating": 6.5,
            }
            self.player_minutes[p.id] = 0
        self.injuries: list[dict[str, Any]] = []
        self.cards: list[dict[str, Any]] = []
        # Videoarbitraje: una referencia por equipo y una decisión revisable
        # (gol, penalty corner o penalty stroke) por jugada.
        self.referrals: dict[int, int] = {0: rules.REFERRALS_PER_TEAM, 1: rules.REFERRALS_PER_TEAM}
        self.reviews: list[dict[str, Any]] = []
        self.last_decision: dict[str, Any] | None = None
        self.added_time: dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0}
        self.protest_used: dict[int, bool] = {0: False, 1: False}
        # Suspensiones temporales en minutos de juego. El equipo juega con
        # un jugador menos mientras el jugador siga en el diccionario.
        self.suspensions: dict[int, dict[str, float]] = {0: {}, 1: {}}
        self.red_cards: dict[int, set[str]] = {0: set(), 1: set()}
        self._subs = {0: 0, 1: 0}
        self.auto_sub_sides = set(auto_sub_sides) if auto_sub_sides is not None else {0, 1}
        self.ai_sides = set(ai_sides) if ai_sides is not None else {0, 1}
        self.auto_talk_sides = set(auto_talk_sides) if auto_talk_sides is not None else set(self.ai_sides)
        self.opposition = dict(opposition or {})
        self.opposition_side = opposition_side
        self.live_bonus = {0: 0.0, 1: 0.0}
        self.talk_bonus = {0: 0.0, 1: 0.0}
        self.talk_done = {0: False, 1: False}
        self.prepared = False
        self.finished = False
        self.result: MatchResult | None = None
        self.moment_in_quarter = 0
        self.total_moments = 0

    @staticmethod
    def _empty_stats() -> dict[str, Any]:
        return {
            "possession": 0,
            "shots": 0,
            "shots_on_target": 0,
            "pc": 0,
            "pc_goals": 0,
            "strokes": 0,
            "stroke_goals": 0,
            "saves": 0,
            "green": 0,
            "yellow": 0,
            "red": 0,
            "circle_entries": 0,
            "tackles": 0,
            "aerials": 0,
            "passes": 0,
            "passes_completed": 0,
            "goals": 0,
            "fouls": 0,
            "advantage": 0,
            "dangerous_play": 0,
            "distance_5m": 0,
            "pc_denied": 0,
            "stroke_awarded": 0,
            "dissent": 0,
            "unsportsmanlike": 0,
        }

    # ---------- utilidades ----------
    def _team(self, side: int) -> TeamState:
        return self.home if side == 0 else self.away

    def _raw_lineup(self, side: int) -> list[PlayerState]:
        """Once inscrito, incluidos lesionados y suspendidos."""
        return self.home_lineup if side == 0 else self.away_lineup

    def _lineup(self, side: int) -> list[PlayerState]:
        """Jugadores que están realmente disponibles para jugar.

        Un jugador lesionado, expulsado o suspendido temporalmente no cuenta
        para la fuerza del equipo ni para las acciones del momento. La lista
        original se conserva para poder sustituirlo o mostrar su estado.
        """
        raw = self._raw_lineup(side)
        active = [
            p
            for p in raw
            if p.id not in self.red_cards[side]
            and self.suspensions[side].get(p.id, 0.0) <= 0.0
            and p.available
        ]
        # Salvaguarda para partidos con expulsiones masivas: el motor nunca
        # debe quedarse sin una lista con la que calcular una acción.
        return active or raw

    def _field_lineup(self, side: int) -> list[PlayerState]:
        """Jugadores que siguen en el campo, incluidos los lesionados.

        Un jugador lesionado sigue ocupando su plaza hasta que se le sustituye;
        por eso aparece en la lista de cambios, aunque no cuente para las
        acciones del motor.
        """
        raw = self._raw_lineup(side)
        return [
            p
            for p in raw
            if p.id not in self.red_cards[side] and self.suspensions[side].get(p.id, 0.0) <= 0.0
        ]

    def _bench(self, side: int) -> list[PlayerState]:
        return self.home_bench if side == 0 else self.away_bench

    def _spec(self, side: int) -> dict[str, PlayerState]:
        return self.home_spec if side == 0 else self.away_spec

    def _gk(self, side: int) -> PlayerState:
        return max(
            self._lineup(side), key=lambda p: p.attributes.get("reflejos", 0) if p.subposition == "Portero" else -1
        )

    def opposition_effect(self, side: int) -> dict[str, float]:
        """Penalización de ataque/defensa por las instrucciones al rival."""
        if self.opposition_side != side or not self.opposition:
            return {"attack": 0.0, "defense": 0.0, "players": 0.0}
        attack = 0.0
        defense = 0.0
        count = 0
        for player in self._lineup(side):
            instruction = self.opposition.get(player.id)
            if not instruction:
                continue
            profile = rules.OPPOSITION_INSTRUCTIONS.get(instruction)
            if not profile:
                continue
            attack += float(profile.get("attack", 0.0))
            defense += float(profile.get("defense", 0.0))
            count += 1
        return {"attack": round(attack, 2), "defense": round(defense, 2), "players": float(count)}

    def _attack_defense(self) -> tuple[float, float, float, float]:
        home_lineup = self._lineup(0)
        away_lineup = self._lineup(1)
        ha, hd = self.home.lineup_strength(home_lineup)
        aa, ad = self.away.lineup_strength(away_lineup)
        # Jugar con uno menos penaliza ataque y defensa.
        ha -= max(0, rules.PLAYERS_ON_FIELD - len(home_lineup)) * 1.2
        hd -= max(0, rules.PLAYERS_ON_FIELD - len(home_lineup)) * 1.2
        aa -= max(0, rules.PLAYERS_ON_FIELD - len(away_lineup)) * 1.2
        ad -= max(0, rules.PLAYERS_ON_FIELD - len(away_lineup)) * 1.2
        if not self.neutral:
            ha += HOME_ADVANTAGE_ATTACK
            hd += HOME_ADVANTAGE_DEFENSE
        # moral + gestión + lectura táctica + ajuste de banquillo
        hm = self.home.management_bonus(home_lineup)
        am = self.away.management_bonus(away_lineup)
        ht = self.tactical_matchup_bonus(0)
        at = self.tactical_matchup_bonus(1)
        ha += hm + ht * 0.8 + self.live_bonus[0] + self.talk_bonus[0] + self.home.prep_bonus + self.home.equipment_bonus
        hd += hm + ht * 0.5 + self.live_bonus[0] * 0.5 + self.talk_bonus[0] * 0.7 + self.home.prep_bonus * 0.5 + self.home.equipment_bonus * 0.5
        aa += am + at * 0.8 + self.live_bonus[1] + self.talk_bonus[1] + self.away.prep_bonus + self.away.equipment_bonus
        ad += am + at * 0.5 + self.live_bonus[1] * 0.5 + self.talk_bonus[1] * 0.7 + self.away.prep_bonus * 0.5 + self.away.equipment_bonus * 0.5
        ha += (self.home.morale - 10) * 0.3
        hd += (self.home.morale - 10) * 0.3
        aa += (self.away.morale - 10) * 0.3
        ad += (self.away.morale - 10) * 0.3
        if self.opposition_side == 0:
            effect = self.opposition_effect(0)
            ha -= effect["attack"]
            hd -= effect["defense"]
        elif self.opposition_side == 1:
            effect = self.opposition_effect(1)
            aa -= effect["attack"]
            ad -= effect["defense"]
        return max(25.0, ha), max(25.0, hd), max(25.0, aa), max(25.0, ad)

    def _add_event(
        self, type_: str, side: int | None, player: PlayerState | None, text: str, minute: int | None = None
    ):
        minute = self.minute if minute is None else minute
        self.events.append(
            {
                "minute": int(minute),
                "quarter": self.quarter,
                "type": type_,
                "team_id": self._team(side).id if side is not None else None,
                "team_name": self._team(side).name if side is not None else None,
                "player_id": player.id if player else None,
                "player_name": player.name if player else None,
                "text": text,
                "score": f"{self.score[0]}-{self.score[1]}",
            }
        )

    def _inc_stat(self, side: int, key: str, n: int = 1):
        self.stats[side][key] += n

    def _rating(self, p: PlayerState) -> float:
        st = self.player_stats.get(p.id, {})
        r = 6.5 + 1.0 * st.get("goals", 0) + 0.5 * st.get("assists", 0) + 0.12 * st.get("saves", 0)
        r -= 0.35 * st.get("green", 0) + 0.7 * st.get("yellow", 0) + 1.5 * st.get("red", 0)
        if p.injury > 0:
            r -= 0.2
        return max(1.0, min(10.0, round(r, 2)))

    # ---------- videoarbitraje ----------
    def _record_decision(
        self, kind: str, side: int, player: PlayerState | None = None, **extra: Any
    ) -> None:
        """Guarda la última decisión revisable por el árbitro de vídeo."""
        self.last_decision = {
            "type": kind,
            "label": rules.REFERRAL_DECISIONS.get(kind, kind),
            "side": side,
            "team_name": self._team(side).name,
            "player_id": player.id if player else None,
            "player_name": player.name if player else None,
            "minute": int(self.minute),
            "quarter": self.quarter,
            "score": f"{self.score[0]}-{self.score[1]}",
            "reviewed": False,
            "goal": False,
            "scorer_id": None,
            "scorer_name": None,
            "assister_id": None,
            "goal_kind": "",
        }
        self.last_decision.update(extra)

    def _mark_decision_goal(
        self, scorer: PlayerState, assister: PlayerState | None, goal_kind: str
    ) -> None:
        if not self.last_decision:
            return
        self.last_decision.update(
            {
                "goal": True,
                "scorer_id": scorer.id,
                "scorer_name": scorer.name,
                "assister_id": assister.id if assister else None,
                "goal_kind": goal_kind,
            }
        )

    def _annul_goal(self, decision: dict[str, Any]) -> None:
        side = int(decision["side"])
        stats = self.stats[side]
        stats["goals"] = max(0, int(stats.get("goals", 0)) - 1)
        stats["shots"] = max(0, int(stats.get("shots", 0)) - 1)
        stats["shots_on_target"] = max(0, int(stats.get("shots_on_target", 0)) - 1)
        if decision.get("type") == "penalty_corner" or decision.get("goal_kind") in ("pc", "pc_rebound"):
            stats["pc_goals"] = max(0, int(stats.get("pc_goals", 0)) - 1)
        if decision.get("type") == "penalty_corner":
            stats["pc"] = max(0, int(stats.get("pc", 0)) - 1)
        if decision.get("type") == "penalty_stroke" or decision.get("goal_kind") == "stroke":
            stats["stroke_goals"] = max(0, int(stats.get("stroke_goals", 0)) - 1)
        if decision.get("type") == "penalty_stroke":
            stats["strokes"] = max(0, int(stats.get("strokes", 0)) - 1)
        self.score[side] = max(0, self.score[side] - 1)
        scorer_id = decision.get("scorer_id")
        if scorer_id and scorer_id in self.player_stats:
            self.player_stats[scorer_id]["goals"] = max(0, self.player_stats[scorer_id]["goals"] - 1)
        assister_id = decision.get("assister_id")
        if assister_id and assister_id in self.player_stats and assister_id != scorer_id:
            self.player_stats[assister_id]["assists"] = max(0, self.player_stats[assister_id]["assists"] - 1)

    def review_decision(self, side: int, decision_type: str = "") -> dict[str, Any]:
        """Revisión de vídeo solicitada por un equipo.

        El capitán pide revisar la última decisión (gol, PC o stroke). Si el
        árbitro de vídeo corrige la decisión, el equipo conserva su referencia;
        si la decisión se mantiene, la pierde.
        """
        if side not in (0, 1):
            return {"ok": False, "message": "Equipo no válido."}
        decision = self.last_decision
        if not decision:
            return {"ok": False, "message": "No hay ninguna decisión revisable."}
        if decision.get("reviewed"):
            return {"ok": False, "message": "Esa decisión ya fue revisada."}
        if decision_type and decision_type != decision.get("type"):
            return {"ok": False, "message": "La decisión ya no coincide con la jugada revisable."}
        if int(decision.get("side", -1)) == side:
            return {"ok": False, "message": "Solo puedes revisar una decisión contra tu equipo."}
        if self.referrals.get(side, 0) <= 0:
            return {"ok": False, "message": "No te quedan referencias de vídeo."}
        strictness = float(self.referee.get("strictness", 55))
        base = {"goal": 0.46, "penalty_corner": 0.34, "penalty_stroke": 0.30}.get(
            str(decision.get("type")), 0.30
        )
        chance = max(0.15, min(0.65, base + (55 - strictness) / 400))
        overturned = self.rng.random() < chance
        score_before = f"{self.score[0]}-{self.score[1]}"
        if overturned:
            if decision.get("goal"):
                self._annul_goal(decision)
            elif decision.get("type") == "penalty_corner":
                stats = self.stats[int(decision["side"])]
                stats["pc"] = max(0, int(stats.get("pc", 0)) - 1)
            elif decision.get("type") == "penalty_stroke":
                stats = self.stats[int(decision["side"])]
                stats["strokes"] = max(0, int(stats.get("strokes", 0)) - 1)
            text = (
                f"Revisión de vídeo: el árbitro corrige la decisión y anula "
                f"{decision.get('label', 'la jugada')} a favor de {decision.get('team_name')}."
            )
            if decision.get("goal"):
                text = (
                    f"Revisión de vídeo: gol anulado a {decision.get('scorer_name') or decision.get('team_name')}. "
                    f"El árbitro de vídeo corrige la decisión."
                )
        else:
            self.referrals[side] = max(0, self.referrals.get(side, 0) - 1)
            text = (
                f"Revisión de vídeo sin éxito para {self._team(side).name}: "
                f"se mantiene {decision.get('label', 'la decisión')} y se pierde la referencia."
            )
        decision["reviewed"] = True
        decision["overturned"] = overturned
        review = {
            "minute": int(self.minute),
            "quarter": self.quarter,
            "type": decision.get("type"),
            "label": decision.get("label"),
            "requested_by": self._team(side).name,
            "requested_side": side,
            "beneficiary": decision.get("team_name"),
            "overturned": overturned,
            "referrals_left": self.referrals[side],
            "score_before": score_before,
            "score_after": f"{self.score[0]}-{self.score[1]}",
            "text": text,
        }
        self.reviews.append(review)
        self._add_event("review", int(decision.get("side", 0)), None, text)
        return {
            "ok": True,
            "message": text,
            "review": review,
            "referrals": dict(self.referrals),
            "score": list(self.score),
        }

    # ---------- set pieces ----------
    def _penalty_corner(self, side: int):
        t = self._team(side)
        spec = t.specialists(self._lineup(side))
        opp = 1 - side
        opp_spec = self._team(opp).specialists(self._lineup(opp))
        gk = opp_spec.get("pc_goalkeeper") or self._gk(opp)
        inj = spec.get("pc_injector")
        stopper = spec.get("pc_stopper")
        # El rol manual manda; si no hay asignación, el especialista con mejor atributo.
        flicker = spec.get("pc_flicker")
        deflector = spec.get("pc_deflector")
        rebounder = spec.get("pc_rebounder") or deflector
        first_runner = opp_spec.get("pc_first_runner")
        self._inc_stat(side, "pc")
        self._record_decision("penalty_corner", side, inj)
        self._add_event("pc", side, inj, f"Penalty corner para {t.name}. {inj.name} coloca la bola en la marca.")
        # 1. saque vs primer runner
        inj_roll = inj.attributes.get("pc_injection", 50) + self.rng.gauss(0, 7)
        press_roll = (
            first_runner.attributes.get("pc_first_runner", 50) + first_runner.attributes.get("velocidad", 50)
        ) / 2 + self.rng.gauss(0, 7)
        if inj_roll < press_roll - 8 and self.rng.random() < 0.35:
            self._add_event(
                "pc", side, first_runner, f"{first_runner.name} sale rápido y corta el saque. PC desactivado."
            )
            self.possession = opp
            self.zone = "middle"
            return
        # 2. parada / control
        stop_roll = stopper.attributes.get("pc_trap", 50) + self.rng.gauss(0, 6)
        if stop_roll < 35 and self.rng.random() < 0.30:
            self._add_event("pc", side, stopper, f"{stopper.name} no controla el saque; la bola se pierde.")
            self.possession = opp
            self.zone = "attacking_23"
            return
        # 3. tiro o desvío
        routine = t.tactics.pc_routine
        if routine == "variacion":
            routine = self.rng.choice(["directa", "slip_izquierda", "slip_derecha", "desvio", "rebote"])
        shooter = deflector if routine == "desvio" else flicker
        attr = "pc_deflection" if routine == "desvio" else "pc_flick"
        shot = shooter.attributes.get(attr, 50) + self.rng.gauss(0, 7)
        gk_roll = (gk.attributes.get("pc_gk_save", 50) + gk.attributes.get("reflejos", 50)) / 2 + self.rng.gauss(0, 6)
        pressure = (first_runner.attributes.get("pc_first_runner", 50) - 50) * 0.15
        chance = 0.42 + (shot - gk_roll) / 260 - pressure / 100
        if routine == "slip_izquierda" or routine == "slip_derecha":
            chance += 0.04
        if routine == "rebote":
            chance += 0.02
        chance = max(0.12, min(0.70, chance))
        if self.rng.random() < chance:
            self.score[side] += 1
            self._inc_stat(side, "goals")
            self._inc_stat(side, "pc_goals")
            self._inc_stat(side, "shots")
            self._inc_stat(side, "shots_on_target")
            self.player_stats[shooter.id]["goals"] += 1
            assister = inj if self.rng.random() < 0.6 else stopper
            self.player_stats[assister.id]["assists"] += 1
            self._mark_decision_goal(shooter, assister, "pc")
            self._add_event(
                "goal",
                side,
                shooter,
                f"¡Gol de {t.name}! {shooter.name} transforma el PC con un {('desvío' if routine == 'desvio' else 'drag flick')}. Asistencia de {assister.name}.",
            )
            self.possession = opp
            self.zone = "middle"
        else:
            self._inc_stat(side, "shots")
            if self.rng.random() < 0.65:
                self._inc_stat(side, "shots_on_target")
                self._inc_stat(opp, "saves")
                self.player_stats[gk.id]["saves"] += 1
                self._add_event(
                    "save", side, gk, f"Paradón de {gk.name} al tiro de {shooter.name}. El PC se queda sin premio."
                )
                # rebote: el jugador asignado al rechace tiene prioridad.
                if self.rng.random() < 0.18:
                    reb = rebounder
                    self.score[side] += 1
                    self._inc_stat(side, "goals")
                    self._inc_stat(side, "pc_goals")
                    self.player_stats[reb.id]["goals"] += 1
                    self._mark_decision_goal(reb, None, "pc_rebound")
                    self._add_event("goal", side, reb, f"{reb.name} caza el rebote y empuja la bola. Gol de {t.name}.")
            else:
                self._add_event("pc", side, shooter, f"{shooter.name} tira el PC, pero la bola se marcha fuera.")
            self.possession = opp
            self.zone = "middle"

    def _stroke(self, side: int):
        t = self._team(side)
        spec = t.specialists(self._lineup(side))
        opp = 1 - side
        opp_spec = self._team(opp).specialists(self._lineup(opp))
        gk = opp_spec.get("stroke_goalkeeper") or self._gk(opp)
        taker = spec.get("stroke_taker")
        self._inc_stat(side, "strokes")
        self._record_decision("penalty_stroke", side, taker)
        self._add_event("stroke", side, taker, f"Penalty stroke para {t.name}. {taker.name} toma la bola.")
        shot = taker.attributes.get("stroke_shot", 50) + self.rng.gauss(0, 6)
        save = gk.attributes.get("stroke_save", 50) + self.rng.gauss(0, 6)
        chance = 0.78 + (shot - save) / 260
        chance = max(0.55, min(0.92, chance))
        if self.rng.random() < chance:
            self.score[side] += 1
            self._inc_stat(side, "goals")
            self._inc_stat(side, "stroke_goals")
            self._inc_stat(side, "shots")
            self._inc_stat(side, "shots_on_target")
            self.player_stats[taker.id]["goals"] += 1
            self._mark_decision_goal(taker, None, "stroke")
            self._add_event(
                "goal", side, taker, f"¡Gol de {t.name}! {taker.name} engaña al portero y convierte el stroke."
            )
        else:
            self._inc_stat(side, "shots")
            if self.rng.random() < 0.75:
                self._inc_stat(side, "shots_on_target")
                self._inc_stat(opp, "saves")
                self.player_stats[gk.id]["saves"] += 1
                self._add_event("save", side, gk, f"{gk.name} adivina el lado y detiene el stroke de {taker.name}.")
            else:
                self._add_event("stroke", side, taker, f"{taker.name} falla el stroke; la bola se marcha fuera.")
        self.possession = opp
        self.zone = "middle"

    # ---------- acciones de juego ----------
    def _goal(self, side: int, scorer: PlayerState, assister: PlayerState | None, kind: str):
        t = self._team(side)
        self._record_decision(
            "goal",
            side,
            scorer,
            goal=True,
            scorer_id=scorer.id,
            scorer_name=scorer.name,
            assister_id=assister.id if assister else None,
            goal_kind=kind,
        )
        self.score[side] += 1
        self._inc_stat(side, "goals")
        self._inc_stat(side, "shots")
        self._inc_stat(side, "shots_on_target")
        self.player_stats[scorer.id]["goals"] += 1
        if assister and assister.id != scorer.id:
            self.player_stats[assister.id]["assists"] += 1
        if kind == "pc":
            self._inc_stat(side, "pc_goals")
        if kind == "stroke":
            self._inc_stat(side, "stroke_goals")
        text = {
            "open": f"¡Gol de {t.name}! {scorer.name} define dentro del área.",
            "pc": f"¡Gol de {t.name}! {scorer.name} transforma el penalty corner.",
            "stroke": f"¡Gol de {t.name}! {scorer.name} convierte el stroke.",
            "deflection": f"¡Gol de {t.name}! {scorer.name} desvía el disparo de {assister.name if assister else 'un compañero'}.",
            "rebound": f"¡Gol de {t.name}! {scorer.name} aprovecha el rebote.",
        }.get(kind, f"¡Gol de {t.name}! {scorer.name} marca.")
        self._add_event("goal", side, scorer, text)
        self.possession = 1 - side
        self.zone = "middle"

    def _shot(self, side: int, kind: str = "open"):
        t = self._team(side)
        opp = 1 - side
        lineup = self._lineup(side)
        # peso por atributos ofensivos y posición
        weights = []
        for p in lineup:
            w = 25 + p.attributes.get("definicion", 50) + p.attributes.get("pc_flick", 40) * 0.2
            if p.subposition == "Delantero":
                w += 20
            elif p.subposition == "Medio":
                w += 5
            elif p.subposition in ("Central", "Lateral"):
                w -= 10
            weights.append(max(1, w))
        scorer = _weighted_choice(self.rng, lineup, weights)
        assister = None
        if self.rng.random() < 0.65:
            assister = _weighted_choice(
                self.rng,
                lineup,
                [p.attributes.get("pase", 50) + p.attributes.get("pc_injection", 40) * 0.3 for p in lineup],
            )
        self._inc_stat(side, "shots")
        attack = scorer.attributes.get("definicion", 50) + self.rng.gauss(0, 8)
        gk = self._gk(opp)
        defense = (gk.attributes.get("reflejos", 50) + gk.attributes.get("blocaje", 50)) / 2 + self.rng.gauss(0, 6)
        on_target = self.rng.random() < (0.55 + (attack - 50) / 180)
        if not on_target:
            self._add_event(
                "chance", side, scorer, f"{scorer.name} prueba desde el borde del círculo, pero se marcha alto."
            )
            self.possession = opp
            self.zone = "middle"
            return
        self._inc_stat(side, "shots_on_target")
        goal_chance = 0.31 + (attack - defense) / 250
        goal_chance = max(0.10, min(0.65, goal_chance))
        if self.rng.random() < goal_chance:
            self._goal(side, scorer, assister, kind)
        else:
            self._inc_stat(opp, "saves")
            self.player_stats[gk.id]["saves"] += 1
            self._add_event("save", side, gk, f"{gk.name} responde con una parada firme al disparo de {scorer.name}.")
            self.possession = opp
            self.zone = "middle"

    def _foul(
        self,
        side: int,
        foul_type: str | None = None,
        advantage: bool | None = None,
        pc_decision: str | None = None,
        distance_call: bool | None = None,
    ):
        # side = equipo que comete la falta
        t = self._team(side)
        opp = 1 - side
        lineup = self._lineup(side)
        offender = self.rng.choice(lineup)
        if foul_type not in rules.FOUL_TYPES:
            keys = list(rules.FOUL_TYPES)
            foul_type = self.rng.choices(keys, weights=[float(rules.FOUL_TYPES[k]["weight"]) for k in keys], k=1)[0]
        profile = rules.FOUL_TYPES[foul_type]
        dangerous = bool(profile.get("dangerous"))
        in_circle = self.zone == "circle"
        in_attack = self.zone in ("attacking_23", "circle")
        self._inc_stat(side, "fouls")
        self._add_event("foul", side, offender, f"Falta de {offender.name} ({t.name}): {profile['label']}.")
        if dangerous:
            self._inc_stat(side, "dangerous_play")
            self._add_event(
                "dangerous_play",
                side,
                offender,
                f"Juego peligroso de {offender.name}: el árbitro detiene la jugada y valora la tarjeta.",
            )
            if self.rng.random() < 0.45:
                self._card(side)
        if advantage is None:
            advantage = not dangerous and not in_circle and in_attack and self.rng.random() < 0.25
        if advantage:
            self._inc_stat(opp, "advantage")
            self._add_event(
                "advantage",
                opp,
                None,
                f"El árbitro deja jugar la ventaja a {self._team(opp).name} durante {rules.ADVANTAGE_SECONDS} segundos.",
            )
            self.possession = opp
            return
        if in_circle:
            if pc_decision is None:
                if dangerous and self.rng.random() < 0.35:
                    pc_decision = "stroke"
                elif self.rng.random() < 0.12:
                    pc_decision = "denied"
                else:
                    pc_decision = "pc"
            if pc_decision == "stroke":
                self._inc_stat(opp, "stroke_awarded")
                self._add_event(
                    "pc_decision",
                    opp,
                    None,
                    f"El árbitro concede penalty stroke a {self._team(opp).name} por la falta en el círculo.",
                )
                self._stroke(opp)
                return
            if pc_decision == "denied":
                self._inc_stat(opp, "pc_denied")
                self._add_event(
                    "pc_decision",
                    opp,
                    None,
                    f"El árbitro no concede penalty corner a {self._team(opp).name}: la falta no impide una ocasión clara.",
                )
                self.possession = opp
                self.zone = "middle"
                return
            self._penalty_corner(opp)
            return
        self._add_event(
            "free_hit",
            side,
            None,
            f"Falta para {self._team(opp).name}. El árbitro marca la distancia de {rules.FREE_HIT_DISTANCE_METERS} metros.",
        )
        if distance_call is None:
            distance_call = self.rng.random() < 0.25 or float(self.referee.get("strictness", 55)) >= 65
        if distance_call:
            self._inc_stat(opp, "distance_5m")
            self._add_event(
                "distance_5m",
                opp,
                None,
                f"El árbitro obliga a retroceder {rules.FREE_HIT_DISTANCE_METERS} metros a la defensa.",
            )
            self.zone = "attacking_23" if self.rng.random() < 0.35 else "middle"
        self.possession = opp

    def _card(self, side: int):
        t = self._team(side)
        lineup = self._lineup(side)
        if not lineup:
            return
        p = self.rng.choice(lineup)
        prior_cards: list[str] = []
        for card_type in ("green", "yellow", "red"):
            prior_cards.extend([card_type] * int(self.player_stats[p.id].get(card_type, 0)))
        forced = rules.next_card_for_player(prior_cards) if prior_cards else ""
        roll = max(0.0, min(0.999, self.rng.random() + float(self.referee.get("card_bias", 0.0))))
        if forced:
            card_type = forced
        elif roll < 0.72:
            card_type = "green"
        elif roll < 0.96:
            card_type = "yellow"
        else:
            card_type = "red"
        serious = card_type == "yellow" and self.rng.random() < 0.25
        duration = rules.suspension_minutes(card_type, serious=serious)
        reason = self.rng.choice(rules.CARD_REASONS[card_type])
        self._inc_stat(side, card_type)
        self.player_stats[p.id][card_type] += 1
        card = {
            "player_id": p.id,
            "player_name": p.name,
            "team_id": t.id,
            "team_name": t.name,
            "type": card_type,
            "label": rules.CARD_LABELS[card_type],
            "duration_minutes": duration,
            "rest_of_match": card_type == "red",
            "minute": int(self.minute),
            "quarter": self.quarter,
            "reason": reason,
            "suspension_matches": rules.next_match_suspension(card_type),
            "date": self.match_date,
        }
        self.cards.append(card)
        p.card_history = (p.card_history + [card])[-50:]
        if card_type in ("green", "yellow"):
            self.suspensions[side][p.id] = max(self.suspensions[side].get(p.id, 0.0), float(duration))
            suffix = f"{duration} minuto(s) de suspensión temporal; el equipo juega con uno menos."
        else:
            self.red_cards[side].add(p.id)
            p.suspension = max(p.suspension, rules.next_match_suspension("red"))
            p.suspension_reason = "Tarjeta roja"
            p.suspension_started = self.match_date
            p.absence_note = "Sanción por tarjeta roja"
            suffix = "expulsado; el equipo juega con uno menos el resto del partido."
        self._add_event("card", side, p, f"{rules.CARD_LABELS[card_type]} para {p.name} ({t.name}): {reason}. {suffix}")
        p.morale = max(1, p.morale - {"green": 1, "yellow": 2, "red": 4}[card_type])
        if reason in ("retraso deliberado", "conducta antideportiva"):
            kind = "delay" if reason == "retraso deliberado" else "misconduct"
            self._unsportsmanlike(side, kind, p, card=False)
        if card_type in ("yellow", "red"):
            self._protest(side, p, "card", "warning")

    def _protest(
        self,
        side: int,
        player: PlayerState | None = None,
        decision_type: str = "card",
        outcome: str = "warning",
    ) -> dict[str, Any]:
        """Protesta de un jugador; puede quedarse en aviso o derivar en tarjeta."""
        lineup = self._lineup(side)
        if not lineup:
            return {"ok": False}
        player = player or lineup[0]
        self._inc_stat(side, "dissent")
        self._add_event(
            "protest",
            side,
            player,
            f"{player.name} protesta la decisión arbitral ({decision_type}). El árbitro responde con {('tarjeta' if outcome == 'card' else 'un aviso')}.",
        )
        if outcome == "card":
            self._card(side)
        return {"ok": True, "outcome": outcome, "player_id": player.id}

    def protest_decision(self, side: int, tone: str = "respetuosa") -> dict[str, Any]:
        """Protesta en directo: una por equipo, con riesgo de tarjeta si es vehemente."""
        if side not in (0, 1):
            return {"ok": False, "message": "Equipo no válido."}
        if self.protest_used.get(side):
            return {"ok": False, "message": "Ya has usado la protesta de este equipo."}
        if tone not in ("respetuosa", "vehemente"):
            return {"ok": False, "message": "El tono de la protesta no es válido."}
        lineup = self._lineup(side)
        if not lineup:
            return {"ok": False, "message": "No hay jugadores para protestar."}
        player = lineup[0]
        outcome = "warning" if tone == "respetuosa" else "card"
        self._protest(side, player, "live", outcome)
        self.protest_used[side] = True
        message = (
            f"{player.name} protesta con respeto. El árbitro responde con un aviso."
            if tone == "respetuosa"
            else f"{player.name} protesta de forma vehemente. El árbitro responde con tarjeta."
        )
        return {"ok": True, "message": message, "tone": tone, "card": outcome == "card", "player_id": player.id}

    def _unsportsmanlike(
        self,
        side: int,
        kind: str = "delay",
        player: PlayerState | None = None,
        card: bool = False,
    ) -> dict[str, Any]:
        """Conducta antideportiva: retraso, simulación o falta de respeto."""
        profile = rules.UNSPORTSMANLIKE_TYPES.get(kind, rules.UNSPORTSMANLIKE_TYPES["delay"])
        lineup = self._lineup(side)
        if not lineup:
            return {"ok": False}
        player = player or lineup[0]
        self._inc_stat(side, "unsportsmanlike")
        self._add_event(
            "unsportsmanlike",
            side,
            player,
            f"Conducta antideportiva de {player.name}: {profile['label']}.",
        )
        if card or profile.get("card"):
            self._card(side)
        return {"ok": True, "kind": kind, "player_id": player.id}

    def compute_added_time(self, quarter: int) -> int:
        """Tiempo añadido por paradas reales del cuarto (lesiones, tarjetas, revisiones...)."""
        relevant = [
            event
            for event in self.events
            if int(event.get("quarter", 0)) == quarter
            and event.get("type") in (
                "injury",
                "card",
                "review",
                "protest",
                "unsportsmanlike",
                "pc_decision",
                "stroke",
            )
        ]
        weights = {"injury": 1.0, "card": 0.5, "review": 1.0, "protest": 0.25, "unsportsmanlike": 0.5, "pc_decision": 0.5, "stroke": 0.5}
        raw = sum(weights.get(str(event.get("type")), 0.0) for event in relevant)
        return max(0, min(rules.MAX_ADDED_TIME_MINUTES, int(round(raw))))

    def _tick_suspensions(self):
        """Descuenta las suspensiones temporales en tiempo de juego."""
        for side in (0, 1):
            for player_id, remaining in list(self.suspensions[side].items()):
                remaining -= MOMENT_MINUTES
                if remaining <= 0:
                    del self.suspensions[side][player_id]
                    player = next((p for p in self._raw_lineup(side) if p.id == player_id), None)
                    if player is not None:
                        self._add_event(
                            "card_return",
                            side,
                            player,
                            f"{player.name} vuelve al campo tras cumplir su suspensión.",
                        )
                else:
                    self.suspensions[side][player_id] = remaining

    def _injury(self, side: int):
        t = self._team(side)
        lineup = self._lineup(side)
        if not lineup:
            return
        p = self.rng.choice(lineup)
        severity = self.rng.choices(["leve", "moderada", "grave"], weights=[0.65, 0.28, 0.07])[0]
        injury_type = self.rng.choices(
            ["muscular", "esguince", "golpe", "fractura", "conmoción"],
            weights=[0.38, 0.27, 0.22, 0.08, 0.05],
        )[0]
        matches = {"leve": 1, "moderada": 2, "grave": 4}[severity]
        p.injury = max(p.injury, matches)
        p.injury_type = injury_type
        p.injury_severity = severity
        p.injury_started = self.match_date
        p.injury_expected = matches
        p.absence_note = f"{injury_type.capitalize()} ({severity})"
        injury = {
            "player_id": p.id,
            "player_name": p.name,
            "team_id": t.id,
            "team_name": t.name,
            "type": injury_type,
            "severity": severity,
            "matches": matches,
            "minute": int(self.minute),
            "quarter": self.quarter,
            "date": self.match_date,
        }
        p.injury_history = (p.injury_history + [injury])[-20:]
        self.injuries.append(injury)
        self._add_event(
            "injury",
            side,
            p,
            f"{p.name} ({t.name}) se lesiona ({injury_type}, {severity}); estará {matches} partido(s) de baja.",
        )

    def _substitute(self, side: int):
        if side not in self.auto_sub_sides:
            return
        if self._subs[side] >= 5:
            return
        lineup = self._lineup(side)
        bench = self._bench(side)
        if not bench:
            return
        tired = max([p for p in lineup if p.subposition != "Portero"] or lineup, key=lambda p: p.fatigue)
        if tired.fatigue < 55:
            return
        slot = "MED"
        if tired.subposition in ("Central", "Lateral"):
            slot = "CEN" if tired.subposition == "Central" else "LAT"
        elif tired.subposition == "Delantero":
            slot = "DEL"
        elif tired.subposition == "Portero":
            slot = "POR"
        candidates = sorted(bench, key=lambda p: p.selection_score(slot), reverse=True)
        if not candidates:
            return
        sub = candidates[0]
        self.manual_substitute(side, tired.id, sub.id, coaching=False)

    # ---------- bucle principal ----------
    def prepare(self):
        self.prepared = True

    def _possession_base(self) -> float:
        home_lineup = self._lineup(0)
        away_lineup = self._lineup(1)
        home_mid = _mean([p.attributes.get("pase", 50) + p.attributes.get("control", 50) for p in home_lineup]) / 2
        away_mid = _mean([p.attributes.get("pase", 50) + p.attributes.get("control", 50) for p in away_lineup]) / 2
        base = (
            0.5
            + (home_mid - away_mid) / 220
            + self.home.tactics.attack_mod() * 0.5
            - self.away.tactics.defense_mod() * 0.5
            - max(0, rules.PLAYERS_ON_FIELD - len(home_lineup)) * 0.015
            + max(0, rules.PLAYERS_ON_FIELD - len(away_lineup)) * 0.015
        )
        return max(0.30, min(0.70, base))

    def tactical_matchup_bonus(self, side: int) -> float:
        """Ventaja por leer la táctica rival (para UI y motor)."""
        t = self._team(side).tactics
        o = self._team(1 - side).tactics
        b = 0.0
        if o.mentality in ("ofensiva", "muy_ofensiva"):
            if t.press in ("alta", "muy_alta"):
                b += 1.5
            if t.mentality in ("defensiva", "muy_defensiva"):
                b += 1.0
        if o.mentality in ("defensiva", "muy_defensiva"):
            if t.mentality in ("ofensiva", "muy_ofensiva"):
                b += 1.0
            if t.tempo == "rapido":
                b += 0.5
        if o.press in ("alta", "muy_alta") and t.passing == "directo":
            b += 1.0
        if o.block == "bajo" and t.tempo == "rapido":
            b += 1.0
        if o.block == "alto" and t.passing in ("corto", "mixto"):
            b += 0.5
        if o.defensive_system == "zona_baja" and t.attack_system in ("directo", "contraataque"):
            b += 0.8
        if o.defensive_system == "zona_alta" and t.tempo == "rapido":
            b += 0.5
        if o.defensive_system == "individual_todo_campo" and t.passing == "directo":
            b += 0.4
        if o.defensive_system == "individual_mixta" and t.attack_system == "interior":
            b += 0.3
        if o.press_trigger == "siempre" and t.outlet == "directo":
            b += 0.4
        return min(3.0, b)

    def _choose_talk_style(self, side: int) -> str:
        team = self._team(side)
        diff = self.score[side] - self.score[1 - side]
        avg_fatigue = _mean([p.fatigue for p in self._lineup(side)])
        morale = team.morale
        if diff < 0:
            styles = ["arenga", "exigir"] if morale >= 10 else ["arenga", "calma"]
        elif diff == 0:
            styles = ["arenga", "calma", "confiar"]
        else:
            styles = ["calma", "confiar"] if diff > 1 else ["calma", "exigir", "confiar"]
        if avg_fatigue > 65:
            styles.append("calma")
        return self.rng.choice(styles)

    def apply_team_talk(self, side: int, style: str = "delegar", coach_label: str | None = None) -> dict:
        """Charla de vestuario. Estilos: arenga, calma, exigir, confiar, delegar/auto."""
        team = self._team(side)
        lineup = self._lineup(side)
        if self.talk_done[side]:
            return {
                "style": style,
                "coach": coach_label or "",
                "success": False,
                "bonus": 0.0,
                "morale_delta": 0,
                "message": "Ya se ha dado la charla de vestuario.",
            }
        delegated = style in ("delegar", "auto")
        if delegated:
            style = self._choose_talk_style(side)
            coach_label = coach_label or "El segundo entrenador"
            coach_rating = team.assistant_rating
        else:
            coach_label = coach_label or "Tú"
            coach_rating = team.manager_rating
        diff = self.score[side] - self.score[1 - side]
        morale = team.morale
        avg_fatigue = _mean([p.fatigue for p in lineup])
        avg_comp = _mean([p.attributes.get("competitividad", 50) for p in lineup])
        avg_leader = _mean([p.attributes.get("liderazgo", 50) for p in lineup])
        if style == "arenga":
            base = 0.55 + (avg_comp - 50) / 200 + (morale - 10) / 50
            if diff < 0:
                base += 0.10
            elif diff > 1:
                base -= 0.15
            if morale <= 6:
                base -= 0.15
            success_bonus, fail_bonus = 1.4, -0.8
        elif style == "calma":
            if diff > 0:
                base, success_bonus, fail_bonus = 0.68, 0.9, -0.3
            elif diff == 0:
                base, success_bonus, fail_bonus = 0.62, 0.5, -0.2
            else:
                base, success_bonus, fail_bonus = 0.42, 0.2, -0.4
            if avg_fatigue > 60:
                base += 0.08
        elif style == "exigir":
            base = 0.50 + (avg_comp - 50) / 150 + (avg_leader - 50) / 200
            if diff < 0:
                base += 0.10
            elif diff > 0:
                base -= 0.10
            if morale <= 7:
                base -= 0.20
            success_bonus, fail_bonus = 1.8, -1.2
        else:  # confiar
            if diff >= 0:
                base, success_bonus, fail_bonus = 0.66, 0.6, -0.4
            else:
                base, success_bonus, fail_bonus = 0.32, -0.2, -0.8
        base += (coach_rating - 50) / 200
        base = max(0.15, min(0.90, base))
        success = self.rng.random() < base
        bonus = success_bonus if success else fail_bonus
        morale_delta = 1 if success else (-1 if style in ("arenga", "exigir") else 0)
        team.morale = max(1, min(20, team.morale + morale_delta))
        for p in lineup:
            p.morale = max(1, min(20, p.morale + morale_delta))
        self.talk_bonus[side] = round(bonus, 2)
        self.talk_done[side] = True
        labels = {"arenga": "arenga", "calma": "calma", "exigir": "exigencia", "confiar": "confianza"}
        outcome = "El equipo responde" if success else "El mensaje no cala"
        message = f"{coach_label} da una charla de {labels.get(style, style)}. {outcome}. Bonus {bonus:+.1f}."
        self._add_event("talk", side, None, message)
        return {
            "style": style,
            "coach": coach_label,
            "success": success,
            "bonus": round(bonus, 2),
            "morale_delta": morale_delta,
            "message": message,
        }

    def _ai_adjust(self, side: int):
        if side not in self.ai_sides:
            return
        team = self._team(side)
        opp = self._team(1 - side)
        q = self.quarter
        diff = self.score[side] - self.score[1 - side]
        avg_fatigue = _mean([p.fatigue for p in self._lineup(side)])
        chance = 0.50 + (team.manager_rating - 50) / 250
        if self.rng.random() > chance:
            return
        before = (
            team.tactics.mentality,
            team.tactics.press,
            team.tactics.block,
            team.tactics.tempo,
            team.tactics.passing,
        )
        if diff < 0 and q >= 2:
            if q >= 3:
                team.tactics.mentality = "muy_ofensiva"
                team.tactics.tempo = "rapido"
                team.tactics.press = "alta"
                team.tactics.block = "alto"
                team.tactics.defensive_system = "individual_todo_campo"
                team.tactics.attack_system = "directo"
                team.tactics.press_trigger = "siempre"
            else:
                team.tactics.mentality = "ofensiva"
                team.tactics.tempo = "rapido"
                team.tactics.press = "alta"
                team.tactics.attack_system = "contraataque"
        elif diff > 0 and q >= 3:
            team.tactics.mentality = "defensiva"
            team.tactics.tempo = "lento"
            team.tactics.press = "media"
            team.tactics.block = "bajo"
            team.tactics.defensive_system = "zona_baja"
            team.tactics.attack_system = "contraataque"
            team.tactics.press_trigger = "pase_atras"
        elif diff == 0 and q >= 3:
            team.tactics.mentality = "ofensiva"
            team.tactics.tempo = "rapido"
            team.tactics.attack_system = "posicional"
        # lectura del rival
        if opp.tactics.press in ("alta", "muy_alta"):
            team.tactics.passing = "directo"
        if opp.tactics.block == "bajo":
            team.tactics.tempo = "rapido"
        elif opp.tactics.block == "alto":
            team.tactics.passing = "corto"
        # fatiga: no se puede presionar eternamente
        if avg_fatigue > 65:
            if team.tactics.press in ("alta", "muy_alta"):
                team.tactics.press = "media"
            if team.tactics.tempo == "rapido":
                team.tactics.tempo = "normal"
        after = (
            team.tactics.mentality,
            team.tactics.press,
            team.tactics.block,
            team.tactics.tempo,
            team.tactics.passing,
        )
        if after != before:
            self._add_event(
                "tactic",
                side,
                None,
                f"{team.name} ajusta su planteamiento para el {q + 1}º cuarto: "
                f"mentalidad {team.tactics.mentality.replace('_', ' ')}, "
                f"presión {team.tactics.press.replace('_', ' ')}, "
                f"tempo {team.tactics.tempo}.",
            )
        if avg_fatigue > 60 and self._subs[side] < 5 and side in self.auto_sub_sides:
            self._substitute(side)

    def advance_moment(self) -> list[dict[str, Any]]:
        """Avanza un momento de juego (~1,1 minutos) y devuelve los eventos nuevos."""
        if self.finished:
            return []
        self.prepare()
        if self.quarter > 4:
            self.finalize()
            return []
        self._tick_suspensions()
        start = len(self.events)
        m = self.moment_in_quarter
        self.minute = int((self.quarter - 1) * QUARTER_MINUTES + (m + 1) * (QUARTER_MINUTES / MOMENTS_PER_QUARTER))
        base_home_pos = self._possession_base()
        ha, hd, aa, ad = self._attack_defense()
        # posesión
        if self.zone == "middle" and self.rng.random() < 0.30:
            self.possession = 0 if self.rng.random() < base_home_pos else 1
        side = self.possession
        self.possession_counts[side] += 1
        total_pos = self.possession_counts[0] + self.possession_counts[1]
        if total_pos:
            self.stats[0]["possession"] = round(100 * self.possession_counts[0] / total_pos, 1)
            self.stats[1]["possession"] = round(100 - self.stats[0]["possession"], 1)
        t = self._team(side)
        opp = 1 - side
        attack = ha if side == 0 else aa
        defense = ad if side == 0 else hd
        # fatiga por momento: ambos equipos están en el campo
        for team_side, team_obj in ((0, self.home), (1, self.away)):
            fat_team = 0.35 + max(0, team_obj.tactics.fatigue_mod()) * 2.5
            for p in self._lineup(team_side):
                p.fatigue = min(100.0, p.fatigue + fat_team)
        # minutos para los jugadores que están realmente en el campo
        for team_side in (0, 1):
            for p in self._lineup(team_side):
                self.player_minutes[p.id] = self.player_minutes.get(p.id, 0) + 1
        # decisiones según zona
        r = self.rng.random()
        if self.zone == "own_23":
            if r < 0.58:
                # salida
                self._inc_stat(side, "passes")
                if self.rng.random() < 0.85:
                    self._inc_stat(side, "passes_completed")
                    self.zone = "middle"
                else:
                    self.possession = opp
                    self.zone = "attacking_23"
            elif r < 0.74:
                self._inc_stat(side, "aerials")
                self._add_event(
                    "aerial", side, self._lineup(side)[0], f"{t.name} busca el aerial para superar la presión."
                )
                self.zone = "middle"
                if self.rng.random() < 0.30:
                    self.possession = opp
            elif r < 0.87:
                self._foul(side)
            else:
                self._add_event("info", side, None, f"{t.name} circula la bola en su campo.")
                self.zone = "middle"
        elif self.zone == "middle":
            if r < 0.44:
                self._inc_stat(side, "passes")
                success = self.rng.random() < (0.78 + (attack - defense) / 250)
                if success:
                    self._inc_stat(side, "passes_completed")
                    self.zone = "attacking_23" if self.rng.random() < 0.70 else "middle"
                else:
                    self._inc_stat(opp, "tackles")
                    self.possession = opp
            elif r < 0.56:
                self._inc_stat(side, "passes")
                if self.rng.random() < 0.75:
                    self._inc_stat(side, "passes_completed")
                    self.zone = "attacking_23"
                else:
                    self.possession = opp
            elif r < 0.68:
                self._inc_stat(side, "aerials")
                self._add_event(
                    "aerial", side, self._lineup(side)[0], f"{t.name} lanza un aerial para cambiar de carril."
                )
                if self.rng.random() < 0.60:
                    self.zone = "attacking_23"
                else:
                    self.possession = opp
            elif r < 0.77:
                self._add_event(
                    "three_d",
                    side,
                    self._lineup(side)[0],
                    f"{self._lineup(side)[0].name} usa un 3D para superar el stick.",
                )
                if self.rng.random() < 0.60:
                    self.zone = "attacking_23"
                else:
                    self.possession = opp
            elif r < 0.88:
                self._inc_stat(side, "tackles")
                self._add_event(
                    "tackle", side, self._lineup(side)[0], f"{self._lineup(side)[0].name} roba con un tackle limpio."
                )
                self.possession = side
            elif r < 0.96:
                self._foul(side)
            else:
                self._card(side)
        elif self.zone == "attacking_23":
            if r < 0.34:
                self._inc_stat(side, "circle_entries")
                self._add_event("circle_entry", side, None, f"{t.name} entra al círculo con peligro.")
                self.zone = "circle"
            elif r < 0.55:
                self._penalty_corner(side)
            elif r < 0.73:
                self._shot(side, "open")
            elif r < 0.82:
                self._inc_stat(side, "aerials")
                self._add_event("aerial", side, self._lineup(side)[0], f"{t.name} busca el segundo palo con un aerial.")
                self.zone = "circle" if self.rng.random() < 0.6 else "middle"
            elif r < 0.90:
                self._inc_stat(side, "passes")
                if self.rng.random() < 0.75:
                    self._inc_stat(side, "passes_completed")
                    self.zone = "circle" if self.rng.random() < 0.50 else "attacking_23"
                else:
                    self.possession = opp
                    self.zone = "middle"
            elif r < 0.97:
                self._foul(side)
            else:
                self._card(side)
        else:  # circle
            if r < 0.44:
                self._shot(side, "open")
            elif r < 0.60:
                self._penalty_corner(side)
            elif r < 0.68:
                self._stroke(side)
            elif r < 0.84:
                self._shot(side, "deflection")
            elif r < 0.92:
                self._add_event(
                    "chance", side, self._lineup(side)[0], f"{t.name} genera una ocasión, pero la defensa despeja."
                )
                self.possession = opp
                self.zone = "middle"
            elif r < 0.96:
                self._foul(side)
            else:
                self._card(side)
        # lesión y cambios automáticos
        if self.rng.random() < 0.0018 * (1 + sum(p.fatigue for p in self._lineup(side)) / 300):
            self._injury(side)
        auto_sub_roll = self.rng.random()
        if side in self.auto_sub_sides and auto_sub_roll < 0.08:
            self._substitute(side)
        self.moment_in_quarter += 1
        self.total_moments += 1
        if self.moment_in_quarter >= MOMENTS_PER_QUARTER:
            self._end_quarter()
        return self.events[start:]

    def _end_quarter(self):
        for side in (0, 1):
            for p in self._lineup(side):
                p.fatigue = max(0.0, p.fatigue - 1.5)
        if self.quarter < 4:
            for side in sorted(self.ai_sides):
                self._ai_adjust(side)
            if self.quarter == 2:
                for side in sorted(self.auto_talk_sides):
                    if not self.talk_done[side]:
                        self.apply_team_talk(side, "auto", coach_label="El cuerpo técnico")
            if self.quarter == 3:
                self.talk_bonus[0] *= 0.5
                self.talk_bonus[1] *= 0.5
            self._add_event(
                "info",
                None,
                None,
                f"Final del {self.quarter}º cuarto: {self.home.name} {self.score[0]}-{self.score[1]} {self.away.name}.",
                minute=int(self.quarter * QUARTER_MINUTES),
            )
        quarter = self.quarter
        added = self.compute_added_time(quarter)
        self.added_time[quarter] = added
        if added > 0:
            self._add_event(
                "added_time",
                None,
                None,
                f"El árbitro añade {added} minuto(s) al final del {quarter}º cuarto.",
                minute=int(quarter * QUARTER_MINUTES),
            )
        self.quarter += 1
        self.moment_in_quarter = 0
        if self.quarter > 4:
            self.finalize()

    def advance_quarter(self) -> list[dict[str, Any]]:
        """Avanza el cuarto actual (o lo que quede de él) y devuelve sus eventos."""
        if self.finished:
            return []
        self.prepare()
        start = len(self.events)
        q = self.quarter
        while not self.finished and self.quarter == q:
            self.advance_moment()
        return self.events[start:]

    def simulate(self) -> MatchResult:
        self.prepare()
        while not self.finished:
            self.advance_quarter()
        return self.result

    def finalize(self) -> MatchResult | None:
        if self.finished and self.result is not None:
            return self.result
        self.finished = True
        total_pos = self.possession_counts[0] + self.possession_counts[1]
        if total_pos:
            self.stats[0]["possession"] = round(100 * self.possession_counts[0] / total_pos, 1)
            self.stats[1]["possession"] = round(100 - self.stats[0]["possession"], 1)
        shootout = {}
        if self.knockout and self.score[0] == self.score[1]:
            shootout = self._shootout()
        home_ratings: dict[str, float] = {}
        away_ratings: dict[str, float] = {}
        for side, team, ratings in ((0, self.home, home_ratings), (1, self.away, away_ratings)):
            by_id = {p.id: p for p in team.players}
            for pid in self.played[side]:
                p = by_id.get(pid)
                if not p:
                    continue
                st = self.player_stats.setdefault(
                    pid,
                    {
                        "goals": 0,
                        "assists": 0,
                        "shots": 0,
                        "saves": 0,
                        "green": 0,
                        "yellow": 0,
                        "red": 0,
                        "rating": 6.0,
                    },
                )
                rating = self._rating(p)
                st["rating"] = rating
                ratings[pid] = rating
                p.apps += 1
                p.rating_sum += rating
                p.season_goals += st["goals"]
                p.season_assists += st["assists"]
                p.form = max(1.0, min(10.0, p.form * 0.85 + rating * 0.15))
        if self.score[0] > self.score[1]:
            self.home.morale = min(20, self.home.morale + 1)
            self.away.morale = max(1, self.away.morale - 1)
        elif self.score[1] > self.score[0]:
            self.away.morale = min(20, self.away.morale + 1)
            self.home.morale = max(1, self.home.morale - 1)
        self.result = MatchResult(
            home_id=self.home.id,
            away_id=self.away.id,
            home_goals=self.score[0],
            away_goals=self.score[1],
            events=self.events,
            home_stats=self.stats[0],
            away_stats=self.stats[1],
            home_ratings=home_ratings,
            away_ratings=away_ratings,
            injuries=self.injuries,
            cards=self.cards,
            player_minutes=self.player_minutes,
            shootout=shootout,
            referee=self.referee,
            reviews=self.reviews,
            added_time=self.added_time,
        )
        return self.result

    def live_snapshot(self) -> dict:
        return {
            "quarter": min(self.quarter, 4),
            "minute": self.minute,
            "score": list(self.score),
            "finished": self.finished,
            "home_stats": self.stats[0],
            "away_stats": self.stats[1],
            "home_management": self.home.management_profile(self._lineup(0)),
            "away_management": self.away.management_profile(self._lineup(1)),
            "home_tactical_bonus": round(self.tactical_matchup_bonus(0), 2),
            "away_tactical_bonus": round(self.tactical_matchup_bonus(1), 2),
            "referee": self.referee,
            "opposition": {
                "side": self.opposition_side,
                "effect": self.opposition_effect(self.opposition_side) if self.opposition_side is not None else {"attack": 0.0, "defense": 0.0, "players": 0.0},
                "instructions": self.opposition,
            },
            "referrals": [self.referrals.get(0, 0), self.referrals.get(1, 0)],
            "added_time": self.added_time,
            "protest_used": [self.protest_used.get(0, False), self.protest_used.get(1, False)],
            "last_decision": self.last_decision,
            "reviews": self.reviews,
        }

    def player_live_rows(self, side: int) -> list[dict]:
        rows = []
        for p in self._field_lineup(side):
            st = self.player_stats.get(p.id, {})
            rows.append(
                {
                    "id": p.id,
                    "name": p.name,
                    "position": p.subposition,
                    "minutes": self.player_minutes.get(p.id, 0),
                    "goals": st.get("goals", 0),
                    "assists": st.get("assists", 0),
                    "shots": st.get("shots", 0),
                    "saves": st.get("saves", 0),
                    "green": st.get("green", 0),
                    "yellow": st.get("yellow", 0),
                    "red": st.get("red", 0),
                    "rating": self._rating(p),
                    "fatigue": round(p.fatigue, 1),
                    "injury": p.injury,
                    "suspension": p.suspension,
                }
            )
        return rows

    def bench_live_rows(self, side: int) -> list[dict]:
        rows = []
        for p in self._bench(side):
            rows.append(
                {
                    "id": p.id,
                    "name": p.name,
                    "position": p.subposition,
                    "overall": p.overall,
                    "fatigue": round(p.fatigue, 1),
                    "form": round(p.form, 1),
                    "injury": p.injury,
                    "suspension": p.suspension,
                }
            )
        return rows

    def manual_substitute(self, side: int, out_id: str, in_id: str, coaching: bool = True) -> tuple[bool, str]:
        if self.finished:
            return False, "El partido ha terminado."
        if side not in (0, 1):
            return False, "Equipo no válido."
        if self._subs[side] >= 5:
            return False, "No quedan cambios disponibles."
        raw_lineup = self._raw_lineup(side)
        bench = self._bench(side)
        out = next((p for p in raw_lineup if p.id == out_id), None)
        inn = next((p for p in bench if p.id == in_id), None)
        if out is None:
            return False, "El jugador que sale no está en el campo."
        if out.id in self.red_cards[side] or self.suspensions[side].get(out.id, 0.0) > 0:
            return False, "No se puede sustituir a un jugador suspendido durante su suspensión."
        if out.suspension > 0:
            return False, "No se puede sustituir a un jugador sancionado para este partido."
        if out not in self._lineup(side) and out.injury <= 0:
            return False, "El jugador que sale no está disponible en el campo."
        if inn is None:
            return False, "El jugador que entra no está en el banquillo."
        if not inn.available:
            return False, "El jugador que entra no está disponible."
        raw_lineup[raw_lineup.index(out)] = inn
        bench.remove(inn)
        self._subs[side] += 1
        self.played[side].add(inn.id)
        self.player_stats.setdefault(
            inn.id, {"goals": 0, "assists": 0, "shots": 0, "saves": 0, "green": 0, "yellow": 0, "red": 0, "rating": 6.0}
        )
        self.player_minutes.setdefault(inn.id, 0)
        if coaching:
            gain = 0.0
            if out.fatigue >= 45 and inn.fatigue < out.fatigue - 10:
                gain = 0.6
            elif out.fatigue >= 30:
                gain = 0.3
            self.live_bonus[side] = min(2.0, self.live_bonus[side] + gain)
        self._add_event(
            "substitution", side, inn, f"Cambio en {self._team(side).name}: entra {inn.name} por {out.name}."
        )
        return True, f"Entra {inn.name} por {out.name}."

    def _shootout(self) -> dict:
        # 5 lanzadores + muerte súbita. El lanzador manual de stroke abre la tanda.
        def takers(team: TeamState, lineup: list[PlayerState]) -> list[PlayerState]:
            specialist = team.specialists(lineup).get("stroke_taker")
            ordered = sorted(lineup, key=lambda p: p.attributes.get("stroke_shot", 0), reverse=True)
            if specialist and specialist in ordered:
                ordered = [specialist] + [p for p in ordered if p.id != specialist.id]
            return ordered[:5]

        home_takers = takers(self.home, self._lineup(0))
        away_takers = takers(self.away, self._lineup(1))
        hgk = self._gk(0)
        agk = self._gk(1)
        hs = as_ = 0
        log = []
        for i in range(5):
            hp = home_takers[i % len(home_takers)]
            ap = away_takers[i % len(away_takers)]
            h_goal = self.rng.random() < max(
                0.55,
                min(0.92, 0.78 + (hp.attributes.get("stroke_shot", 50) - agk.attributes.get("stroke_save", 50)) / 260),
            )
            a_goal = self.rng.random() < max(
                0.55,
                min(0.92, 0.78 + (ap.attributes.get("stroke_shot", 50) - hgk.attributes.get("stroke_save", 50)) / 260),
            )
            hs += int(h_goal)
            as_ += int(a_goal)
            log.append({"round": i + 1, "home": hp.name, "home_goal": h_goal, "away": ap.name, "away_goal": a_goal})
        while hs == as_:
            hp = self.rng.choice(home_takers)
            ap = self.rng.choice(away_takers)
            h_goal = self.rng.random() < 0.7
            a_goal = self.rng.random() < 0.7
            hs += int(h_goal)
            as_ += int(a_goal)
            log.append(
                {"round": len(log) + 1, "home": hp.name, "home_goal": h_goal, "away": ap.name, "away_goal": a_goal}
            )
        winner = self.home.id if hs > as_ else self.away.id
        return {"home_score": hs, "away_score": as_, "winner_id": winner, "log": log}


def quick_sim(
    home: TeamState, away: TeamState, seed: int, neutral: bool = False, knockout: bool = False
) -> MatchResult:
    rng = random.Random(seed)
    return MatchEngine(home, away, rng, neutral=neutral, knockout=knockout).simulate()
