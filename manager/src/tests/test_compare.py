from src.compare import compare_candidates, compare_players
from src.season import new_game


def test_compare_candidates_returns_players_and_filters():
    state = new_game("cd-terrassa", "Compare Test", seed=231)
    candidates = compare_candidates(state, limit=20)
    assert candidates
    assert all(candidate["id"] and candidate["name"] for candidate in candidates)
    needle = candidates[0]["name"].split()[0].lower()
    filtered = compare_candidates(state, needle, limit=20)
    assert filtered
    assert all(needle in candidate["name"].lower() for candidate in filtered)


def test_compare_players_has_attributes_categories_and_summary():
    state = new_game("cd-terrassa", "Compare Test", seed=232)
    candidates = compare_candidates(state, limit=2)
    result = compare_players(state, candidates[0]["id"], candidates[1]["id"])
    assert result["ok"] is True
    assert result["a"]["id"] != result["b"]["id"]
    assert result["attributes"]
    assert result["categories"]
    assert sum(category["rows"].__len__() for category in result["categories"]) == len(result["attributes"])
    summary = result["summary"]
    assert summary["a_wins"] + summary["b_wins"] + summary["ties"] == summary["attributes"]
    assert summary["winner"] in ("a", "b", "tie")
    assert "overall" in result["differences"]
    assert all(row["winner"] in ("a", "b", "tie") for row in result["attributes"])


def test_compare_validation():
    state = new_game("cd-terrassa", "Compare Test", seed=233)
    candidate = compare_candidates(state, limit=1)[0]
    assert compare_players(state, "", candidate["id"])["ok"] is False
    assert compare_players(state, candidate["id"], candidate["id"])["ok"] is False
    assert compare_players(state, candidate["id"], "no-existe")["ok"] is False
