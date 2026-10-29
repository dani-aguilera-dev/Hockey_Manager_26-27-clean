import random

from src.data_loader import load_teams
from src.datahub import datahub_overview, set_instructions
from src.match_engine import MatchEngine
from src.models import GameState
from src.season import new_game


def test_datahub_has_opponent_analysis_key_players_and_options():
    state = new_game("cd-terrassa", "Datahub Test", seed=71)
    data = datahub_overview(state)
    assert data["fixture"] is not None
    assert data["opponent"]["id"] != state.club_id
    assert data["key_players"]
    assert data["options"]
    assert data["analysis"]
    assert data["opponent"]["stats"]["played"] >= 0
    assert data["user"]["stats"]["form"]
    assert data["fixture"]["home_name"] and data["fixture"]["away_name"]


def test_set_instructions_validates_players_and_saves():
    state = new_game("cd-terrassa", "Datahub Test", seed=72)
    data = datahub_overview(state)
    opponent = data["opponent"]
    player_id = data["key_players"][0]["id"]
    result = set_instructions(
        state,
        opponent["id"],
        {player_id: "tight_marking", "no-existe": "press", player_id + "-x": "double_team"},
    )
    assert result["ok"] is True
    assert result["instructions"] == {player_id: "tight_marking"}
    assert state.opposition_instructions[opponent["id"]][player_id] == "tight_marking"
    cleared = set_instructions(state, opponent["id"], {})
    assert cleared["ok"] is True
    assert opponent["id"] not in state.opposition_instructions


def test_opposition_instructions_reduce_opponent_strength():
    teams, _, _ = load_teams()
    home = teams["cd-terrassa"]
    away = teams["sardinero"]
    base = MatchEngine(home, away, random.Random(1), detailed=True)
    base_attack, base_defense = base._attack_defense()[2], base._attack_defense()[3]
    ids = [player.id for player in away.auto_lineup()[0][:4]]
    instructions = {player_id: "tight_marking" for player_id in ids}
    modified = MatchEngine(
        home,
        away,
        random.Random(1),
        detailed=True,
        opposition=instructions,
        opposition_side=1,
    )
    attack, defense = modified._attack_defense()[2], modified._attack_defense()[3]
    assert modified.opposition_effect(1)["players"] == 4
    assert attack < base_attack
    assert defense <= base_defense
    assert modified.live_snapshot()["opposition"]["effect"]["attack"] > 0


def test_opposition_instructions_persist_in_game_state():
    state = new_game("cd-terrassa", "Datahub Test", seed=73)
    data = datahub_overview(state)
    opponent_id = data["opponent"]["id"]
    player_id = data["key_players"][0]["id"]
    set_instructions(state, opponent_id, {player_id: "press"})
    restored = GameState.from_dict(state.to_dict())
    assert restored.opposition_instructions[opponent_id][player_id] == "press"
