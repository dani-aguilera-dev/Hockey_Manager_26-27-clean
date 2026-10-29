from pathlib import Path

import pytest

from src.competitions import COMPETITIONS
from src.international import load_international_teams
from src.market import market_players
from src.persistence import load_game, save_game
from src.ratings import stars
from src.season import advance_to_next_season, new_game, play_round


INTERNATIONAL_CASES = [
    ("ned-amsterdam", "NED", 12, 132),
    ("bel-dragons", "BEL", 12, 132),
    ("ger-rw-koln", "GER", 12, 132),
    ("eng-surbiton", "ENG", 12, 132),
    ("arg-san-fernando", "ARG", 14, 182),
    ("ind-kalinga-lancers", "IND", 8, 56),
]


@pytest.mark.parametrize("club_id,league,team_count,fixture_count", INTERNATIONAL_CASES)
def test_international_leagues_are_playable(club_id, league, team_count, fixture_count):
    state = new_game(club_id, "Test", seed=801)
    assert state.competition == league
    assert state.country == COMPETITIONS[league].country
    assert len([t for t in state.teams.values() if t.league == league]) == team_count
    assert len([f for f in state.fixtures if f.phase == "regular"]) == fixture_count
    assert state.total_rounds == 2 * (team_count - 1)
    assert len(state.user_team.players) >= 18
    assert state.user_team.country == state.country
    assert any(m.role == "head_coach" for m in state.user_team.staff)
    result = play_round(state, None, "equilibrado")
    assert result
    assert state.round == 2
    assert len(state.table()) == team_count
    assert state.user_position() >= 1


def test_international_market_and_ratings():
    state = new_game("ned-amsterdam", "Test", seed=802)
    pool = market_players(state, limit=1000)
    assert pool
    assert any(p.league == "NED" for p in pool if p.team_name != "Agente libre")
    assert all(p.league in COMPETITIONS for p in pool)
    assert stars(80, "NED") < stars(80, "DHA")


def test_international_persistence_roundtrip(tmp_path):
    state = new_game("eng-surbiton", "Test", seed=803)
    path = Path(tmp_path) / "intl.db"
    save_game(state, "intl-test", path)
    loaded = load_game("intl-test", path)
    assert loaded.country == "Inglaterra"
    assert loaded.competition == "ENG"
    assert loaded.user_team.country == "Inglaterra"
    assert len(loaded.user_team.players) >= 18


def test_international_season_transition():
    state = new_game("ind-kalinga-lancers", "Test", seed=804)
    for _ in range(14):
        play_round(state, None, "equilibrado")
    assert state.phase == "season_end"
    assert state.final4.get("champion_id")
    old = state.season
    advance_to_next_season(state)
    assert state.phase == "regular"
    assert state.season != old
    assert state.competition == "IND"
    assert state.round == 1
    assert len([f for f in state.fixtures if f.phase == "regular"]) == 56
    assert len(state.user_team.players) >= 18


def test_international_clubs_are_complete():
    teams, clubs, cities = load_international_teams()
    assert len(teams) == 70
    assert len(clubs) == 70
    for team in teams.values():
        assert team.country
        assert len(team.players) >= 18
        assert team.stadium_name
        assert team.staff
        assert all(p.league == team.league for p in team.players)
    assert len(cities) >= 40


def test_real_dutch_and_belgian_squads_have_media():
    teams, _, _ = load_international_teams()
    root = Path(__file__).resolve().parents[3]
    photos = root / "jugadores"
    crests = root / "manager" / "web" / "static" / "crests"
    for league, minimum in (("NED", 230), ("BEL", 230), ("GER", 300), ("IND", 150)):
        squad = [p for t in teams.values() if t.league == league for p in t.players]
        assert len(squad) >= minimum
        assert sum(bool(p.photo) for p in squad) >= minimum - 15
        for team in (t for t in teams.values() if t.league == league):
            assert any(crests.glob(f"{team.id}.*")), team.id
    for player in (p for t in teams.values() if t.league in ("NED", "BEL") for p in t.players):
        if player.photo:
            assert (photos / player.photo).exists(), player.photo


def test_real_england_and_argentina_squads_and_crests():
    teams, _, _ = load_international_teams()
    root = Path(__file__).resolve().parents[3]
    crests = root / "manager" / "web" / "static" / "crests"
    for league, minimum in (("ENG", 240), ("ARG", 420)):
        squad = [p for t in teams.values() if t.league == league for p in t.players]
        assert len(squad) >= minimum, league
        assert all(p.name for p in squad)
        for team in (t for t in teams.values() if t.league == league):
            assert any(crests.glob(f"{team.id}.*")), team.id


def test_luis_calzado_is_a_goalkeeper():
    teams, _, _ = load_international_teams()
    kampong = next(t for t in teams.values() if t.id == "ned-kampong")
    calzado = next(p for p in kampong.players if p.name == "Luis Calzado")
    assert calzado.position_group == "Portero"
    assert calzado.subposition == "Portero"
