from src.data_loader import dha_teams, load_teams
from src.finance import apply_round_finances, financial_summary, sponsor_income
from src.season import new_game, play_round


def test_dha_staff_and_board_loaded():
    teams, _, _ = load_teams()
    dha = dha_teams(teams)
    assert len(dha) == 12
    for team in dha:
        assert team.staff, team.name
        assert any(m.role == "head_coach" for m in team.staff), team.name
        assert len(team.board) == 6, team.name
        assert team.staff_rating("fitness_coach") > 0
        assert team.staff_wage_bill() > 0
        assert team.transfer_budget > 0


def test_player_salaries_match_wage_budget():
    teams, _, _ = load_teams()
    for team in dha_teams(teams):
        assert abs(team.player_wage_bill() - team.wage_budget) <= 2, team.name
        assert team.player_wage_bill() > 0


def test_round_finances_and_summary():
    state = new_game("cd-terrassa", "Test", seed=401)
    cash_before = state.user_team.budget
    play_round(state, None, "equilibrado")
    log = state.user_team.finance_log
    assert state.finance_round == 1
    assert len(log) == 1
    entry = log[0]
    assert entry["round"] == 1
    assert entry["sponsor"] > 0
    assert entry["wages"] == entry["player_wages"] + entry["staff_wages"]
    assert state.user_team.budget == cash_before + entry["gate"] + entry["sponsor"] - entry["wages"] - entry["travel"]
    summary = financial_summary(state.user_team)
    assert summary["cash"] == state.user_team.budget
    assert summary["annual_wage_bill"] == state.user_team.wage_budget + state.user_team.staff_wage_bill()
    assert summary["sponsor_round"] == sponsor_income(state.user_team)


def test_finance_guard_same_round():
    state = new_game("cd-terrassa", "Test", seed=402)
    play_round(state, None, "equilibrado")
    state.round = 1
    before = len(state.user_team.finance_log)
    apply_round_finances(state)
    assert len(state.user_team.finance_log) == before
