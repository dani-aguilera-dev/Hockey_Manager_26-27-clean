import random

from src.data_loader import load_teams
from src.match_engine import MatchEngine
from src.season import finish_live_round, new_game, play_round, prepare_live_round


def _fresh_match(seed=123):
    teams, _, _ = load_teams()
    return teams, MatchEngine(teams["cd-terrassa"], teams["ud-taburiente"], random.Random(seed), detailed=True)


def test_quarter_stepping_matches_full_simulation():
    teams1, _, _ = load_teams()
    teams2, _, _ = load_teams()
    full = MatchEngine(teams1["cd-terrassa"], teams1["ud-taburiente"], random.Random(55), detailed=True)
    r_full = full.simulate()
    stepped = MatchEngine(teams2["cd-terrassa"], teams2["ud-taburiente"], random.Random(55), detailed=True)
    quarters = 0
    while not stepped.finished:
        events = stepped.advance_quarter()
        assert isinstance(events, list)
        quarters += 1
    assert quarters == 4
    assert (r_full.home_goals, r_full.away_goals) == (stepped.result.home_goals, stepped.result.away_goals)
    assert [e["text"] for e in r_full.events] == [e["text"] for e in stepped.result.events]
    assert stepped.result is not None


def test_manual_substitution():
    teams, engine = _fresh_match()
    engine.advance_quarter()
    bench = engine.bench_live_rows(0)
    starters = engine.player_live_rows(0)
    assert bench and starters
    ok, msg = engine.manual_substitute(0, starters[0]["id"], bench[0]["id"], coaching=True)
    assert ok, msg
    assert engine._subs[0] == 1
    assert any(e["type"] == "substitution" for e in engine.events)
    assert bench[0]["id"] in {p.id for p in engine.home_lineup}
    # no se puede repetir un jugador que ya está en el campo
    ok2, _ = engine.manual_substitute(0, starters[0]["id"], bench[0]["id"], coaching=True)
    assert not ok2


def test_live_round_updates_season():
    state = new_game("cd-terrassa", "Test", seed=2027)
    ctx = prepare_live_round(state, user_lineup_ids=None, travel_option_id="equilibrado")
    assert ctx.fixture.played is False
    # el resto de la jornada ya está resuelto
    assert sum(1 for f in state.fixtures if f.phase == "regular" and f.round == 1 and f.played) == 5
    while not ctx.engine.finished:
        ctx.engine.advance_quarter()
    payload = finish_live_round(state, ctx)
    assert ctx.fixture.played
    assert payload["result"] in ("Victoria", "Empate", "Derrota")
    assert state.round == 2
    assert sum(1 for f in state.fixtures if f.phase == "regular" and f.round == 1 and f.played) == 6
    assert state.user_team.last_lineup
    assert 1 <= state.user_team.cohesion <= 20
    assert 0 <= state.user_team.manager_rating <= 100


def test_live_and_quick_produce_same_user_result():
    quick_state = new_game("cd-terrassa", "Test", seed=303)
    quick = play_round(quick_state, user_lineup_ids=None, travel_option_id="equilibrado")
    live_state = new_game("cd-terrassa", "Test", seed=303)
    ctx = prepare_live_round(live_state, user_lineup_ids=None, travel_option_id="equilibrado")
    # misma configuración que la simulación rápida: charla delegada y cambios automáticos
    ctx.engine.auto_talk_sides = {0, 1}
    ctx.engine.auto_sub_sides = {0, 1}
    while not ctx.engine.finished:
        ctx.engine.advance_quarter()
    live = finish_live_round(live_state, ctx)
    assert (quick["home_goals"], quick["away_goals"]) == (live["home_goals"], live["away_goals"])
    assert quick["result"] == live["result"]


def test_team_talk_and_delegation():
    teams, engine = _fresh_match()
    engine.score = [0, 1]
    result = engine.apply_team_talk(0, "delegar")
    assert engine.talk_done[0] is True
    assert result["bonus"] != 0
    assert any(e["type"] == "talk" for e in engine.events)
    # solo una charla por equipo
    again = engine.apply_team_talk(0, "arenga")
    assert again["bonus"] == 0
    assert "Ya se ha dado" in again["message"]


def test_ai_reactive_tactics():
    teams, _, _ = load_teams()
    home = teams["cd-terrassa"]
    away = teams["ud-taburiente"]
    engine = MatchEngine(home, away, random.Random(3), ai_sides={0}, auto_talk_sides=set())
    engine.quarter = 3
    engine.score = [2, 0]
    home.manager_rating = 100
    before_away = (away.tactics.mentality, away.tactics.press, away.tactics.tempo)
    changed = False
    for seed in range(30):
        engine.rng = random.Random(seed)
        previous = (home.tactics.mentality, home.tactics.press, home.tactics.tempo)
        engine._ai_adjust(0)
        if (home.tactics.mentality, home.tactics.press, home.tactics.tempo) != previous:
            changed = True
            break
    assert changed
    assert home.tactics.mentality in ("defensiva", "muy_defensiva")
    assert (away.tactics.mentality, away.tactics.press, away.tactics.tempo) == before_away
    # el lado usuario no está en ai_sides: no se toca
    before_home = (home.tactics.mentality, home.tactics.press, home.tactics.tempo)
    engine._ai_adjust(1)
    assert (home.tactics.mentality, home.tactics.press, home.tactics.tempo) == before_home


def test_ai_talk_appears_in_full_match():
    teams, engine = _fresh_match(seed=77)
    result = engine.simulate()
    assert any(e["type"] == "talk" for e in result.events)


def test_management_bonus_affects_engine_strength():
    teams_hi, _, _ = load_teams()
    teams_lo, _, _ = load_teams()
    hi = teams_hi["fc-barcelona"]
    lo = teams_lo["fc-barcelona"]
    for t, good in ((hi, True), (lo, False)):
        t.morale = 20 if good else 1
        t.cohesion = 20 if good else 1
        t.board_confidence = 95 if good else 5
        t.fan_confidence = 95 if good else 5
        t.manager_rating = 95 if good else 5
    e_hi = MatchEngine(hi, teams_hi["rc-de-campo"], random.Random(1), neutral=True)
    e_lo = MatchEngine(lo, teams_lo["rc-de-campo"], random.Random(1), neutral=True)
    attack_hi, defense_hi, _, _ = e_hi._attack_defense()
    attack_lo, defense_lo, _, _ = e_lo._attack_defense()
    assert attack_hi > attack_lo
    assert defense_hi > defense_lo


def test_management_rewards_good_management():
    teams, _, _ = load_teams()
    team = teams["fc-barcelona"]
    lineup = team.auto_lineup()[0]
    low = team.management_score(lineup)
    team.morale = 20
    team.cohesion = 20
    team.board_confidence = 95
    team.fan_confidence = 95
    team.manager_rating = 95
    for p in team.players:
        p.fatigue = 0
    high = team.management_score(lineup)
    assert high > low
    assert -7.0 <= team.management_bonus(lineup) <= 7.0
