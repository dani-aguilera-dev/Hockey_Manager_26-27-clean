from src.season import _create_promotion_groups, advance_to_next_season, new_game, play_round


def _finish(state):
    for _ in range(state.total_rounds):
        play_round(state, None, "equilibrado")


def test_regional_league_is_playable_and_has_promotion_playoff():
    state = new_game("reg-codema", "Regional", seed=1201)
    assert state.competition == "1N"
    assert len([t for t in state.teams.values() if t.league == "1N"]) == 10
    assert state.total_rounds == 18
    _finish(state)
    assert state.phase == "season_end"
    assert len(state.promoted_ids) == 2
    assert state.playout["format"] == "regional_promotion"
    assert len(state.playout["groups"]) == 4
    assert all(len(group["team_ids"]) == 4 for group in state.playout["groups"])
    assert all(len(group["table"]) == 4 for group in state.playout["groups"])
    assert len(state.playout["final_group"]["team_ids"]) == 4
    assert len(state.playout["final_group"]["table"]) == 4
    assert len(state.playout["final_group"]["promoted_ids"]) == 2
    assert state.playout.get("final") is not None


def test_primera_andalucia_is_playable_with_san_fernando():
    state = new_game("san-fernando-andaluza", "Regional", seed=1202)
    assert state.competition == "1A"
    assert len([t for t in state.teams.values() if t.league == "1A"]) == 8
    assert state.total_rounds == 14
    _finish(state)
    assert state.phase == "season_end"


def test_regional_champion_can_promote_to_dhb():
    state = new_game("reg-codema", "Regional", seed=1203)
    _finish(state)
    state.promoted_ids = [state.club_id]
    advance_to_next_season(state)
    assert state.user_team.league == "DHB"
    assert state.competition == "DHB"


def test_benalmadena_has_first_and_second_team_in_primera_andalucia():
    from src.regional import load_regional_teams

    teams, _, _ = load_regional_teams()
    primera = {team.name for team in teams.values() if team.league == "1A"}
    assert "RH PRIVÉ BENALMÁDENA" in primera
    assert "CHP BENALMÁDENA B" in primera


def test_regional_teams_do_not_repeat_players():
    from collections import Counter
    from src.regional import load_regional_teams

    teams, _, _ = load_regional_teams()
    names = Counter(player.name for team in teams.values() for player in team.players)
    assert not [name for name, count in names.items() if count > 1]


def test_all_regional_leagues_have_their_full_team_count():
    from src.competitions import competition
    from src.regional import load_regional_teams

    teams, _, _ = load_regional_teams()
    for code in ("1N", "1A", "1M", "1G", "1C", "1V", "SUP", "CAT1"):
        count = len([team for team in teams.values() if team.league == code])
        assert count == competition(code).teams, code


def test_every_regional_team_has_a_real_crest_file():
    from pathlib import Path
    from src.regional import load_regional_teams

    teams, _, _ = load_regional_teams()
    crests = Path(__file__).resolve().parents[2] / "web" / "static" / "crests"
    missing = [team.name for team in teams.values() if not (crests / f"{team.id}.png").exists()]
    assert not missing


def test_san_fernando_b_has_official_players_without_staff_or_duplicates():
    from src.data_loader import load_teams
    from src.regional import load_regional_teams

    base, _, _ = load_teams()
    first = next(team for team in base.values() if team.league == "DHB" and "San Fernando" in team.name)
    regional, _, _ = load_regional_teams()
    b = next(team for team in regional.values() if team.name == "CLUB DE HOCKEY SAN FERNANDO B")
    assert len(b.players) == 27
    assert len(first.players) == 15
    first_names = {player.name for player in first.players}
    b_names = {player.name for player in b.players}
    assert not first_names & b_names
    staff_names = {"MARCO ANTONIO ALEU RAMOS", "MIGUEL MUIÑO MORENO", "IDELFONSO FUENTES ASENCIO", "TRINIDAD BOZA LEON"}
    assert not b_names & staff_names
    lazaro = next(player for player in b.players if player.name == "LAZARO NAVAS MONTALVO")
    assert lazaro.position_group == "Portero"


def test_all_world_leagues_advance_in_the_same_round():
    state = new_game("cd-terrassa", "World", seed=1210)
    play_round(state, None, "equilibrado")
    for code in ("DHA", "DHB", "1A", "1N", "1G", "1M", "1C", "1V", "SUP", "CAT1", "NED", "BEL", "GER", "ENG", "ARG", "IND"):
        teams = [team for team in state.teams.values() if team.league == code]
        assert teams
        assert sum(team.played for team in teams) > 0, code


def test_regional_promotion_matches_can_be_played_by_the_user():
    state = new_game("reg-codema", "Promotion", seed=1211)
    for _ in range(state.total_rounds):
        play_round(state, None, "equilibrado")
    group = state.promotion["groups"][0]
    state.club_id = group["team_ids"][0]
    state.promotion = {}
    state.promotion_round = 0
    _create_promotion_groups(state)
    assert state.phase == "promotion"
    fixture = state.next_user_fixture()
    assert fixture is not None
    assert fixture.phase.startswith("promotion")
    play_round(state, None, "equilibrado")
    group = next(group for group in state.promotion["groups"] if state.club_id in group["team_ids"])
    assert sum(row["played"] for row in group["table"]) > 0


def test_no_player_is_in_two_teams_or_twice_in_the_free_agent_pool():
    from collections import Counter

    state = new_game("cd-terrassa", "Unique", seed=1212)
    names = [player.name for team in state.teams.values() for player in team.players]
    names += [player.name for player in state.free_agents]
    assert not [name for name, count in Counter(names).items() if count > 1]


def test_promotion_phase_generates_news():
    from src.news import news_feed

    state = new_game("reg-codema", "News", seed=1213)
    for _ in range(state.total_rounds):
        play_round(state, None, "equilibrado")
    group = state.promotion["groups"][0]
    state.club_id = group["team_ids"][0]
    state.promotion = {}
    state.promotion_round = 0
    _create_promotion_groups(state)
    items = news_feed(state)
    assert any(item.get("category") == "Ascenso" for item in items)
