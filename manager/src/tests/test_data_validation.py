from src.data_validation import validate_state
from src.models import PlayerState
from src.season import new_game


def test_new_game_data_has_no_errors():
    state = new_game("cd-terrassa", "Data Validation", seed=1401)
    report = validate_state(state)
    assert report["ok"] is True, report["errors"]
    assert report["summary"]["teams"] > 100
    assert report["summary"]["players"] > 3000
    assert report["summary"]["guests"] > 0


def test_validation_detects_staff_as_player_and_duplicate():
    state = new_game("cd-terrassa", "Data Validation", seed=1402)
    team = state.user_team
    clone = PlayerState.from_dict(team.players[0].to_dict())
    clone.name = "STAFF TEST"
    clone.perfil = "Entrenador"
    team.players.append(clone)
    team.players.append(PlayerState.from_dict({**team.players[0].to_dict(), "name": "DUPLICADO TEST"}))
    report = validate_state(state)
    assert report["ok"] is False
    kinds = {issue["kind"] for issue in report["errors"]}
    assert "staff_as_player" in kinds
    assert "duplicate_id" in kinds
