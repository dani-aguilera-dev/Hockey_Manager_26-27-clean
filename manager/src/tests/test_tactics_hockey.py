from src.models import FORMATION_SLOTS
from src.season import new_game


def test_hockey_specific_tactics_modifiers_and_manual_specialists():
    state = new_game("cd-terrassa", "Test", seed=931)
    team = state.user_team
    line, _ = team.auto_lineup()
    assert len(line) == 11
    chosen = line[0]
    team.tactics.pc_injector_id = chosen.id
    team.tactics.pc_stopper_id = line[1].id
    team.tactics.pc_flicker_id = line[2].id
    team.tactics.pc_deflector_id = line[3].id
    team.tactics.pc_rebounder_id = line[4].id
    team.tactics.stroke_taker_id = line[5].id
    specs = team.specialists(line)
    assert specs["pc_injector"].id == chosen.id
    assert specs["pc_stopper"].id == line[1].id
    assert specs["pc_flicker"].id == line[2].id
    assert specs["pc_deflector"].id == line[3].id
    assert specs["pc_rebounder"].id == line[4].id
    assert specs["stroke_taker"].id == line[5].id

    team.tactics.defensive_system = "zona_baja"
    low_attack = team.tactics.attack_mod()
    low_defense = team.tactics.defense_mod()
    team.tactics.defensive_system = "individual_todo_campo"
    assert team.tactics.attack_mod() != low_attack
    assert team.tactics.defense_mod() != low_defense
    assert team.tactics.fatigue_mod() >= 0


def test_tactics_keep_legacy_defaults_for_old_saves():
    state = new_game("cd-terrassa", "Test", seed=932)
    data = state.user_team.tactics.to_dict()
    data.pop("defensive_system", None)
    data.pop("pc_injector_id", None)
    restored = type(state.user_team.tactics).from_dict(data)
    assert restored.defensive_system == "zona_media"
    assert restored.pc_injector_id == ""
    assert restored.attack_system == "posicional"
