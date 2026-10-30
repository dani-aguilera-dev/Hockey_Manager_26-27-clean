"""Modelos de datos del Hockey Manager (Fase 1)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

SLOT_TO_SUB = {
    "POR": "Portero",
    "CEN": "Central",
    "LAT": "Lateral",
    "MED": "Medio",
    "DEL": "Delantero",
}

FORMATION_SLOTS = {
    "4-3-3": ["POR", "LAT", "CEN", "CEN", "LAT", "MED", "MED", "MED", "DEL", "DEL", "DEL"],
    "3-4-3": ["POR", "CEN", "CEN", "CEN", "LAT", "MED", "MED", "LAT", "DEL", "DEL", "DEL"],
    "3-3-3-1": ["POR", "CEN", "CEN", "CEN", "LAT", "MED", "MED", "LAT", "MED", "DEL", "DEL"],
    "4-4-2": ["POR", "LAT", "CEN", "CEN", "LAT", "MED", "MED", "MED", "MED", "DEL", "DEL"],
    "5-3-2": ["POR", "LAT", "CEN", "CEN", "CEN", "LAT", "MED", "MED", "MED", "DEL", "DEL"],
    "3-2-1-4": ["POR", "CEN", "CEN", "CEN", "MED", "MED", "MED", "DEL", "DEL", "DEL", "DEL"],
}

TACTIC_MODS = {
    "mentality": {
        "muy_defensiva": (-0.15, 0.15),
        "defensiva": (-0.08, 0.08),
        "equilibrada": (0.0, 0.0),
        "ofensiva": (0.08, -0.08),
        "muy_ofensiva": (0.15, -0.15),
    },
    "press": {
        "baja": (-0.05, -0.10, -0.05),
        "media": (0.0, 0.0, 0.0),
        "alta": (0.05, 0.08, 0.08),
        "muy_alta": (0.10, 0.12, 0.15),
    },
    "tempo": {
        "lento": (-0.05, 0.03, -0.03),
        "normal": (0.0, 0.0, 0.0),
        "rapido": (0.08, -0.03, 0.05),
    },
    "block": {
        "bajo": (-0.03, 0.05),
        "medio": (0.0, 0.0),
        "alto": (0.04, -0.03),
    },
    "width": {
        "estrecha": (-0.01, 0.02),
        "normal": (0.0, 0.0),
        "ancha": (0.02, -0.01),
    },
    "passing": {
        "corto": (-0.02, 0.02),
        "mixto": (0.0, 0.0),
        "directo": (0.03, -0.02),
    },
    "defensive_system": {
        "zona_baja": (-0.04, 0.10, -0.02),
        "zona_media": (0.0, 0.04, 0.0),
        "zona_alta": (0.04, 0.06, 0.05),
        "individual_todo_campo": (0.02, 0.03, 0.10),
        "individual_mixta": (0.01, 0.07, 0.05),
    },
    "attack_system": {
        "posicional": (0.02, -0.01, 0.0),
        "contraataque": (0.06, -0.03, 0.02),
        "directo": (0.04, -0.02, 0.01),
        "bandas": (0.03, 0.0, 0.0),
        "interior": (0.02, 0.0, 0.0),
        "sobrecarga_derecha": (0.03, -0.01, 0.0),
        "sobrecarga_izquierda": (0.03, -0.01, 0.0),
    },
    "outlet": {
        "portero": (0.01, 0.01, 0.0),
        "central": (0.02, 0.0, 0.0),
        "lateral": (0.01, 0.01, 0.0),
        "directo": (0.03, -0.02, 0.01),
    },
    "press_trigger": {
        "perdida": (0.03, 0.02, 0.02),
        "saque_fondo": (0.02, 0.03, 0.03),
        "banda": (0.01, 0.02, 0.02),
        "pase_atras": (0.01, 0.03, 0.02),
        "siempre": (0.04, 0.04, 0.06),
    },
}


@dataclass
class Tactics:
    formation: str = "4-3-3"
    mentality: str = "equilibrada"
    press: str = "media"
    block: str = "medio"
    width: str = "normal"
    tempo: str = "normal"
    passing: str = "mixto"
    pc_routine: str = "directa"
    defensive_system: str = "zona_media"
    attack_system: str = "posicional"
    outlet: str = "central"
    press_trigger: str = "perdida"
    pc_injector_id: str = ""
    pc_stopper_id: str = ""
    pc_flicker_id: str = ""
    pc_deflector_id: str = ""
    pc_rebounder_id: str = ""
    pc_first_runner_id: str = ""
    pc_goalkeeper_id: str = ""
    stroke_taker_id: str = ""
    stroke_goalkeeper_id: str = ""
    free_hit_taker_id: str = ""

    @staticmethod
    def _mod(group: str, key: str, index: int) -> float:
        entry = TACTIC_MODS[group].get(key, (0.0, 0.0, 0.0))
        return entry[index] if index < len(entry) else 0.0

    def attack_mod(self) -> float:
        return (
            self._mod("mentality", self.mentality, 0)
            + self._mod("press", self.press, 0)
            + self._mod("tempo", self.tempo, 0)
            + self._mod("block", self.block, 0)
            + self._mod("width", self.width, 0)
            + self._mod("passing", self.passing, 0)
            + self._mod("defensive_system", self.defensive_system, 0)
            + self._mod("attack_system", self.attack_system, 0)
            + self._mod("outlet", self.outlet, 0)
            + self._mod("press_trigger", self.press_trigger, 0)
        )

    def defense_mod(self) -> float:
        return (
            self._mod("mentality", self.mentality, 1)
            + self._mod("press", self.press, 1)
            + self._mod("tempo", self.tempo, 1)
            + self._mod("block", self.block, 1)
            + self._mod("width", self.width, 1)
            + self._mod("passing", self.passing, 1)
            + self._mod("defensive_system", self.defensive_system, 1)
            + self._mod("attack_system", self.attack_system, 1)
            + self._mod("outlet", self.outlet, 1)
            + self._mod("press_trigger", self.press_trigger, 1)
        )

    def fatigue_mod(self) -> float:
        return (
            self._mod("press", self.press, 2)
            + self._mod("tempo", self.tempo, 2)
            + self._mod("defensive_system", self.defensive_system, 2)
            + self._mod("attack_system", self.attack_system, 2)
            + self._mod("outlet", self.outlet, 2)
            + self._mod("press_trigger", self.press_trigger, 2)
        )

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Tactics":
        return cls(**{k: d.get(k, getattr(cls(), k)) for k in cls().__dict__})


@dataclass
class PlayerState:
    id: str
    name: str
    team_name: str
    position_group: str
    subposition: str
    age: int
    overall: float
    potential: float
    attributes: dict[str, int]
    archetype: str
    perfil: str
    goals_isquad: int
    origin_team: str = ""
    value: int = 0
    polivalencia: float = 0.0
    overalls: dict[str, float] = field(default_factory=dict)
    fatigue: float = 0.0  # 0-100
    morale: int = 12  # 1-20
    relationship: int = 50  # 0-100 con el entrenador
    absence_note: str = ""  # motivo específico de la baja (legal, enfermedad, etc.)
    form: float = 6.5  # 1-10
    injury: int = 0  # partidos de baja
    injury_type: str = ""
    injury_severity: str = ""
    injury_started: str = ""
    injury_expected: int = 0
    injury_history: list[dict[str, Any]] = field(default_factory=list)
    suspension: int = 0  # partidos de sanción
    suspension_reason: str = ""
    suspension_started: str = ""
    card_history: list[dict[str, Any]] = field(default_factory=list)
    traits: list[str] = field(default_factory=list)
    promises: list[dict[str, Any]] = field(default_factory=list)
    season_goals: int = 0
    season_assists: int = 0
    apps: int = 0
    rating_sum: float = 0.0
    salary: int = 0
    contract_until: str = "2028-06-30"
    league: str = ""
    photo: str = ""
    photo_remote: str = ""
    career: list[dict[str, Any]] = field(default_factory=list)
    transfer_listed: bool = False
    transfer_asking_price: int = 0
    brand_deal: dict[str, Any] = field(default_factory=dict)
    loan: dict[str, Any] = field(default_factory=dict)
    development_plan: dict[str, Any] = field(default_factory=dict)
    release_clause: int = 0
    renewal_bonus: int = 0

    @property
    def youth_category(self) -> str:
        if self.age <= 15:
            return "Sub-16"
        if self.age <= 17:
            return "Sub-18"
        if self.age <= 20:
            return "Sub-21"
        return "Senior"

    @property
    def available(self) -> bool:
        return self.injury <= 0 and self.suspension <= 0

    @property
    def rating(self) -> float:
        return round(self.rating_sum / self.apps, 2) if self.apps else 0.0

    @property
    def relationship_label(self) -> str:
        if self.relationship >= 80:
            return "Muy cercana"
        if self.relationship >= 60:
            return "Buena"
        if self.relationship >= 40:
            return "Normal"
        if self.relationship >= 20:
            return "Fría"
        return "Mala"

    @property
    def absence_label(self) -> str:
        if self.injury > 0:
            return self.absence_note or "Lesión"
        if self.suspension > 0:
            return self.absence_note or "Sanción"
        return ""

    def slot_fit(self, slot: str) -> float:
        target = SLOT_TO_SUB.get(slot)
        if not target:
            return 0.0
        if self.subposition == target:
            return 6.0
        if self.position_group == target:
            return 3.0
        if target in ("Central", "Lateral") and self.position_group == "Defensa":
            return 3.0
        if self.subposition == "Polivalente":
            return 2.0
        # Portero solo puede jugar de portero; los demás tienen penalización.
        if self.subposition == "Portero" or target == "Portero":
            return -40.0
        return -3.0

    def selection_score(self, slot: str) -> float:
        fatigue_pen = self.fatigue * 0.20
        form_bonus = (self.form - 5) * 1.2
        morale_bonus = (self.morale - 10) * 0.3
        relationship_bonus = (self.relationship - 50) * 0.02
        return self.overall + self.slot_fit(slot) + form_bonus + morale_bonus + relationship_bonus - fatigue_pen

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "PlayerState":
        return cls(**d)


@dataclass
class StaffMember:
    role: str
    name: str
    rating: int = 60
    salary: int = 0
    contract_until: str = ""
    source: str = "modelo"
    confidence: str = "baja"
    relationship: int = 50
    morale: int = 12

    @property
    def relationship_label(self) -> str:
        if self.relationship >= 80:
            return "Muy cercana"
        if self.relationship >= 60:
            return "Buena"
        if self.relationship >= 40:
            return "Normal"
        if self.relationship >= 20:
            return "Fría"
        return "Mala"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "StaffMember":
        return cls(
            role=d["role"],
            name=d["name"],
            rating=int(d.get("rating", 60)),
            salary=int(d.get("salary", 0)),
            contract_until=d.get("contract_until", ""),
            source=d.get("source", "modelo"),
            confidence=d.get("confidence", "baja"),
            relationship=int(d.get("relationship", 50)),
            morale=int(d.get("morale", 12)),
        )


@dataclass
class BoardMember:
    role: str
    name: str
    source: str = "modelo"
    confidence: str = "baja"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "BoardMember":
        return cls(
            role=d["role"],
            name=d["name"],
            source=d.get("source", "modelo"),
            confidence=d.get("confidence", "baja"),
        )


DEFAULT_FACILITIES: dict[str, int] = {
    "training": 60,
    "youth": 60,
    "medical": 60,
    "video": 55,
    "scouting": 55,
    "stadium": 55,
}


@dataclass
class TeamState:
    id: str
    name: str
    league: str
    city: str
    players: list[PlayerState]
    community: str = ""
    country: str = "España"
    tactics: Tactics = field(default_factory=Tactics)
    stadium_name: str = ""
    stadium_capacity: int = 1000
    board_expectation: str = ""
    board_patience: int = 3
    board_pressure: str = "media"
    academy_rating: int = 60
    preferred_mode: str = ""
    budget: int = 0
    wage_budget: int = 0
    board_confidence: int = 60
    fan_confidence: int = 60
    morale: int = 12
    cohesion: int = 12
    manager_rating: int = 60
    assistant_rating: int = 60
    prep_bonus: float = 0.0
    media_confidence: int = 50
    equipment_bonus: float = 0.0
    equipment_deals: list[dict[str, Any]] = field(default_factory=list)
    facilities: dict[str, int] = field(default_factory=lambda: dict(DEFAULT_FACILITIES))
    board_requests: list[dict[str, Any]] = field(default_factory=list)
    mentoring: list[dict[str, Any]] = field(default_factory=list)
    mentoring_history: list[dict[str, Any]] = field(default_factory=list)
    team_meetings: list[dict[str, Any]] = field(default_factory=list)
    staff_assignments: dict[str, str] = field(default_factory=dict)
    staff: list[StaffMember] = field(default_factory=list)
    board: list[BoardMember] = field(default_factory=list)
    transfer_budget: int = 0
    club_tier: int = 3
    brand_rating: int = 50
    ticket_price: int = 15
    merchandising: int = 50
    sponsor_deals: list[dict[str, Any]] = field(default_factory=list)
    commercial_history: list[dict[str, Any]] = field(default_factory=list)
    finance_log: list[dict] = field(default_factory=list)
    youth: list[PlayerState] = field(default_factory=list)
    last_lineup: list[str] = field(default_factory=list)
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0
    points: int = 0

    @property
    def squad(self) -> list[PlayerState]:
        return [p for p in self.players if p.perfil == "Jugador"]

    @property
    def available_players(self) -> list[PlayerState]:
        return [p for p in self.players if p.available]

    def auto_lineup(self) -> tuple[list[PlayerState], list[PlayerState]]:
        slots = FORMATION_SLOTS.get(self.tactics.formation, FORMATION_SLOTS["4-3-3"])
        # Si las bajas dejan menos de 11 disponibles, el equipo juega con
        # menos efectivos; nunca se alinea a un lesionado o sancionado.
        all_available = self.available_players
        # Rotación: si hay 11 jugadores por debajo del 80% de fatiga, priorizarlos.
        rotation = [p for p in all_available if p.fatigue < 80]
        if len(rotation) < 11:
            rest = sorted(
                [p for p in all_available if p.id not in {x.id for x in rotation}],
                key=lambda p: (p.fatigue, -p.overall),
            )
            rotation = rotation + rest[: 11 - len(rotation)]
        if len(rotation) < 11:
            # Emergencia: no se debe alinear a un lesionado o sancionado. Si
            # no hay 11 disponibles, el equipo juega con menos y el motor lo
            # penaliza; la interfaz debe avisar y permitir llamar a cantera.
            rotation = rotation + sorted(
                [p for p in self.players if p.available and p.id not in {x.id for x in rotation}],
                key=lambda p: (p.fatigue, -p.overall),
            )[: 11 - len(rotation)]
        pool = [p for p in rotation if p.subposition != "Portero" or "POR" in slots]
        chosen: list[PlayerState | None] = [None] * len(slots)
        used: set[str] = set()
        # Primero porteros, luego el resto por slot. Se guarda cada jugador
        # en su índice de formación para que el once salga en orden de pista.
        priority = sorted(enumerate(slots), key=lambda item: (item[1] != "POR", item[1], item[0]))
        for index, slot in priority:
            # Prioridad: jugador natural del puesto > mismo grupo > cualquier otro.
            natural = [p for p in pool if p.id not in used and p.slot_fit(slot) >= 6]
            group = [p for p in pool if p.id not in used and p.slot_fit(slot) >= 3]
            candidates = natural or group or [p for p in pool if p.id not in used and p.slot_fit(slot) > -20]
            if not candidates:
                candidates = [p for p in rotation if p.id not in used]
            if not candidates:
                break
            best = max(candidates, key=lambda p: p.selection_score(slot))
            chosen[index] = best
            used.add(best.id)
        # Completar huecos hasta 11 si faltan.
        for p in sorted(rotation, key=lambda x: x.overall, reverse=True):
            if all(x is not None for x in chosen):
                break
            if p.id not in used:
                for index in range(len(chosen)):
                    if chosen[index] is None:
                        chosen[index] = p
                        used.add(p.id)
                        break
        lineup = [p for p in chosen if p is not None][:11]
        bench = [p for p in sorted(all_available, key=lambda x: (x.fatigue, -x.overall)) if p.id not in used][:7]
        return lineup, bench

    def lineup_strength(self, lineup: list[PlayerState]) -> tuple[float, float]:
        if not lineup:
            return 50.0, 50.0

        def mean_attr(keys, players):
            vals = []
            for p in players:
                vals.append(sum(p.attributes.get(k, 50) for k in keys) / len(keys))
            return sum(vals) / len(vals) if vals else 50.0

        attack = mean_attr(["definicion", "pc_flick", "regate_3d", "pase", "velocidad"], lineup)
        defense = mean_attr(["cobertura", "posicionamiento", "pc_first_runner", "pressing", "fuerza"], lineup)
        # Portero
        gk = next((p for p in lineup if p.subposition == "Portero"), None)
        if gk:
            defense = 0.75 * defense + 0.25 * (gk.attributes.get("reflejos", 50) + gk.attributes.get("blocaje", 50)) / 2
        fatigue = sum(p.fatigue for p in lineup) / len(lineup)
        attack -= fatigue * 0.08
        defense -= fatigue * 0.08
        attack += self.tactics.attack_mod() * 100
        defense += self.tactics.defense_mod() * 100
        return max(25.0, attack), max(25.0, defense)

    def staff_rating(self, role: str, default: int = 55) -> int:
        for m in self.staff:
            if m.role == role:
                return int(m.rating)
        return default

    def staff_wage_bill(self) -> int:
        return sum(max(0, int(m.salary)) for m in self.staff)

    def player_wage_bill(self) -> int:
        return sum(max(0, int(p.salary)) for p in self.players)

    def management_profile(self, lineup: list[PlayerState] | None = None) -> dict:
        """Puntuación interna de gestión (0-100) y sus componentes.

        Premia moral, cohesión, descanso, confianza, encaje posicional y
        trayectoria del entrenador. Se aplica como pequeño modificador de
        ataque/defensa en el motor, para que una buena gestión pueda competir
        contra plantillas superiores.
        """
        if lineup is None:
            lineup = self.auto_lineup()[0]
        if not lineup:
            lineup = self.players[:11]
        slots = FORMATION_SLOTS.get(self.tactics.formation, FORMATION_SLOTS["4-3-3"])
        avg_fatigue = sum(p.fatigue for p in lineup) / max(1, len(lineup))
        fits = [p.slot_fit(slots[i] if i < len(slots) else "MED") for i, p in enumerate(lineup)]
        avg_fit = sum(fits) / len(fits) if fits else 0.0
        comps = {
            "moral": (self.morale - 10) * 2.0,
            "cohesion": (self.cohesion - 10) * 1.5,
            "fatiga": -avg_fatigue * 0.30,
            "confianza": (((self.board_confidence + self.fan_confidence) / 2) - 50) * 0.15,
            "encaje": (avg_fit - 2.0) * 1.5,
            "entrenador": (self.manager_rating - 50) * 0.10,
        }
        score = max(0.0, min(100.0, 50.0 + sum(comps.values())))
        bonus = max(-7.0, min(7.0, (score - 50.0) / 8.0))
        comps["score"] = round(score, 1)
        comps["bonus"] = round(bonus, 2)
        comps["avg_fatigue"] = round(avg_fatigue, 1)
        comps["avg_fit"] = round(avg_fit, 2)
        return comps

    def management_score(self, lineup: list[PlayerState] | None = None) -> float:
        return self.management_profile(lineup)["score"]

    def management_bonus(self, lineup: list[PlayerState] | None = None) -> float:
        return self.management_profile(lineup)["bonus"]

    def specialists(self, lineup: list[PlayerState] | None = None) -> dict[str, PlayerState]:
        pool = lineup or self.auto_lineup()[0]
        if not pool:
            pool = self.players

        def best(attr: str) -> PlayerState:
            return max(pool, key=lambda p: p.attributes.get(attr, 0)) if pool else None

        def manual(field: str, attr: str) -> PlayerState:
            player_id = str(getattr(self.tactics, field, "") or "")
            if player_id:
                chosen = next((p for p in pool if p.id == player_id), None)
                if chosen is not None:
                    return chosen
            return best(attr)

        goalkeeper = max(
            [p for p in pool if p.subposition == "Portero"] or pool,
            key=lambda p: p.attributes.get("pc_gk_save", 0),
        )
        stroke_goalkeeper = max(
            [p for p in pool if p.subposition == "Portero"] or pool,
            key=lambda p: p.attributes.get("stroke_save", 0),
        )
        return {
            "pc_injector": manual("pc_injector_id", "pc_injection"),
            "pc_stopper": manual("pc_stopper_id", "pc_trap"),
            "pc_flicker": manual("pc_flicker_id", "pc_flick"),
            "pc_deflector": manual("pc_deflector_id", "pc_deflection"),
            "pc_rebounder": manual("pc_rebounder_id", "pc_deflection"),
            "pc_first_runner": manual("pc_first_runner_id", "pc_first_runner"),
            "pc_goalkeeper": manual("pc_goalkeeper_id", "pc_gk_save") or goalkeeper,
            "stroke_taker": manual("stroke_taker_id", "stroke_shot"),
            "stroke_goalkeeper": manual("stroke_goalkeeper_id", "stroke_save") or stroke_goalkeeper,
            "free_hit_taker": manual("free_hit_taker_id", "free_hit"),
        }

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "league": self.league,
            "city": self.city,
            "community": self.community,
            "country": self.country,
            "players": [p.to_dict() for p in self.players],
            "tactics": self.tactics.to_dict(),
            "stadium_name": self.stadium_name,
            "stadium_capacity": self.stadium_capacity,
            "board_expectation": self.board_expectation,
            "board_patience": self.board_patience,
            "board_pressure": self.board_pressure,
            "academy_rating": self.academy_rating,
            "preferred_mode": self.preferred_mode,
            "budget": self.budget,
            "wage_budget": self.wage_budget,
            "board_confidence": self.board_confidence,
            "fan_confidence": self.fan_confidence,
            "morale": self.morale,
            "cohesion": self.cohesion,
            "manager_rating": self.manager_rating,
            "assistant_rating": self.assistant_rating,
            "prep_bonus": self.prep_bonus,
            "media_confidence": self.media_confidence,
            "equipment_bonus": self.equipment_bonus,
            "equipment_deals": self.equipment_deals,
            "facilities": self.facilities,
            "board_requests": self.board_requests,
            "mentoring": self.mentoring,
            "mentoring_history": self.mentoring_history,
            "team_meetings": self.team_meetings,
            "staff_assignments": self.staff_assignments,
            "staff": [m.to_dict() for m in self.staff],
            "board": [m.to_dict() for m in self.board],
            "transfer_budget": self.transfer_budget,
            "club_tier": self.club_tier,
            "brand_rating": self.brand_rating,
            "ticket_price": self.ticket_price,
            "merchandising": self.merchandising,
            "sponsor_deals": self.sponsor_deals,
            "commercial_history": self.commercial_history,
            "finance_log": self.finance_log,
            "youth": [p.to_dict() for p in self.youth],
            "last_lineup": self.last_lineup,
            "played": self.played,
            "won": self.won,
            "drawn": self.drawn,
            "lost": self.lost,
            "goals_for": self.goals_for,
            "goals_against": self.goals_against,
            "points": self.points,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TeamState":
        return cls(
            id=d["id"],
            name=d["name"],
            league=d["league"],
            city=d["city"],
            community=d.get("community", ""),
            country=d.get("country", "España"),
            players=[PlayerState.from_dict(p) for p in d["players"]],
            tactics=Tactics.from_dict(d.get("tactics", {})),
            stadium_name=d.get("stadium_name", ""),
            stadium_capacity=d.get("stadium_capacity", 1000),
            board_expectation=d.get("board_expectation", ""),
            board_patience=d.get("board_patience", 3),
            board_pressure=d.get("board_pressure", "media"),
            academy_rating=d.get("academy_rating", 60),
            preferred_mode=d.get("preferred_mode", ""),
            budget=d.get("budget", 0),
            wage_budget=d.get("wage_budget", 0),
            board_confidence=d.get("board_confidence", 60),
            fan_confidence=d.get("fan_confidence", 60),
            morale=d.get("morale", 12),
            cohesion=d.get("cohesion", 12),
            manager_rating=d.get("manager_rating", 60),
            assistant_rating=d.get("assistant_rating", 60),
            prep_bonus=d.get("prep_bonus", 0.0),
            media_confidence=d.get("media_confidence", 50),
            equipment_bonus=d.get("equipment_bonus", 0.0),
            equipment_deals=d.get("equipment_deals", []),
            facilities={**DEFAULT_FACILITIES, **(d.get("facilities") or {})},
            board_requests=d.get("board_requests") or [],
            mentoring=d.get("mentoring") or [],
            mentoring_history=d.get("mentoring_history") or [],
            team_meetings=d.get("team_meetings") or [],
            staff_assignments=d.get("staff_assignments") or {},
            staff=[StaffMember.from_dict(m) for m in d.get("staff", [])],
            board=[BoardMember.from_dict(m) for m in d.get("board", [])],
            transfer_budget=d.get("transfer_budget", 0),
            club_tier=d.get("club_tier", 3),
            brand_rating=d.get("brand_rating", 50),
            ticket_price=d.get("ticket_price", 15),
            merchandising=d.get("merchandising", 50),
            sponsor_deals=d.get("sponsor_deals", []),
            commercial_history=d.get("commercial_history", []),
            finance_log=d.get("finance_log", []),
            youth=[PlayerState.from_dict(p) for p in d.get("youth", [])],
            last_lineup=d.get("last_lineup", []),
            played=d.get("played", 0),
            won=d.get("won", 0),
            drawn=d.get("drawn", 0),
            lost=d.get("lost", 0),
            goals_for=d.get("goals_for", 0),
            goals_against=d.get("goals_against", 0),
            points=d.get("points", 0),
        )


@dataclass
class Fixture:
    id: str
    round: int
    date: str
    home_id: str
    away_id: str
    phase: str = "regular"
    played: bool = False
    home_goals: int = 0
    away_goals: int = 0
    home_stats: dict[str, Any] = field(default_factory=dict)
    away_stats: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    attendance: int = 0
    travel: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Fixture":
        return cls(**d)


@dataclass
class GameState:
    manager_name: str
    club_id: str
    season: str
    seed: int
    round: int
    date: str
    fixtures: list[Fixture]
    teams: dict[str, TeamState]
    competition: str = "DHA"
    country: str = "España"
    phase: str = "regular"
    # Calendario de todas las ligas del mundo. `fixtures` sigue siendo el
    # calendario de la competición del usuario para mantener la API/UI actual.
    league_fixtures: dict[str, list[Fixture]] = field(default_factory=dict)
    promotion: dict[str, Any] = field(default_factory=dict)
    promotion_round: int = 0
    final4: dict[str, Any] = field(default_factory=dict)
    playout: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    inbox: list[dict[str, Any]] = field(default_factory=list)
    last_result: dict[str, Any] = field(default_factory=dict)
    manual_lineup: list[str] = field(default_factory=list)
    week_trained: bool = False
    weekly_plan: list[str] = field(default_factory=list)
    training_report: dict[str, Any] = field(default_factory=dict)
    ai_training_round: int = 0
    finance_round: int = 0
    transfer_offers: list[dict[str, Any]] = field(default_factory=list)
    market_history: list[dict[str, Any]] = field(default_factory=list)
    market_offers_round: int = 0
    market_offers_date: str = ""
    sponsor_offers: list[dict[str, Any]] = field(default_factory=list)
    sponsor_offer_date: str = ""
    brand_offers: list[dict[str, Any]] = field(default_factory=list)
    brand_offer_date: str = ""
    player_brand_offers: list[dict[str, Any]] = field(default_factory=list)
    player_brand_offer_date: str = ""
    friendlies: list[Fixture] = field(default_factory=list)
    pending_transfers: list[dict[str, Any]] = field(default_factory=list)
    daily_events: list[dict[str, Any]] = field(default_factory=list)
    chat_messages: list[dict[str, Any]] = field(default_factory=list)
    promoted_ids: list[str] = field(default_factory=list)
    relegated_ids: list[str] = field(default_factory=list)
    cup_round: int = 0
    cup_active: bool = False
    cup_winner_id: str = ""
    cup_third_id: str = ""
    press_done_round: int = 0
    press_history: list[dict[str, Any]] = field(default_factory=list)
    board_review: dict[str, Any] = field(default_factory=dict)
    free_agents: list[PlayerState] = field(default_factory=list)
    dhb_phase: int = 1
    dhb_groups: dict[str, list[str]] = field(default_factory=dict)
    dhb_group: str = "A"
    ehl: dict[str, Any] = field(default_factory=dict)
    retirements: list[dict[str, Any]] = field(default_factory=list)
    pending_events: list[dict[str, Any]] = field(default_factory=list)
    event_queue: list[dict[str, Any]] = field(default_factory=list)
    event_history: list[dict[str, Any]] = field(default_factory=list)
    event_flags: dict[str, Any] = field(default_factory=dict)
    negotiations: list[dict[str, Any]] = field(default_factory=list)
    loans: list[dict[str, Any]] = field(default_factory=list)
    loan_history: list[dict[str, Any]] = field(default_factory=list)
    opposition_instructions: dict[str, dict[str, str]] = field(default_factory=dict)
    affiliates: list[dict[str, Any]] = field(default_factory=list)
    affiliate_history: list[dict[str, Any]] = field(default_factory=list)
    match_history: list[dict[str, Any]] = field(default_factory=list)
    player_history: list[dict[str, Any]] = field(default_factory=list)
    awards_history: list[dict[str, Any]] = field(default_factory=list)
    scouting_assignments: list[dict[str, Any]] = field(default_factory=list)
    scouting_reports: list[dict[str, Any]] = field(default_factory=list)

    @property
    def total_rounds(self) -> int:
        from .competitions import competition

        meta = competition(self.competition)
        if meta.regular_rounds:
            return meta.regular_rounds
        n = len([t for t in self.teams.values() if t.league == self.competition])
        if not n:
            return meta.regular_rounds or 2
        rounds_per_leg = n if n % 2 else n - 1
        return max(2, 2 * rounds_per_leg)

    @property
    def user_team(self) -> TeamState:
        return self.teams[self.club_id]

    def table(self) -> list[TeamState]:
        from .competitions import competition

        teams = [t for t in self.teams.values() if t.league == self.competition]
        if competition(self.competition).system == "dhb_two_phase" and self.dhb_groups:
            ids = set(self.dhb_groups.get(self.dhb_group, []))
            teams = [t for t in teams if t.id in ids]
        return sorted(teams, key=lambda t: (-t.points, -(t.goals_for - t.goals_against), -t.goals_for, t.name))

    def user_position(self) -> int:
        table = self.table()
        for i, t in enumerate(table, 1):
            if t.id == self.club_id:
                return i
        return 0

    def next_user_fixture(self) -> Fixture | None:
        candidates = [
            f
            for f in self.fixtures
            if not f.played
            and self.club_id in (f.home_id, f.away_id)
            and (f.phase == "regular" or f.phase.startswith("cup_") or f.phase.startswith("promotion"))
        ]
        return (
            min(candidates, key=lambda f: (f.date, 0 if f.phase == "regular" else 1, f.round)) if candidates else None
        )

    def next_user_friendly(self) -> Fixture | None:
        candidates = [f for f in self.friendlies if not f.played and self.club_id in (f.home_id, f.away_id)]
        return min(candidates, key=lambda f: (f.date, f.id)) if candidates else None

    def to_dict(self) -> dict:
        return {
            "manager_name": self.manager_name,
            "club_id": self.club_id,
            "season": self.season,
            "competition": self.competition,
            "country": self.country,
            "seed": self.seed,
            "round": self.round,
            "date": self.date,
            "fixtures": [f.to_dict() for f in self.fixtures],
            "teams": {k: v.to_dict() for k, v in self.teams.items()},
            "phase": self.phase,
            "league_fixtures": {
                code: [f.to_dict() for f in fixtures] for code, fixtures in self.league_fixtures.items()
            },
            "promotion": self.promotion,
            "promotion_round": self.promotion_round,
            "final4": self.final4,
            "playout": self.playout,
            "history": self.history,
            "inbox": self.inbox,
            "last_result": self.last_result,
            "manual_lineup": self.manual_lineup,
            "week_trained": self.week_trained,
            "weekly_plan": self.weekly_plan,
            "training_report": self.training_report,
            "ai_training_round": self.ai_training_round,
            "finance_round": self.finance_round,
            "transfer_offers": self.transfer_offers,
            "market_history": self.market_history,
            "market_offers_round": self.market_offers_round,
            "market_offers_date": self.market_offers_date,
            "sponsor_offers": self.sponsor_offers,
            "sponsor_offer_date": self.sponsor_offer_date,
            "brand_offers": self.brand_offers,
            "brand_offer_date": self.brand_offer_date,
            "player_brand_offers": self.player_brand_offers,
            "player_brand_offer_date": self.player_brand_offer_date,
            "friendlies": [f.to_dict() for f in self.friendlies],
            "pending_transfers": self.pending_transfers,
            "daily_events": self.daily_events,
            "chat_messages": self.chat_messages,
            "promoted_ids": self.promoted_ids,
            "relegated_ids": self.relegated_ids,
            "cup_round": self.cup_round,
            "cup_active": self.cup_active,
            "cup_winner_id": self.cup_winner_id,
            "cup_third_id": self.cup_third_id,
            "press_done_round": self.press_done_round,
            "press_history": self.press_history,
            "board_review": self.board_review,
            "free_agents": [p.to_dict() for p in self.free_agents],
            "dhb_phase": self.dhb_phase,
            "dhb_groups": self.dhb_groups,
            "dhb_group": self.dhb_group,
            "ehl": self.ehl,
            "retirements": self.retirements,
            "pending_events": self.pending_events,
            "event_queue": self.event_queue,
            "event_history": self.event_history,
            "event_flags": self.event_flags,
            "negotiations": self.negotiations,
            "loans": self.loans,
            "loan_history": self.loan_history,
            "opposition_instructions": self.opposition_instructions,
            "affiliates": self.affiliates,
            "affiliate_history": self.affiliate_history,
            "match_history": self.match_history,
            "player_history": self.player_history,
            "awards_history": self.awards_history,
            "scouting_assignments": self.scouting_assignments,
            "scouting_reports": self.scouting_reports,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "GameState":
        state = cls(
            manager_name=d["manager_name"],
            club_id=d["club_id"],
            season=d["season"],
            competition=d.get("competition", "DHA"),
            country=d.get("country", "España"),
            seed=d["seed"],
            round=d["round"],
            date=d["date"],
            fixtures=[Fixture.from_dict(f) for f in d["fixtures"]],
            teams={k: TeamState.from_dict(v) for k, v in d["teams"].items()},
            phase=d.get("phase", "regular"),
            league_fixtures={
                code: [Fixture.from_dict(f) for f in fixtures]
                for code, fixtures in d.get("league_fixtures", {}).items()
            },
            promotion=d.get("promotion", {}),
            promotion_round=d.get("promotion_round", 0),
            final4=d.get("final4", {}),
            playout=d.get("playout", {}),
            history=d.get("history", []),
            inbox=d.get("inbox", []),
            last_result=d.get("last_result", {}),
            manual_lineup=d.get("manual_lineup", []),
            week_trained=d.get("week_trained", False),
            weekly_plan=d.get("weekly_plan", []),
            training_report=d.get("training_report", {}),
            ai_training_round=d.get("ai_training_round", 0),
            finance_round=d.get("finance_round", 0),
            transfer_offers=d.get("transfer_offers", []),
            market_history=d.get("market_history", []),
            market_offers_round=d.get("market_offers_round", 0),
            market_offers_date=d.get("market_offers_date", ""),
            sponsor_offers=d.get("sponsor_offers", []),
            sponsor_offer_date=d.get("sponsor_offer_date", ""),
            brand_offers=d.get("brand_offers", []),
            brand_offer_date=d.get("brand_offer_date", ""),
            player_brand_offers=d.get("player_brand_offers", []),
            player_brand_offer_date=d.get("player_brand_offer_date", ""),
            friendlies=[Fixture.from_dict(f) for f in d.get("friendlies", [])],
            pending_transfers=d.get("pending_transfers", []),
            daily_events=d.get("daily_events", []),
            chat_messages=d.get("chat_messages", []),
            promoted_ids=d.get("promoted_ids", []),
            relegated_ids=d.get("relegated_ids", []),
            cup_round=d.get("cup_round", 0),
            cup_active=d.get("cup_active", False),
            cup_winner_id=d.get("cup_winner_id", ""),
            cup_third_id=d.get("cup_third_id", ""),
            press_done_round=d.get("press_done_round", 0),
            press_history=d.get("press_history", []),
            board_review=d.get("board_review", {}),
            free_agents=[PlayerState.from_dict(p) for p in d.get("free_agents", [])],
            dhb_phase=d.get("dhb_phase", 1),
            dhb_groups=d.get("dhb_groups", {}),
            dhb_group=d.get("dhb_group", "A"),
            ehl=d.get("ehl", {}),
            retirements=d.get("retirements", []),
            pending_events=d.get("pending_events", []),
            event_queue=d.get("event_queue", []),
            event_history=d.get("event_history", []),
            event_flags=d.get("event_flags", {}),
            negotiations=d.get("negotiations", []),
            loans=d.get("loans", []),
            loan_history=d.get("loan_history", []),
            opposition_instructions=d.get("opposition_instructions", {}),
            affiliates=d.get("affiliates", []),
            affiliate_history=d.get("affiliate_history", []),
            match_history=d.get("match_history", []),
            player_history=d.get("player_history", []),
            awards_history=d.get("awards_history", []),
            scouting_assignments=d.get("scouting_assignments", []),
            scouting_reports=d.get("scouting_reports", []),
        )
        if state.league_fixtures.get(state.competition):
            # Los partidos de Copa y de la fase de ascenso viven en
            # `fixtures`, pero no en el calendario regular global.
            extras = [fixture for fixture in state.fixtures if fixture.phase != "regular"]
            state.fixtures = state.league_fixtures[state.competition] + extras
        return state
