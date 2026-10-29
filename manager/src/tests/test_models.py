from src.data_loader import load_teams
from src.models import FORMATION_SLOTS, Tactics


def test_auto_lineup_and_tactics():
    teams, _, _ = load_teams()
    t = teams["cd-terrassa"]
    line, bench = t.auto_lineup()
    assert len(line) == 11
    assert len({p.id for p in line}) == 11
    assert all(p.available for p in line)
    for formation in FORMATION_SLOTS:
        t.tactics.formation = formation
        line, _ = t.auto_lineup()
        assert len(line) == 11
        assert line[0].position_group == "Portero"
    t.tactics.formation = "4-3-3"
    line, _ = t.auto_lineup()
    slots = FORMATION_SLOTS["4-3-3"]
    assert line[0].position_group == "Portero"
    for slot, player in zip(slots[:5], line[:5]):
        assert player.slot_fit(slot) >= 3, (slot, player.name, player.subposition)

    t.tactics = Tactics(mentality="ofensiva", press="alta", tempo="rapido")
    assert t.tactics.attack_mod() > 0
    assert t.tactics.fatigue_mod() > 0
    assert Tactics(block="bajo").defense_mod() > 0
    assert Tactics(block="alto").attack_mod() > 0
    assert Tactics(passing="directo").attack_mod() > 0
    assert Tactics(width="estrecha").defense_mod() > 0


def test_auto_lineup_never_fields_unavailable_players():
    teams, _, _ = load_teams()
    team = teams["cd-terrassa"]
    for player in team.players[:14]:
        player.injury = 3
    line, _ = team.auto_lineup()
    assert line
    assert all(player.available for player in line)
