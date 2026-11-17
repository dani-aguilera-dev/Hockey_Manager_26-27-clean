"""Mixin de simulation del motor de partido."""

from __future__ import annotations

from typing import Any

from .match_shared import (
    MOMENTS_PER_QUARTER,
    QUARTER_MINUTES,
    MatchResult,
)
from .models import PlayerState, TeamState


class SimulationMixin:
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

    def advance_moment(self) -> list[dict[str, Any]]:
        """Avanza un momento de juego (~1,1 minutos) y devuelve los eventos nuevos."""
        if self.finished:
            return []
        self.prepare()
        if self.quarter > 4:
            self.finalize()
            return []
        self._tick_suspensions()
        self.momentum *= 0.985
        start = len(self.events)
        m = self.moment_in_quarter
        self.minute = int((self.quarter - 1) * QUARTER_MINUTES + (m + 1) * (QUARTER_MINUTES / MOMENTS_PER_QUARTER))
        self._resolve_advantage()
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
        carrier = self._carrier(side)
        fatigue_pen = max(0.0, carrier.fatigue - 55.0) / 100.0 * 0.12
        # fatiga individual: depende del rol, la resistencia y la carga táctica
        for team_side, team_obj in ((0, self.home), (1, self.away)):
            fat_team = 0.35 + max(0, team_obj.tactics.fatigue_mod()) * 2.5
            for p in self._lineup(team_side):
                role_load = 1.0
                if p.subposition == "Portero":
                    role_load = 0.55
                elif p.subposition == "Medio":
                    role_load = 1.12
                elif p.subposition == "Delantero":
                    role_load = 1.06
                stamina = float(p.attributes.get("resistencia", 50))
                load = fat_team * role_load * max(0.55, 1.15 - stamina / 250)
                p.fatigue = min(100.0, p.fatigue + max(0.15, load))
        # minutos para los jugadores que están realmente en el campo
        for team_side in (0, 1):
            for p in self._lineup(team_side):
                self.player_minutes[p.id] = self.player_minutes.get(p.id, 0) + 1
        # decisiones según zona
        r = self.rng.random()
        if self.zone == "own_23":
            if r < 0.58:
                # salida con el portador como protagonista
                self._inc_stat(side, "passes")
                success = 0.85 + (carrier.attributes.get("pase", 50) - 50) / 500 - fatigue_pen
                if self.rng.random() < success:
                    self._inc_stat(side, "passes_completed")
                    self._record_carrier(carrier, "pass", True)
                    self.zone = "middle"
                else:
                    self._record_carrier(carrier, "pass", False)
                    self.possession = opp
                    self.zone = "attacking_23"
            elif r < 0.74:
                self._inc_stat(side, "aerials")
                self._add_event("aerial", side, carrier, f"{carrier.name} busca el aerial para superar la presión.")
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
                chance = 0.78 + (attack - defense) / 250 + (carrier.attributes.get("pase", 50) - 50) / 400 - fatigue_pen
                success = self.rng.random() < chance
                if success:
                    self._inc_stat(side, "passes_completed")
                    self._record_carrier(carrier, "pass", True)
                    self.zone = "attacking_23" if self.rng.random() < 0.70 else "middle"
                else:
                    self._inc_stat(opp, "tackles")
                    self._record_carrier(carrier, "pass", False)
                    self.possession = opp
            elif r < 0.56:
                self._inc_stat(side, "passes")
                chance = 0.75 + (carrier.attributes.get("pase", 50) - 50) / 400 - fatigue_pen
                if self.rng.random() < chance:
                    self._inc_stat(side, "passes_completed")
                    self._record_carrier(carrier, "pass", True)
                    self.zone = "attacking_23"
                else:
                    self._record_carrier(carrier, "pass", False)
                    self.possession = opp
            elif r < 0.68:
                self._inc_stat(side, "aerials")
                self._add_event("aerial", side, carrier, f"{carrier.name} lanza un aerial para cambiar de carril.")
                if self.rng.random() < 0.60:
                    self.zone = "attacking_23"
                else:
                    self.possession = opp
            elif r < 0.77:
                self._add_event(
                    "three_d",
                    side,
                    carrier,
                    f"{carrier.name} usa un 3D para superar el stick.",
                )
                if self.rng.random() < 0.60:
                    self.zone = "attacking_23"
                else:
                    self.possession = opp
            elif r < 0.88:
                self._inc_stat(side, "tackles")
                self._add_event("tackle", side, carrier, f"{carrier.name} roba con un tackle limpio.")
                self.possession = side
            elif r < 0.96:
                self._foul(side)
            else:
                self._card(side)
        elif self.zone == "attacking_23":
            if r < 0.34:
                self._inc_stat(side, "circle_entries")
                self._add_event("circle_entry", side, carrier, f"{carrier.name} entra al círculo con peligro.")
                self._shift_momentum(side, 0.05, "entrada al círculo")
                self.zone = "circle"
            elif r < 0.55:
                self._penalty_corner(side)
            elif r < 0.73:
                self._shot(side, "open")
            elif r < 0.82:
                self._inc_stat(side, "aerials")
                self._add_event("aerial", side, carrier, f"{carrier.name} busca el segundo palo con un aerial.")
                self.zone = "circle" if self.rng.random() < 0.6 else "middle"
            elif r < 0.90:
                self._inc_stat(side, "passes")
                chance = 0.75 + (carrier.attributes.get("pase", 50) - 50) / 400 - fatigue_pen
                if self.rng.random() < chance:
                    self._inc_stat(side, "passes_completed")
                    self._record_carrier(carrier, "pass", True)
                    self.zone = "circle" if self.rng.random() < 0.50 else "attacking_23"
                else:
                    self._record_carrier(carrier, "pass", False)
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
                self._add_event("chance", side, carrier, f"{carrier.name} genera una ocasión, pero la defensa despeja.")
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
                recovery = 1.2 + float(p.attributes.get("resistencia", 50)) / 100.0
                p.fatigue = max(0.0, p.fatigue - recovery)
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
                        "decisions": 0,
                        "key_passes": 0,
                        "turnovers": 0,
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
            "momentum": round(self.momentum, 3),
            "momentum_log": self.momentum_log[-8:],
            "opposition": {
                "side": self.opposition_side,
                "effect": self.opposition_effect(self.opposition_side) if self.opposition_side is not None else {"attack": 0.0, "defense": 0.0, "players": 0.0},
                "instructions": self.opposition,
            },
            "match_plans": {
                "side": self.plan_side,
                "applied": sorted(self.applied_plans),
                "effect": self.plan_effect_cache,
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
                    "decisions": st.get("decisions", 0),
                    "key_passes": st.get("key_passes", 0),
                    "turnovers": st.get("turnovers", 0),
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
            inn.id,
            {
                "goals": 0,
                "assists": 0,
                "shots": 0,
                "saves": 0,
                "green": 0,
                "yellow": 0,
                "red": 0,
                "rating": 6.0,
                "decisions": 0,
                "key_passes": 0,
                "turnovers": 0,
            },
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
