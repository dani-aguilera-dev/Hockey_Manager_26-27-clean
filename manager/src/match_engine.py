"""Motor de partido por fases para la Fase 1.

No es un motor físicas 2D/3D: simula momentos de juego y genera eventos
explicables a partir de los 37 atributos, la táctica, la fatiga y el contexto.
"""

from __future__ import annotations

import random
from typing import Any

from . import rules
from .match_referee import RefereeMixin
from .match_scoring import ScoringMixin
from .match_shared import (
    HOME_ADVANTAGE_ATTACK as HOME_ADVANTAGE_ATTACK,
)
from .match_shared import (
    HOME_ADVANTAGE_DEFENSE as HOME_ADVANTAGE_DEFENSE,
)
from .match_shared import (
    MOMENT_MINUTES as MOMENT_MINUTES,
)
from .match_shared import (
    MOMENTS_PER_QUARTER as MOMENTS_PER_QUARTER,
)
from .match_shared import (
    QUARTER_MINUTES as QUARTER_MINUTES,
)
from .match_shared import (
    MatchResult as MatchResult,
)
from .match_simulation import SimulationMixin
from .match_tactics import TacticsMixin
from .models import PlayerState, TeamState


class MatchEngine(SimulationMixin, RefereeMixin, ScoringMixin, TacticsMixin):
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
        match_plans: list[dict[str, Any]] | None = None,
        plan_side: int | None = None,
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
        # Momentum en [-1, 1]: positivo favorece al local. Se alimenta de
        # goles, ocasiones, paradas y tarjetas, y decae con el tiempo.
        self.momentum = 0.0
        self.momentum_log: list[dict[str, Any]] = []
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
                "decisions": 0,
                "key_passes": 0,
                "turnovers": 0,
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
        self.match_plans = list(match_plans or [])
        self.plan_side = plan_side
        self.applied_plans: set[str] = set()
        self.plan_effect_cache: dict[str, Any] = {"attack": 0.0, "defense": 0.0, "plans": []}
        self.pending_advantage: dict[str, Any] | None = None
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
            "free_hits": 0,
            "goals": 0,
            "fouls": 0,
            "advantage": 0,
            "advantage_failed": 0,
            "goals_disallowed": 0,
            "foot_goals_disallowed": 0,
            "back_stick_goals_disallowed": 0,
            "hand_goals_disallowed": 0,
            "outside_circle_goals_disallowed": 0,
            "dangerous_play": 0,
            "dangerous_sanction": 0,
            "distance_5m": 0,
            "free_hit_10m": 0,
            "pc_denied": 0,
            "pc_retake": 0,
            "stroke_awarded": 0,
            "stroke_retake": 0,
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







    # ---------- videoarbitraje ----------




    # ---------- set pieces ----------


    # ---------- acciones de juego ----------



















    # ---------- bucle principal ----------
    def prepare(self):
        self.prepared = True

















def quick_sim(
    home: TeamState, away: TeamState, seed: int, neutral: bool = False, knockout: bool = False
) -> MatchResult:
    rng = random.Random(seed)
    return MatchEngine(home, away, rng, neutral=neutral, knockout=knockout).simulate()