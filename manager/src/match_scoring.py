"""Mixin de scoring del motor de partido."""

from __future__ import annotations

import zlib
from typing import Any

from . import rules
from .match_shared import (
    _weighted_choice,
)
from .models import PlayerState


class ScoringMixin:
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

    def _credit_goal(
        self, side: int, scorer: PlayerState, assister: PlayerState | None, kind: str
    ) -> None:
        t = self._team(side)
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

    def _goal(self, side: int, scorer: PlayerState, assister: PlayerState | None, kind: str):
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
        self._credit_goal(side, scorer, assister, kind)

    def _goal_offence(self, side: int, scorer: PlayerState, kind: str) -> str | None:
        """Infracción de ataque determinista que anula un gol.

        No consume el RNG principal para no alterar la secuencia de partidos
        existentes. El resultado depende del contexto y del número de tiros.
        """
        key = "|".join(
            (
                str(self.match_date),
                self.home.id,
                self.away.id,
                str(self.quarter),
                str(int(self.minute)),
                str(side),
                scorer.id,
                kind,
                str(int(self.stats[side].get("shots", 0))),
            )
        )
        roll = (zlib.crc32(key.encode("utf-8")) % 10000) / 10000
        if roll < 0.035:
            return "foot"
        if roll < 0.060:
            return "back_stick"
        if roll < 0.078:
            return "hand"
        return None

    def _outside_circle_deflection(self, side: int, scorer: PlayerState, kind: str) -> bool:
        """Determina si un tiro desde fuera del círculo se desvía dentro.

        Un disparo directo desde fuera no puede ser gol. Si el modelo lo trata
        como desvío de un compañero dentro del círculo, el gol es válido.
        """
        key = "|".join(
            (
                str(self.match_date),
                self.home.id,
                self.away.id,
                str(self.quarter),
                str(int(self.minute)),
                str(side),
                scorer.id,
                kind,
                str(int(self.stats[side].get("shots", 0))),
                "outside_circle_deflection",
            )
        )
        return (zlib.crc32(key.encode("utf-8")) % 100) < 55

    def _deflector(self, side: int, shooter: PlayerState) -> PlayerState:
        candidates = [player for player in self._lineup(side) if player.id != shooter.id]
        if not candidates:
            return shooter
        key = "|".join(
            (
                str(self.match_date),
                self.home.id,
                self.away.id,
                str(self.quarter),
                str(int(self.minute)),
                shooter.id,
                "deflector",
            )
        )
        return candidates[zlib.crc32(key.encode("utf-8")) % len(candidates)]

    def _shot(
        self,
        side: int,
        kind: str = "open",
        offence: str | None = None,
        deflected: bool | None = None,
    ):
        self._clear_advantage(side)
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
            # Un gol solo puede concederse si la bola se juega dentro del
            # círculo. Un disparo desde fuera solo vale si se desvía dentro.
            if self.zone != "circle":
                if deflected is None:
                    deflected = self._outside_circle_deflection(side, scorer, kind)
                if deflected:
                    deflector = self._deflector(side, scorer)
                    self._goal(side, deflector, scorer, "deflection")
                else:
                    self._disallowed_goal(side, scorer, assister, kind, "outside_circle")
            else:
                if offence is None:
                    offence = self._goal_offence(side, scorer, kind)
                if offence in rules.ATTACKING_GOAL_OFFENCES:
                    self._disallowed_goal(side, scorer, assister, kind, offence)
                else:
                    self._goal(side, scorer, assister, kind)
        else:
            self._inc_stat(opp, "saves")
            self.player_stats[gk.id]["saves"] += 1
            self._add_event("save", side, gk, f"{gk.name} responde con una parada firme al disparo de {scorer.name}.")
            self.possession = opp
            self.zone = "middle"
