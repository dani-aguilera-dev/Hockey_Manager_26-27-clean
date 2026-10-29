from src.data_loader import load_teams
from src.ratings import league_label, stars, stars_bar, tier
from src.season import new_game


def test_stars_are_relative_to_the_league():
    assert stars(69, "1A") == 4.5
    assert stars(69, "DHB") == 3.5
    assert stars(69, "DHA") == 2.5
    assert stars(60, "1A") == 3.5
    assert stars(64, "DHB") == 3.0
    assert stars(80, "DHA") == 3.5
    assert stars_bar(69, "1A").startswith("★★★★")
    assert "Estrella" in tier(69, "1A")
    assert "Rotación" in tier(69, "DHA")
    assert league_label("1A") == "1ª Andaluza"


def test_loaded_players_have_their_league_and_stars_change_on_promotion():
    teams, _, _ = load_teams()
    player = teams["cd-terrassa"].players[0]
    assert player.league == "DHA"
    before = stars(player.overall, player.league)
    player.league = "1A"
    after = stars(player.overall, player.league)
    assert after >= before
    state = new_game("cd-terrassa", "Test", seed=900)
    assert all(p.league == "DHA" for p in state.user_team.players)
    assert all(p.league in {"1A", "1N", "1M", "1G", "1C", "1V", "SUP", "CAT1"} for p in state.free_agents)


def test_spanish_league_ladder_has_clear_boundaries():
    import statistics
    from src.data_loader import load_teams
    from src.regional import load_regional_teams

    base, _, _ = load_teams()
    regional, _, _ = load_regional_teams()
    teams = {**base, **regional}

    def means(code):
        return sorted(
            statistics.mean(player.overall for player in team.players)
            for team in teams.values()
            if team.league == code
        )

    dha, dhb, primera = means("DHA"), means("DHB"), means("1A")
    assert statistics.mean(dha) > statistics.mean(dhb) > statistics.mean(primera)
    assert dha[0] >= dhb[-1] - 0.1
    assert dhb[0] >= primera[-1] - 0.1


def test_international_leagues_follow_the_world_hierarchy():
    import statistics
    from src.competitions import LEAGUE_RATING_TARGETS
    from src.international import load_international_teams

    teams, _, _ = load_international_teams()
    means = {}
    for code in ("NED", "BEL", "GER", "ENG", "ARG", "IND"):
        players = [player for team in teams.values() if team.league == code for player in team.players]
        means[code] = statistics.mean(player.overall for player in players)
        assert abs(means[code] - LEAGUE_RATING_TARGETS[code]) < 0.1
    assert means["NED"] > means["BEL"] > means["GER"] > means["ENG"] > means["ARG"] > means["IND"]
