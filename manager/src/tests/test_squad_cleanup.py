from src.season import new_game


def test_first_teams_have_no_guest_players_and_minimum_roster():
    state = new_game("cd-terrassa", "Squad Cleanup", seed=1201)
    for team in state.teams.values():
        if team.league not in ("DHA", "DHB"):
            continue
        assert len(team.players) >= 18, (team.name, len(team.players))
        assert all(player.perfil == "Jugador" for player in team.players), team.name
        assert all(player.team_name == team.name for player in team.players), team.name


def test_guests_move_to_market_with_origin_team():
    state = new_game("cd-terrassa", "Squad Cleanup", seed=1202)
    guests = [player for player in state.free_agents if player.origin_team]
    assert guests
    assert all(player.team_name == "Agente libre" for player in guests)
    assert any(player.league in ("DHA", "DHB") for player in guests)


def test_wage_budget_matches_cleaned_squad():
    state = new_game("cd-terrassa", "Squad Cleanup", seed=1203)
    for team in state.teams.values():
        assert team.wage_budget == sum(player.salary for player in team.players), team.name
