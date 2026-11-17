"""Mixin de referee del motor de partido."""

from __future__ import annotations

from typing import Any

from . import rules
from .match_shared import (
    MOMENT_MINUTES,
)
from .models import PlayerState


class RefereeMixin:
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
        is_disallowed_goal = decision.get("type") == "goal_disallowed"
        decision_side = int(decision.get("side", -1))
        if is_disallowed_goal:
            if decision_side != side:
                return {
                    "ok": False,
                    "message": "Solo el equipo al que se le anuló el gol puede revisarlo.",
                }
        elif decision_side == side:
            return {"ok": False, "message": "Solo puedes revisar una decisión contra tu equipo."}
        if self.referrals.get(side, 0) <= 0:
            return {"ok": False, "message": "No te quedan referencias de vídeo."}
        strictness = float(self.referee.get("strictness", 55))
        base = {
            "goal": 0.46,
            "goal_disallowed": 0.40,
            "penalty_corner": 0.34,
            "penalty_stroke": 0.30,
        }.get(str(decision.get("type")), 0.30)
        chance = max(0.15, min(0.65, base + (55 - strictness) / 400))
        overturned = self.rng.random() < chance
        score_before = f"{self.score[0]}-{self.score[1]}"
        if overturned:
            if is_disallowed_goal:
                self._award_goal_from_decision(decision)
                text = (
                    f"Revisión de vídeo: el árbitro corrige la decisión y concede el gol a "
                    f"{decision.get('team_name')}. {decision.get('scorer_name') or ''} marca."
                )
            elif decision.get("goal"):
                self._annul_goal(decision)
                text = (
                    f"Revisión de vídeo: gol anulado a {decision.get('scorer_name') or decision.get('team_name')}. "
                    f"El árbitro de vídeo corrige la decisión."
                )
            else:
                if decision.get("type") == "penalty_corner":
                    stats = self.stats[int(decision["side"])]
                    stats["pc"] = max(0, int(stats.get("pc", 0)) - 1)
                elif decision.get("type") == "penalty_stroke":
                    stats = self.stats[int(decision["side"])]
                    stats["strokes"] = max(0, int(stats.get("strokes", 0)) - 1)
                text = (
                    f"Revisión de vídeo: el árbitro corrige la decisión y anula "
                    f"{decision.get('label', 'la jugada')} a favor de {decision.get('team_name')}."
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

    def _penalty_corner(self, side: int, retake: bool | None = None, retake_count: int = 0):
        self._clear_advantage(side)
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
        if retake is None:
            strictness = int(self.referee.get("strictness", 55))
            retake = retake_count == 0 and (strictness + int(self.minute) * 3 + side * 11) % 97 < 5
        if retake and retake_count == 0:
            self._inc_stat(side, "pc_retake")
            self._add_event(
                "pc_retake",
                side,
                inj,
                "El árbitro ordena repetir el penalty corner por invasión del área.",
            )
            return self._penalty_corner(side, retake=False, retake_count=1)
        self._inc_stat(side, "pc")
        self._shift_momentum(side, 0.05, "penalty corner")
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
            self._shift_momentum(side, 0.14, "gol de penalty corner")
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
                self._shift_momentum(opp, 0.04, "parada de penalty corner")
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

    def _stroke(self, side: int, retake: bool | None = None, retake_count: int = 0):
        self._clear_advantage(side)
        t = self._team(side)
        spec = t.specialists(self._lineup(side))
        opp = 1 - side
        opp_spec = self._team(opp).specialists(self._lineup(opp))
        gk = opp_spec.get("stroke_goalkeeper") or self._gk(opp)
        taker = spec.get("stroke_taker")
        if retake is None:
            strictness = int(self.referee.get("strictness", 55))
            retake = retake_count == 0 and (strictness + int(self.minute) * 5 + side * 7) % 101 < 4
        if retake and retake_count == 0:
            self._inc_stat(side, "stroke_retake")
            self._add_event(
                "stroke_retake",
                side,
                taker,
                "El árbitro ordena repetir el penalty stroke por invasión del portero.",
            )
            return self._stroke(side, retake=False, retake_count=1)
        self._inc_stat(side, "strokes")
        self._record_decision("penalty_stroke", side, taker)
        self._add_event("stroke", side, taker, f"Penalty stroke para {t.name}. {taker.name} toma la bola.")
        shot = taker.attributes.get("stroke_shot", 50) + self.rng.gauss(0, 6)
        save = gk.attributes.get("stroke_save", 50) + self.rng.gauss(0, 6)
        chance = 0.78 + (shot - save) / 260
        chance = max(0.55, min(0.92, chance))
        if self.rng.random() < chance:
            self.score[side] += 1
            self._shift_momentum(side, 0.16, "gol de stroke")
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

    def _disallowed_goal(
        self,
        side: int,
        scorer: PlayerState,
        assister: PlayerState | None,
        kind: str,
        offence: str,
    ) -> None:
        t = self._team(side)
        opp = 1 - side
        self._inc_stat(side, "goals_disallowed")
        if offence in rules.ATTACKING_GOAL_OFFENCES:
            self._inc_stat(side, f"{offence}_goals_disallowed")
        self._record_decision(
            "goal_disallowed",
            side,
            scorer,
            goal=False,
            disallowed_goal=True,
            disallowed_reason=offence,
            scorer_id=scorer.id,
            scorer_name=scorer.name,
            assister_id=assister.id if assister else None,
            goal_kind=kind,
        )
        reason = rules.ATTACKING_GOAL_OFFENCES.get(offence, offence)
        if offence == "outside_circle":
            text = (
                f"Gol anulado a {t.name}: el disparo de {scorer.name} entró directamente "
                f"desde fuera del círculo. Se concede golpe franco a {self._team(opp).name}."
            )
        else:
            text = (
                f"Gol anulado a {t.name}: {scorer.name} jugó la bola con {reason}. "
                f"Se concede golpe franco a {self._team(opp).name}."
            )
        self._add_event("goal_disallowed", side, scorer, text)
        self.possession = opp
        self.zone = "middle"

    def _award_goal_from_decision(self, decision: dict[str, Any]) -> None:
        side = int(decision["side"])
        scorer_id = decision.get("scorer_id")
        scorer = next(
            (player for player in self._team(side).players if player.id == scorer_id), None
        )
        assister_id = decision.get("assister_id")
        assister = None
        if assister_id:
            assister = next(
                (player for player in self._team(side).players if player.id == assister_id),
                None,
            )
        kind = str(decision.get("goal_kind") or "open")
        self.score[side] += 1
        self._inc_stat(side, "goals")
        if kind == "pc":
            self._inc_stat(side, "pc_goals")
        if kind == "stroke":
            self._inc_stat(side, "stroke_goals")
        if scorer is not None:
            self.player_stats[scorer.id]["goals"] += 1
        if assister is not None and scorer is not None and assister.id != scorer.id:
            self.player_stats[assister.id]["assists"] += 1
        name = scorer.name if scorer is not None else decision.get("scorer_name") or self._team(side).name
        self._add_event(
            "goal",
            side,
            scorer,
            f"Revisión de vídeo: gol concedido a {self._team(side).name}. {name} marca tras corregir el árbitro.",
        )

    def _clear_advantage(self, side: int) -> None:
        if self.pending_advantage is not None and self.pending_advantage.get("side") == side:
            self.pending_advantage = None

    def _resolve_advantage(self) -> None:
        pending = self.pending_advantage
        if pending is None:
            return
        side = int(pending["side"])
        if self.possession != side:
            self._inc_stat(side, "advantage_failed")
            self._add_event(
                "advantage_failed",
                side,
                None,
                f"La ventaja no se materializa: el árbitro vuelve a la falta original a favor de {self._team(side).name}.",
            )
            self.pending_advantage = None
            if pending.get("in_circle"):
                self._penalty_corner(side)
            else:
                self.possession = side
                self.zone = str(pending.get("zone", "middle"))
                self._add_event(
                    "free_hit",
                    side,
                    None,
                    f"Se reanuda con golpe franco para {self._team(side).name}.",
                )
            return
        pending["moments_left"] = int(pending.get("moments_left", 2)) - 1
        if pending["moments_left"] <= 0:
            self.pending_advantage = None

    def _foul(
        self,
        side: int,
        foul_type: str | None = None,
        advantage: bool | None = None,
        pc_decision: str | None = None,
        distance_call: bool | None = None,
        dangerous_severity: str | None = None,
        dangerous_card: bool | None = None,
        advance_10m: bool | None = None,
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
            severity = dangerous_severity
            if severity not in rules.DANGEROUS_PLAY_LEVELS:
                roll = self.rng.random()
                if foul_type == "stick":
                    severity = "dangerous" if roll < 0.25 else ("reckless" if roll < 0.80 else "careless")
                else:
                    severity = "dangerous" if roll < 0.20 else ("reckless" if roll < 0.75 else "careless")
            level = rules.DANGEROUS_PLAY_LEVELS[severity]
            self._inc_stat(side, "dangerous_play")
            self._add_event(
                "dangerous_play",
                side,
                offender,
                f"Juego peligroso de {offender.name}: {level['label']}.",
            )
            if dangerous_card is None:
                dangerous_card = self.rng.random() < float(level["card_chance"])
            if dangerous_card:
                self._card(side)
                self._inc_stat(side, "dangerous_sanction")
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
            self.pending_advantage = {
                "side": opp,
                "offender_side": side,
                "zone": self.zone,
                "in_circle": in_circle,
                "minute": int(self.minute),
                "moments_left": 2,
            }
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
        if advance_10m is None:
            advance_10m = bool(distance_call) and (
                float(self.referee.get("strictness", 55)) >= 60 or int(self.minute) % 9 == 0
            )
        if advance_10m:
            self._inc_stat(opp, "free_hit_10m")
            self._add_event(
                "free_hit_10m",
                opp,
                None,
                f"El árbitro adelanta el golpe franco {rules.FREE_HIT_ADVANCE_METERS} metros por protestas de la defensa.",
            )
            self.zone = "attacking_23" if self.rng.random() < 0.35 else "middle"
        self._free_hit(opp)

    def _free_hit(self, side: int):
        """Cadena de golpe franco: corto, largo o tiro directo.

        Usa un RNG derivado para no alterar la secuencia principal del partido.
        """
        t = self._team(side)
        lineup = [p for p in self._lineup(side) if p.subposition != "Portero"] or self._lineup(side)
        rng = self._decision_rng("free_hit")
        taker = max(
            lineup,
            key=lambda p: p.attributes.get("pase", 50) * 0.45
            + p.attributes.get("pc_injection", 50) * 0.30
            + p.attributes.get("control", 50) * 0.25,
        )
        self._inc_stat(side, "free_hits")
        self.possession = side
        option = rng.choices(["short", "long", "direct"], weights=[0.45, 0.40, 0.15], k=1)[0]
        fatigue_pen = max(0.0, taker.fatigue - 55.0) / 100.0 * 0.12
        if option == "short":
            chance = 0.74 + (taker.attributes.get("pase", 50) - 50) / 300 - fatigue_pen
            if rng.random() < chance:
                self._record_carrier(taker, "pass", True)
                self._add_event(
                    "free_hit",
                    side,
                    taker,
                    f"{taker.name} juega corto el golpe franco y {t.name} conserva la posesión.",
                )
                self.zone = "attacking_23" if rng.random() < 0.55 else "middle"
            else:
                self._record_carrier(taker, "pass", False)
                self._add_event("free_hit", side, taker, f"El pase corto de {taker.name} es interceptado.")
                self.possession = 1 - side
                self.zone = "middle"
            return
        if option == "long":
            target = max(
                lineup,
                key=lambda p: p.attributes.get("aerial", 50) + p.attributes.get("definicion", 50) * 0.35,
            )
            chance = 0.52 + (taker.attributes.get("pc_injection", 50) - 50) / 300 - fatigue_pen
            if rng.random() < chance:
                self._add_event(
                    "free_hit",
                    side,
                    taker,
                    f"{taker.name} lanza el golpe franco al área y {target.name} gana la posición.",
                )
                self.zone = "circle"
            else:
                self._add_event("free_hit", side, taker, f"El envío largo de {taker.name} no encuentra receptor.")
                self.possession = 1 - side
                self.zone = "middle"
            return
        self._add_event("free_hit", side, taker, f"{taker.name} opta por el tiro directo desde el golpe franco.")
        self.zone = "attacking_23"
        self._shot(side, "open")

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
        self._shift_momentum(side, -0.10, f"tarjeta {card_type}")
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
