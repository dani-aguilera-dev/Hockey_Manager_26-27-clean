import random

from src.cup import cup_round_fixtures, cup_status_text, new_cup
from src.ehl import create_ehl, simulate_ehl
from src.press import answer_press, mark_press_done, press_questions
from src.season import (
    _process_age_and_retirements,
    new_game,
    play_round,
    season_summary,
    simulate_cup_remaining,
    simulate_cup_round,
)
from src.youth import (
    CATEGORY_AGES,
    YOUTH_CATEGORIES,
    category_for_age,
    community_pool,
    develop_youth,
    intake,
    promote_youth,
)


def test_cup_bracket_and_rounds():
    state = new_game("cd-terrassa", "Test", seed=601)
    new_cup(state)
    assert state.cup_active
    assert state.cup_round == 1
    assert len(cup_round_fixtures(state)) == 4
    simulate_cup_round(state)
    assert state.cup_round == 2
    assert len(cup_round_fixtures(state)) == 2
    simulate_cup_remaining(state)
    assert not state.cup_active
    assert state.cup_winner_id in state.teams
    assert "Campeón" in cup_status_text(state)


def test_youth_promotion_and_development():
    state = new_game("cd-terrassa", "Test", seed=602)
    team = state.user_team
    assert len(team.youth) >= 6
    assert {p.youth_category for p in team.youth} == set(YOUTH_CATEGORIES)
    before_players = len(team.players)
    before_youth = len(team.youth)
    ok, _ = promote_youth(team, team.youth[0].id)
    assert ok
    assert len(team.players) == before_players + 1
    assert len(team.youth) == before_youth - 1
    develop_youth(team, random.Random(1), 2027)
    intake(team, random.Random(2), 2027)
    assert len(team.youth) >= 3


def test_youth_names_follow_autonomous_community():
    state = new_game("aticos-san-fernando", "Test", seed=607)
    team = state.user_team
    assert team.community == "Andalucía"
    pool = community_pool("Andalucía")
    assert "Pau" not in pool["names"]
    for player in team.youth:
        parts = player.name.split()
        assert parts[0] in pool["names"]
        assert all(surname in pool["surnames"] for surname in parts[1:])
    assert category_for_age(14) == "Sub-16"
    assert category_for_age(16) == "Sub-18"
    assert category_for_age(18) == "Sub-21"
    assert category_for_age(21) == "Senior"
    assert CATEGORY_AGES["Sub-16"] == (14, 15)


def test_every_team_has_a_coach_from_isquad():
    from src.data_loader import load_teams

    teams, _, _ = load_teams()
    active = [t for t in teams.values() if t.league in ("DHA", "DHB")]
    assert active
    for team in active:
        assert any(member.role == "head_coach" for member in team.staff), team.name


def test_press_conference():
    state = new_game("cd-terrassa", "Test", seed=603)
    qs = press_questions(state)
    assert len(qs) >= 2
    result = answer_press(state, qs[0]["id"], 0)
    assert result["ok"]
    mark_press_done(state)
    assert state.press_done_round == state.round
    assert state.press_history


def test_ehl_tournament():
    state = new_game("cd-terrassa", "Test", seed=605)
    create_ehl(state)
    assert len(state.ehl["participants"]) == 8
    simulate_ehl(state)
    assert not state.ehl["active"]
    assert state.ehl["winner_name"]


def test_retirements():
    state = new_game("cd-terrassa", "Test", seed=606)
    player = state.user_team.players[0]
    player.age = 39
    _process_age_and_retirements(state)
    assert state.retirements
    assert all(p.id != player.id for p in state.user_team.players)


def test_board_review_after_season():
    state = new_game("cd-terrassa", "Test", seed=604)
    for _ in range(22):
        play_round(state, None, "equilibrado")
    assert state.phase == "season_end"
    summary = season_summary(state)
    review = summary.get("board_review") or {}
    assert review
    assert "target" in review and "position" in review
    assert 0 <= state.user_team.board_confidence <= 100
