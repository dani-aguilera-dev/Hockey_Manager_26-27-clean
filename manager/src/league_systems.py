"""Sistemas de competición y orquestación del calendario global.

Cada competición declara su ``system`` en ``competitions.py``. Este módulo
traduce esa configuración a una clase concreta, sin repartir condiciones por
``season.py``. Así una liga nueva solo necesita declarar su sistema, su zona de
ascenso y sus equipos.
"""

from __future__ import annotations

from dataclasses import dataclass

from .calendar import create_fixtures, sort_table
from .competitions import Competition, COMPETITIONS
from .models import Fixture, GameState, TeamState


class LeagueSystem:
    """Contrato común para construir y consultar una competición."""

    def __init__(self, meta: Competition):
        self.meta = meta

    @property
    def code(self) -> str:
        return self.meta.code

    def build_fixtures(self, state: GameState, start: str | None = None) -> list[Fixture]:
        teams = sorted(
            (team for team in state.teams.values() if team.league == self.code),
            key=lambda team: team.id,
        )
        if len(teams) < 2:
            return []
        fixtures = create_fixtures(
            [team.id for team in teams],
            start or self.meta.start_date,
        )
        for fixture in fixtures:
            fixture.id = f"{self.code}-{fixture.id}"
        return fixtures

    def table(self, state: GameState) -> list[TeamState]:
        return sort_table([team for team in state.teams.values() if team.league == self.code])


class DoubleRoundRobinSystem(LeagueSystem):
    """Liga regular de ida y vuelta."""


class RegionalLeagueSystem(DoubleRoundRobinSystem):
    """Liga autonómica que alimenta la fase nacional de ascenso a DHB."""


class InternationalLeagueSystem(DoubleRoundRobinSystem):
    """Liga internacional con su propio calendario y play-offs."""


class DHASystem(LeagueSystem):
    """DHA: liga regular, Final Four y playout."""


class DHBTwoPhaseSystem(LeagueSystem):
    """DHB: dos grupos y segunda fase.

    Cuando el usuario no juega en DHB se usa una liga regular de 16 equipos
    para que su clasificación también avance y pueda consultarse. Cuando el
    usuario está en DHB, ``season.py`` construye las dos fases especiales.
    """

    def build_fixtures(self, state: GameState, start: str | None = None) -> list[Fixture]:
        if state.competition == self.code:
            return []
        return super().build_fixtures(state, start)


SYSTEMS: dict[str, type[LeagueSystem]] = {
    "double_round_robin": DoubleRoundRobinSystem,
    "dha": DHASystem,
    "dhb_two_phase": DHBTwoPhaseSystem,
    "regional": RegionalLeagueSystem,
    "international": InternationalLeagueSystem,
}


def system_for(meta: Competition) -> LeagueSystem:
    return SYSTEMS.get(meta.system, DoubleRoundRobinSystem)(meta)


@dataclass
class LeagueWorld:
    """Vista de todas las ligas que comparten un mismo GameState."""

    state: GameState

    @property
    def systems(self) -> dict[str, LeagueSystem]:
        return {
            meta.code: system_for(meta)
            for meta in COMPETITIONS.values()
            if any(team.league == meta.code for team in self.state.teams.values())
        }

    def build(self, start: str | None = None) -> None:
        self.state.league_fixtures = {}
        for code, system in self.systems.items():
            fixtures = system.build_fixtures(self.state, start)
            if fixtures:
                self.state.league_fixtures[code] = fixtures
        if self.state.competition in self.state.league_fixtures:
            self.state.fixtures = self.state.league_fixtures[self.state.competition]

    def fixtures(self) -> list[Fixture]:
        return [fixture for fixtures in self.state.league_fixtures.values() for fixture in fixtures]

    def round_fixtures(self, round_no: int) -> list[Fixture]:
        return [
            fixture
            for fixture in self.fixtures()
            if fixture.phase == "regular" and fixture.round == round_no and not fixture.played
        ]

    def table(self, code: str) -> list[TeamState]:
        system = self.systems.get(code)
        return system.table(self.state) if system else []
