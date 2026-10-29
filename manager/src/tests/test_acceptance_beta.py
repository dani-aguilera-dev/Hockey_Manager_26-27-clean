"""Matriz de aceptación deportiva/FIH de la beta avanzada."""

from collections import Counter
from datetime import date

from src import rules
from src.competitions import COMPETITIONS, competition, playable_competitions
from src.season import new_game


def test_fih_match_structure_and_discipline():
    assert rules.RULESET == "FIH_2027"
    assert rules.QUARTERS == 4
    assert rules.QUARTER_MINUTES == 15.0
    assert rules.PLAYERS_ON_FIELD == 11
    assert rules.MAX_SUBSTITUTES == 5
    assert rules.GREEN_CARD_MINUTES == 2
    assert rules.suspension_minutes("green") == 2
    assert rules.suspension_minutes("yellow", serious=False) == 5
    assert rules.suspension_minutes("yellow", serious=True) == 10
    assert rules.next_match_suspension("red") == 1
    assert rules.next_match_suspension("yellow") == 0
    assert rules.next_card_for_player(["green"]) == "yellow"
    assert rules.next_card_for_player(["yellow"]) == "red"


def test_dha_calendar_structure_is_complete():
    state = new_game("cd-terrassa", "Acceptance", seed=41)
    fixtures = [fixture for fixture in state.fixtures if fixture.phase == "regular"]
    assert len(fixtures) == 132
    assert len({fixture.round for fixture in fixtures}) == 22
    per_round = Counter(fixture.round for fixture in fixtures)
    assert set(per_round.values()) == {6}
    teams = {team.id for team in state.teams.values() if team.league == "DHA"}
    assert len(teams) == 12
    games = Counter()
    for fixture in fixtures:
        games[fixture.home_id] += 1
        games[fixture.away_id] += 1
    assert set(games) == teams
    assert set(games.values()) == {22}
    dates = [date.fromisoformat(fixture.date) for fixture in fixtures]
    assert dates == sorted(dates)
    pairs = {(fixture.home_id, fixture.away_id) for fixture in fixtures}
    assert len(pairs) == 132
    assert all((away, home) in pairs for home, away in pairs)


def test_competition_catalog_and_world_calendar():
    assert len(playable_competitions()) >= 16
    assert competition("DHA").teams == 12
    assert competition("DHB").teams == 16
    assert competition("NED").international is True
    assert competition("1A").format == "regional"
    state = new_game("cd-terrassa", "Acceptance", seed=42)
    assert state.league_fixtures
    assert "DHA" in state.league_fixtures
    assert "DHB" in state.league_fixtures
    assert any(code in state.league_fixtures for code in ("NED", "BEL", "GER", "ENG", "ARG", "IND"))
    assert all(fixture.phase == "regular" for fixtures in state.league_fixtures.values() for fixture in fixtures)


def test_spanish_competition_boundaries_are_declared():
    # La matriz no exige un nombre hardcodeado: comprueba que cada competición
    # declara sistema, número de equipos y formato.
    for meta in COMPETITIONS.values():
        assert meta.code
        assert meta.name
        assert meta.teams >= 2
        assert meta.format
        assert meta.system
    assert competition("DHA").system == "dha"
    assert competition("DHB").system == "dhb_two_phase"
    assert competition("1A").system == "regional"
