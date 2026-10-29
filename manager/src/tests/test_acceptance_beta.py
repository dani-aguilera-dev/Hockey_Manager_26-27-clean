"""Matriz de aceptación deportiva/FIH de la beta avanzada."""

import random
from collections import Counter
from datetime import date

from src import rules
from src.competitions import COMPETITIONS, competition, playable_competitions
from src.data_loader import load_teams
from src.match_engine import MatchEngine
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


def test_penalty_corner_stroke_and_referee_are_exposed():
    teams, _, _ = load_teams()
    engine = MatchEngine(teams["cd-terrassa"], teams["ud-taburiente"], random.Random(88), detailed=True)
    assert engine.referee["name"]
    assert engine.referee["style"]
    before_pc = engine.stats[0]["pc"]
    engine._penalty_corner(0)
    assert engine.stats[0]["pc"] > before_pc
    assert any(event["type"] == "pc" for event in engine.events)
    before_strokes = engine.stats[0]["strokes"]
    engine._stroke(0)
    assert engine.stats[0]["strokes"] > before_strokes
    assert any(event["type"] == "stroke" for event in engine.events)
    result = engine.simulate()
    assert result.referee["name"] == engine.referee["name"]


def test_shootout_resolves_draw_with_five_rounds_and_winner():
    teams, _, _ = load_teams()
    engine = MatchEngine(teams["cd-terrassa"], teams["ud-taburiente"], random.Random(19), detailed=True, knockout=True)
    shootout = engine._shootout()
    assert len(shootout["log"]) >= 5
    assert shootout["home_score"] != shootout["away_score"]
    assert shootout["winner_id"] in (engine.home.id, engine.away.id)
    assert all("home_goal" in row and "away_goal" in row for row in shootout["log"])


def test_substitution_limit_and_red_card_suspension():
    teams, _, _ = load_teams()
    engine = MatchEngine(teams["cd-terrassa"], teams["ud-taburiente"], random.Random(91), detailed=True)
    engine.advance_quarter()
    for _ in range(5):
        starters = [p for p in engine._lineup(0) if p.available]
        bench = [p for p in engine._bench(0) if p.available]
        if not starters or not bench:
            break
        ok, _ = engine.manual_substitute(0, starters[0].id, bench[0].id, coaching=True)
        assert ok
    assert engine._subs[0] == 5
    starters = [p for p in engine._lineup(0) if p.available]
    bench = [p for p in engine._bench(0) if p.available]
    if starters and bench:
        ok, message = engine.manual_substitute(0, starters[0].id, bench[0].id, coaching=True)
        assert not ok
        assert "cambios" in message.lower()

    red_engine = MatchEngine(teams["cd-terrassa"], teams["ud-taburiente"], random.Random(92), detailed=True)
    player = red_engine._lineup(0)[0]
    player.suspension = 1
    ok, message = red_engine.manual_substitute(0, player.id, red_engine._bench(0)[0].id)
    assert not ok
    assert "sancionado" in message.lower() or "suspendido" in message.lower()


class _FixedRng:
    """RNG mínimo para forzar el resultado de una revisión de vídeo."""

    def __init__(self, value: float):
        self.value = value

    def random(self) -> float:
        return self.value

    def gauss(self, mu: float, sigma: float) -> float:
        return 0.0

    def choice(self, seq):
        return seq[0]

    def choices(self, seq, weights=None, k=1):
        return [seq[0]] * k

    def sample(self, seq, k):
        return list(seq)[:k]


def test_video_review_overturns_goal_and_retains_referral():
    teams, _, _ = load_teams()
    engine = MatchEngine(teams["cd-terrassa"], teams["ud-taburiente"], random.Random(101), detailed=True)
    engine.prepare()
    scorer = engine._lineup(0)[0]
    engine._goal(0, scorer, None, "open")
    assert engine.score == [1, 0]
    assert engine.last_decision["type"] == "goal"
    assert engine.last_decision["side"] == 0
    engine.rng = _FixedRng(0.0)
    result = engine.review_decision(1, "goal")
    assert result["ok"] is True
    assert result["review"]["overturned"] is True
    assert engine.score == [0, 0]
    assert engine.stats[0]["goals"] == 0
    assert engine.player_stats[scorer.id]["goals"] == 0
    # Una revisión acertada conserva la referencia.
    assert engine.referrals[1] == 1
    assert any(event["type"] == "review" for event in engine.events)


def test_video_review_upheld_consumes_referral():
    teams, _, _ = load_teams()
    engine = MatchEngine(teams["cd-terrassa"], teams["ud-taburiente"], random.Random(102), detailed=True)
    engine.prepare()
    scorer = engine._lineup(0)[0]
    engine._goal(0, scorer, None, "open")
    engine.rng = _FixedRng(0.99)
    result = engine.review_decision(1, "goal")
    assert result["ok"] is True
    assert result["review"]["overturned"] is False
    assert engine.score == [1, 0]
    assert engine.referrals[1] == 0
    # La misma decisión no se puede revisar dos veces.
    again = engine.review_decision(1, "goal")
    assert again["ok"] is False


def test_penalty_corner_and_stroke_are_reviewable():
    teams, _, _ = load_teams()
    engine = MatchEngine(teams["cd-terrassa"], teams["ud-taburiente"], random.Random(104), detailed=True)
    engine.prepare()
    engine._penalty_corner(0)
    assert engine.last_decision["type"] == "penalty_corner"
    engine._stroke(1)
    assert engine.last_decision["type"] == "penalty_stroke"
    engine.rng = _FixedRng(0.0)
    result = engine.review_decision(0, "penalty_stroke")
    assert result["ok"] is True
    assert result["review"]["type"] == "penalty_stroke"


def test_video_review_rejects_own_decision_and_unknown_play():
    teams, _, _ = load_teams()
    engine = MatchEngine(teams["cd-terrassa"], teams["ud-taburiente"], random.Random(103), detailed=True)
    engine.prepare()
    assert engine.review_decision(0, "goal")["ok"] is False
    engine._goal(0, engine._lineup(0)[0], None, "open")
    assert engine.review_decision(0, "goal")["ok"] is False
    assert engine.review_decision(1, "penalty_stroke")["ok"] is False
    assert engine.review_decision(1, "goal")["ok"] is True
