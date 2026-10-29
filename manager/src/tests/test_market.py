from src.market import (
    asking_price,
    fire_staff,
    generate_incoming_offers,
    hire_staff,
    make_transfer_offer,
    market_players,
    market_window,
    renew_contract,
    staff_candidates,
)
from src.season import advance_to_next_season, new_game, play_round, season_summary


def test_market_window():
    state = new_game("cd-terrassa", "Test", seed=501)
    assert market_window(state) == "verano"
    play_round(state, None, "equilibrado")
    # El primer partido no cierra el mercado: sigue abierto hasta el 30/09.
    assert market_window(state) == "verano"
    state.date = "2026-10-01"
    assert market_window(state) == "cerrado"
    state.date = "2027-01-01"
    assert market_window(state) == "invierno"
    state.date = "2027-02-01"
    assert market_window(state) == "cerrado"


def test_transfer_and_contracts():
    state = new_game("cd-terrassa", "Test", seed=502)
    state.user_team.transfer_budget = 2_000_000
    players = market_players(state, limit=30, max_value=1_000_000)
    assert players
    player = min(players, key=lambda p: p.value)
    old_team = next(t for t in state.teams.values() if any(p.id == player.id for p in t.players))
    result = make_transfer_offer(state, player.id, max(asking_price(player), 1), player.salary * 2, 3)
    if result["ok"]:
        assert any(p.id == player.id for p in state.user_team.players)
        assert not any(p.id == player.id for p in old_team.players)
        assert state.market_history
    # renovación de un jugador propio
    own = max(state.user_team.players, key=lambda p: p.overall)
    renewed = renew_contract(state, own.id, own.salary * 2, 3)
    assert "message" in renewed
    if renewed["ok"]:
        assert own.contract_until.endswith("-06-30")


def test_incoming_offers_shape():
    state = new_game("cd-terrassa", "Test", seed=503)
    offers = generate_incoming_offers(state)
    for offer in offers:
        assert offer["player_id"]
        assert offer["from_club_id"] != state.club_id
        assert offer["fee"] >= 0


def test_staff_hire_and_fire():
    state = new_game("cd-terrassa", "Test", seed=504)
    team = state.user_team
    role = next(m.role for m in team.staff if m.role not in ("head_coach", "delegate", "additional"))
    fired = fire_staff(state, role)
    assert fired["ok"]
    candidates = staff_candidates(team, "scout", __import__("random").Random(1))
    hired = hire_staff(state, candidates[0])
    assert hired["ok"]
    assert any(m.role == "scout" for m in team.staff)


def test_multi_season_transition():
    state = new_game("cd-terrassa", "Test", seed=505)
    for _ in range(22):
        play_round(state, None, "equilibrado")
    assert state.phase == "season_end"
    old_season = state.season
    advance_to_next_season(state)
    assert state.phase == "regular"
    assert state.season != old_season
    assert state.round == 1
    assert len([t for t in state.teams.values() if t.league == "DHA"]) == 12
    assert len([t for t in state.teams.values() if t.league == "DHB"]) == 16
    regular = [f for f in state.fixtures if f.phase == "regular"]
    assert len(regular) == len([f for f in state.league_fixtures[state.competition] if f.phase == "regular"])
    assert state.total_rounds == (22 if state.competition == "DHA" else 21 if state.competition == "DHB" else state.total_rounds)
    assert all(len(t.players) >= 18 for t in state.teams.values() if t.league in ("DHA", "DHB"))


def test_free_agents_from_primera_andaluza():
    state = new_game("cd-terrassa", "Test", seed=506)
    assert state.free_agents
    assert all(p.team_name == "Agente libre" for p in state.free_agents)
    assert any(t.league == "1A" for t in state.teams.values())
    state.user_team.transfer_budget = 100000
    free = None
    result = {"ok": False}
    for candidate in state.free_agents[:15]:
        result = make_transfer_offer(state, candidate.id, 0, max(20000, candidate.salary * 3), 3)
        if result["ok"]:
            free = candidate
            break
    assert result["ok"]
    assert any(p.id == free.id for p in state.user_team.players)
    assert not any(p.id == free.id for p in state.free_agents)


def test_new_game_dhb_is_playable():
    state = new_game("pozuelo", "Test", seed=508)
    assert state.competition == "DHB"
    assert state.dhb_phase == 1
    assert len(state.dhb_groups["A"]) == 8
    assert len(state.dhb_groups["B"]) == 8
    regular = [f for f in state.fixtures if f.phase == "regular"]
    assert len(regular) == 112
    assert state.total_rounds == 21
    for _ in range(14):
        play_round(state, None, "equilibrado")
    assert state.dhb_phase == 2
    assert state.round == 15


def test_dhb_two_phase_setup():
    from src.season import setup_dhb_phase1, setup_dhb_phase2

    state = new_game("cd-terrassa", "Test", seed=507)
    state.competition = "DHB"
    setup_dhb_phase1(state, "2026-09-20")
    assert state.dhb_phase == 1
    assert sorted(len(v) for v in state.dhb_groups.values()) == [8, 8]
    regular = [f for f in state.fixtures if f.phase == "regular"]
    assert len(regular) == 112
    assert max(f.round for f in regular) == 14
    setup_dhb_phase2(state)
    assert state.dhb_phase == 2
    assert sorted(len(v) for v in state.dhb_groups.values()) == [8, 8]
    regular = [f for f in state.fixtures if f.phase == "regular"]
    assert len(regular) == 168
    assert max(f.round for f in regular) == 21
