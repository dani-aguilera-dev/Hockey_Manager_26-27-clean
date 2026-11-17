"""Mixin de tactics del motor de partido."""

from __future__ import annotations

import random
import zlib
from typing import Any

from . import rules
from .match_shared import (
    HOME_ADVANTAGE_ATTACK,
    HOME_ADVANTAGE_DEFENSE,
    _mean,
)
from .models import TACTIC_MODS, PlayerState


class TacticsMixin:
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

    def match_plan_effect(self, side: int) -> dict[str, Any]:
        """Delta táctico de los planes de partido activos para un equipo.

        No modifica la táctica persistente: calcula la diferencia entre las
        instrucciones del plan y la táctica base para ese momento del partido.
        """
        if self.plan_side != side or not self.match_plans:
            return {"attack": 0.0, "defense": 0.0, "plans": []}
        diff = self.score[side] - self.score[1 - side]
        situation = "leading" if diff > 0 else ("trailing" if diff < 0 else "drawing")
        labels = {"leading": "por delante", "drawing": "empatados", "trailing": "por detrás"}
        tactics = self._team(side).tactics
        attack = 0.0
        defense = 0.0
        active: list[str] = []
        for plan in self.match_plans:
            if not plan.get("enabled", True):
                continue
            if plan.get("situation") != situation:
                continue
            if self.minute < int(plan.get("from_minute", 45) or 0):
                continue
            instructions = plan.get("instructions") or {}
            for field_name, value in instructions.items():
                if field_name not in TACTIC_MODS or value not in TACTIC_MODS[field_name]:
                    continue
                old_value = getattr(tactics, field_name, "")
                if old_value == value:
                    continue
                old_mod = TACTIC_MODS[field_name].get(old_value, (0.0, 0.0))
                new_mod = TACTIC_MODS[field_name][value]
                attack += new_mod[0] - old_mod[0]
                defense += new_mod[1] - old_mod[1]
            active.append(str(plan.get("id", "")))
            if str(plan.get("id", "")) not in self.applied_plans:
                self.applied_plans.add(str(plan.get("id", "")))
                self._add_event(
                    "match_plan",
                    side,
                    None,
                    f"Plan «{plan.get('name', '')}» activado: {labels[situation]} desde el minuto {int(plan.get('from_minute', 45) or 0)}.",
                )
        result = {
            "attack": round(max(-0.15, min(0.15, attack)), 3),
            "defense": round(max(-0.15, min(0.15, defense)), 3),
            "plans": active,
        }
        self.plan_effect_cache = result
        return result

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
        if self.plan_side == 0:
            plan_effect = self.match_plan_effect(0)
            ha += plan_effect["attack"]
            hd += plan_effect["defense"]
        elif self.plan_side == 1:
            plan_effect = self.match_plan_effect(1)
            aa += plan_effect["attack"]
            ad += plan_effect["defense"]
        # El momentum premia al equipo que está dominando los últimos momentos.
        ha += self.momentum * 1.8
        hd += self.momentum * 1.1
        aa -= self.momentum * 1.8
        ad -= self.momentum * 1.1
        return max(25.0, ha), max(25.0, hd), max(25.0, aa), max(25.0, ad)

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
            + self.momentum * 0.04
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

    # ---------- decisiones por jugador y momentum ----------
    def _decision_rng(self, salt: str) -> random.Random:
        """RNG derivado para decisiones de jugador.

        No consume el RNG principal: así los partidos ya guardados conservan
        su secuencia y el resultado sigue siendo reproducible.
        """
        key = "|".join(
            (
                str(self.match_date),
                self.home.id,
                self.away.id,
                str(self.quarter),
                str(int(self.minute)),
                self.zone,
                salt,
            )
        )
        return random.Random(zlib.crc32(key.encode("utf-8")))

    def _carrier(self, side: int, zone: str | None = None) -> PlayerState:
        """Elige al portador de la bola según zona, rol, atributos y fatiga."""
        zone = zone or self.zone
        lineup = [p for p in self._lineup(side) if p.subposition != "Portero"] or self._lineup(side)
        weights: list[float] = []
        for p in lineup:
            base = 20.0 + p.attributes.get("control", 50) * 0.5 + p.attributes.get("pase", 50) * 0.3
            if zone == "own_23":
                if p.subposition in ("Central", "Lateral"):
                    base += 25
                elif p.subposition == "Medio":
                    base += 10
                elif p.subposition == "Delantero":
                    base -= 5
            elif zone == "middle":
                if p.subposition == "Medio":
                    base += 30
                elif p.subposition == "Delantero":
                    base += 10
            elif zone in ("attacking_23", "circle"):
                if p.subposition == "Delantero":
                    base += 30
                elif p.subposition == "Medio":
                    base += 18
            base -= max(0.0, p.fatigue - 55.0) * 0.25
            weights.append(max(1.0, base))
        return self._decision_rng("carrier").choices(lineup, weights=weights, k=1)[0]

    def _record_carrier(self, player: PlayerState, kind: str, success: bool) -> None:
        st = self.player_stats.setdefault(player.id, {})
        st["decisions"] = int(st.get("decisions", 0)) + 1
        if success and kind in ("pass", "carry") and self.zone in ("attacking_23", "circle"):
            st["key_passes"] = int(st.get("key_passes", 0)) + 1
        if not success:
            st["turnovers"] = int(st.get("turnovers", 0)) + 1

    def _shift_momentum(self, side: int, amount: float, reason: str = "") -> None:
        """Mueve el momentum hacia el equipo indicado y registra el cambio."""
        before = self.momentum
        delta = amount if side == 0 else -amount
        self.momentum = max(-1.0, min(1.0, before * 0.97 + delta))
        if abs(self.momentum - before) < 0.0005:
            return
        self.momentum_log.append(
            {
                "minute": int(self.minute),
                "quarter": self.quarter,
                "side": side,
                "amount": round(self.momentum - before, 3),
                "momentum": round(self.momentum, 3),
                "reason": reason,
            }
        )
        crossed = (before < 0.30 <= self.momentum) or (before > -0.30 >= self.momentum)
        if crossed:
            beneficiary = 0 if self.momentum > 0 else 1
            self._add_event(
                "momentum",
                beneficiary,
                None,
                f"El partido cambia de ritmo a favor de {self._team(beneficiary).name}.",
            )

