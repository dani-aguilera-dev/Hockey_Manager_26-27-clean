from src.models import GameState
from src.season import new_game
from src.shortlist import (
    add_to_shortlist,
    is_shortlisted,
    remove_from_shortlist,
    shortlist_candidates,
    shortlist_overview,
    update_shortlist_entry,
)


def test_shortlist_starts_empty_and_has_candidates():
    state = new_game("cd-terrassa", "Shortlist Test", seed=201)
    data = shortlist_overview(state)
    assert data["entries"] == []
    assert data["summary"]["total"] == 0
    candidates = shortlist_candidates(state)
    assert candidates
    assert all(candidate["team_name"] != state.user_team.name for candidate in candidates)


def test_add_update_and_remove_shortlist_entry():
    state = new_game("cd-terrassa", "Shortlist Test", seed=202)
    candidate = shortlist_candidates(state)[0]
    added = add_to_shortlist(state, candidate["id"], "alta", "Lateral con salida")
    assert added["ok"] is True
    assert is_shortlisted(state, candidate["id"]) is True
    data = shortlist_overview(state)
    assert data["summary"]["total"] == 1
    assert data["summary"]["high"] == 1
    assert data["entries"][0]["note"] == "Lateral con salida"
    updated = update_shortlist_entry(state, candidate["id"], "baja", "Revisar en verano")
    assert updated["ok"] is True
    assert shortlist_overview(state)["entries"][0]["priority"] == "baja"
    removed = remove_from_shortlist(state, candidate["id"])
    assert removed["ok"] is True
    assert shortlist_overview(state)["summary"]["total"] == 0


def test_shortlist_validation_and_persistence():
    state = new_game("cd-terrassa", "Shortlist Test", seed=203)
    own_player = state.user_team.players[0]
    assert add_to_shortlist(state, own_player.id)["ok"] is False
    assert add_to_shortlist(state, "no-existe")["ok"] is False
    candidate = shortlist_candidates(state)[0]
    assert add_to_shortlist(state, candidate["id"])["ok"] is True
    assert add_to_shortlist(state, candidate["id"])["ok"] is False
    assert update_shortlist_entry(state, "no-existe", "alta", "")["ok"] is False
    restored = GameState.from_dict(state.to_dict())
    assert is_shortlisted(restored, candidate["id"]) is True
    assert shortlist_overview(restored)["entries"][0]["priority"] == "media"
