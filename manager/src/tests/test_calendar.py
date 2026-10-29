from collections import Counter

from src.calendar import create_dha_fixtures, dha_table, recompute_table
from src.data_loader import dha_teams, load_teams


def test_dha_calendar_shape():
    teams, _, _ = load_teams()
    ids = sorted(t.id for t in dha_teams(teams))
    fx = create_dha_fixtures(ids, "2026-09-20")
    assert len(fx) == 132
    assert sorted({f.round for f in fx}) == list(range(1, 23))
    per_round = Counter(f.round for f in fx)
    assert set(per_round.values()) == {6}
    home = Counter(f.home_id for f in fx)
    away = Counter(f.away_id for f in fx)
    assert set(home.values()) == {11}
    assert set(away.values()) == {11}
    # cada equipo juega 22 y cada pareja dos veces (ida y vuelta)
    pairs = Counter(tuple(sorted((f.home_id, f.away_id))) for f in fx)
    assert set(pairs.values()) == {2}
    ordered = Counter((f.home_id, f.away_id) for f in fx)
    assert max(ordered.values()) == 1


def test_dha_table_after_results():
    teams, _, _ = load_teams()
    ids = sorted(t.id for t in dha_teams(teams))
    fx = create_dha_fixtures(ids, "2026-09-20")
    fx[0].played = True
    fx[0].home_goals = 3
    fx[0].away_goals = 1
    recompute_table(teams, fx)
    table = dha_table(teams)
    winner = teams[fx[0].home_id]
    loser = teams[fx[0].away_id]
    assert winner.points == 3
    assert loser.points == 0
    assert winner.goals_for == 3
    assert loser.goals_against == 3
    assert table[0].points >= 3
