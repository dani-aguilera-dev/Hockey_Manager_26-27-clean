import random

from src.data_loader import load_teams
from src.match_engine import MatchEngine


def _engine(seed: int = 1) -> MatchEngine:
    teams, _, _ = load_teams()
    return MatchEngine(
        teams["cd-terrassa"],
        teams["sardinero"],
        random.Random(seed),
        detailed=True,
        match_date="2026-10-01",
    )


def test_momentum_starts_neutral_and_moves_with_goals():
    engine = _engine()
    engine.prepare()
    assert engine.momentum == 0.0
    scorer = engine._lineup(0)[5]
    engine._goal(0, scorer, None, "open")
    assert engine.momentum > 0.0
    assert engine.momentum_log[-1]["reason"] == "gol"
    engine._shift_momentum(1, 5.0, "prueba")
    assert engine.momentum == -1.0


def test_momentum_changes_possession_base():
    engine = _engine()
    engine.prepare()
    engine.momentum = -0.8
    low = engine._possession_base()
    engine.momentum = 0.8
    high = engine._possession_base()
    assert high > low


def test_carrier_is_an_outfield_player_and_respects_zone():
    engine = _engine()
    engine.prepare()
    engine.zone = "circle"
    carrier = engine._carrier(0)
    assert carrier.subposition != "Portero"
    engine.zone = "own_23"
    carrier = engine._carrier(0)
    assert carrier.subposition != "Portero"


def test_moments_record_player_decisions_and_fatigue():
    engine = _engine(2)
    engine.prepare()
    for _ in range(16):
        engine.advance_moment()
    decisions = sum(st.get("decisions", 0) for st in engine.player_stats.values())
    assert decisions > 0
    gk = next(p for p in engine._lineup(0) if p.subposition == "Portero")
    midfielders = [p for p in engine._lineup(0) if p.subposition == "Medio"]
    assert all(p.fatigue > gk.fatigue for p in midfielders)
    rows = engine.player_live_rows(0)
    assert all("decisions" in row for row in rows)


def test_free_hit_chain_is_recorded():
    engine = _engine(3)
    engine.prepare()
    engine.zone = "middle"
    engine._foul(0, foul_type="physical", advantage=False, distance_call=False, advance_10m=False)
    assert engine.stats[1]["free_hits"] == 1
    assert any(event["type"] == "free_hit" for event in engine.events)
    assert engine.possession in (0, 1)


def test_live_snapshot_exposes_momentum():
    engine = _engine(4)
    engine.prepare()
    engine.advance_moment()
    snapshot = engine.live_snapshot()
    assert "momentum" in snapshot
    assert -1.0 <= snapshot["momentum"] <= 1.0
    assert isinstance(snapshot["momentum_log"], list)
