"""Constantes y tipos compartidos por el motor de partido."""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass, field
from typing import Any

from . import rules
from .models import PlayerState

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
