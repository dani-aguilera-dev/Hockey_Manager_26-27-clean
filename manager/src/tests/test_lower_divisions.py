import statistics

from src.season import new_game


def _mean(players):
    return statistics.mean(p.overall for p in players) if players else 0


def test_lower_divisions_are_free_agents_with_estimated_positions():
    state = new_game("cd-terrassa", "Lower", seed=1001)
    assert len(state.free_agents) > 200
    lower = [p for p in state.free_agents if p.league != "1A"]
    assert lower
    assert all(p.team_name == "Agente libre" for p in state.free_agents)
    assert all(p.origin_team for p in lower)
    assert all(p.position_group in {"Portero", "Defensa", "Medio", "Delantero", "Polivalente"} for p in lower)
    assert {p.league for p in lower}.intersection({"1N", "1M", "1G", "1C"})


def test_league_average_order_and_promoted_teams_are_not_overrated():
    state = new_game("cd-terrassa", "Lower", seed=1002)
    dha = [p for t in state.teams.values() if t.league == "DHA" for p in t.players]
    dhb = [p for t in state.teams.values() if t.league == "DHB" for p in t.players]
    lower = [p for p in state.free_agents if p.league != "1A"]
    assert _mean(dha) > _mean(dhb) > _mean(lower)
    pozuelo = next(t for t in state.teams.values() if t.name == "Pozuelo")
    san_fernando = next(t for t in state.teams.values() if t.league == "DHB" and "San Fernando" in t.name)
    assert _mean(pozuelo.players) <= _mean(dhb) + 2.0
    assert _mean(san_fernando.players) <= _mean(dhb) + 2.0


def test_dhb_history_team_has_higher_average_than_never_promoted_team():
    state = new_game("cd-terrassa", "Lower", seed=1003)
    benalmadena = [p for p in state.free_agents if p.origin_team == "RH PRIVÉ BENALMÁDENA"]
    carranque = [p for p in state.free_agents if p.origin_team == "CARRANQUE ARCHIDONA CANDELARIA"]
    assert benalmadena and carranque
    assert _mean(benalmadena) > _mean(carranque)


def test_no_player_is_in_two_teams_or_in_the_free_agent_pool_twice():
    from collections import Counter

    state = new_game("cd-terrassa", "Unicidad", seed=1004)
    spanish = {"DHA", "DHB", "1A", "1N", "1M", "1G", "1C", "1V", "SUP", "CAT1"}
    names = [
        player.name
        for team in state.teams.values()
        if team.league in spanish
        for player in team.players
    ]
    names += [player.name for player in state.free_agents if player.league in spanish]
    repeated = [name for name, count in Counter(names).items() if count > 1]
    assert not repeated
