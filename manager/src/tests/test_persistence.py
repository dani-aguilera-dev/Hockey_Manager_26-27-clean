import tempfile
from pathlib import Path

import pytest

from src.market import generate_incoming_offers, renew_contract
from src.persistence import delete_save, export_json, import_json, list_saves, load_game, rename_save, save_game
from src.season import ensure_week_training, new_game, play_round


def test_sqlite_roundtrip():
    state = new_game("cd-terrassa", "Test", seed=42)
    play_round(state)
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "test.db"
        name = save_game(state, "partida-test", db)
        assert list_saves(db)[0]["name"] == name
        loaded = load_game(name, db)
        assert loaded.club_id == state.club_id
        assert loaded.round == state.round
        assert loaded.user_team.points == state.user_team.points
        assert loaded.user_team.players[0].overall == state.user_team.players[0].overall
        assert loaded.last_result["home_goals"] == state.last_result["home_goals"]
        assert len(loaded.fixtures) == len(state.fixtures)
        assert loaded.user_team.staff[0].name == state.user_team.staff[0].name
        assert loaded.user_team.board[0].name == state.user_team.board[0].name
        assert loaded.user_team.players[0].salary == state.user_team.players[0].salary
        assert loaded.user_team.finance_log == state.user_team.finance_log
        assert loaded.finance_round == state.finance_round
        assert len(loaded.user_team.youth) == len(state.user_team.youth)
        assert len(loaded.free_agents) == len(state.free_agents)
        assert len(loaded.teams) == len(state.teams)


def test_old_save_backfills_player_photos():
    state = new_game("cd-terrassa", "Test", seed=90)
    for team in state.teams.values():
        for player in team.players:
            player.photo = ""
            player.photo_remote = ""
            player.league = ""
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "old.db"
        save_game(state, "old-save", db)
        loaded = load_game("old-save", db)
        assert any(player.photo for team in loaded.teams.values() for player in team.players)
        assert loaded.user_team.players[0].photo
        assert loaded.user_team.players[0].league == "DHA"


def test_old_save_backfills_staff():
    state = new_game("pozuelo", "Test", seed=91)
    for team in state.teams.values():
        team.staff = []
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "staff.db"
        save_game(state, "old-staff", db)
        loaded = load_game("old-staff", db)
        assert all(any(member.role == "head_coach" for member in team.staff) for team in loaded.teams.values())


def test_training_state_roundtrip():
    state = new_game("cd-terrassa", "Test", seed=88)
    ensure_week_training(state)
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "training.db"
        name = save_game(state, "training-test", db)
        loaded = load_game(name, db)
        assert loaded.week_trained is True
        assert loaded.weekly_plan == state.weekly_plan
        assert loaded.user_team.prep_bonus == state.user_team.prep_bonus
        assert loaded.training_report["plan_name"] == state.training_report["plan_name"]


def test_market_state_roundtrip():
    state = new_game("cd-terrassa", "Test", seed=89)
    generate_incoming_offers(state)
    player = max(state.user_team.players, key=lambda p: p.overall)
    renew_contract(state, player.id, player.salary * 2, 3)
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "market.db"
        name = save_game(state, "market-test", db)
        loaded = load_game(name, db)
        assert loaded.transfer_offers == state.transfer_offers
        assert loaded.market_history == state.market_history
        assert loaded.user_team.players[0].contract_until


def test_json_roundtrip():
    state = new_game("club-egara", "Test", seed=7)
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "save.json"
        export_json(state, path)
        loaded = import_json(path)
        assert loaded.club_id == "club-egara"
        assert loaded.round == state.round
        assert len(loaded.teams) == len(state.teams)


def test_old_save_backfills_lower_division_free_agents():
    state = new_game("cd-terrassa", "Test", seed=92)
    state.free_agents = [player for player in state.free_agents if player.league == "1A"]
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "lower.db"
        save_game(state, "old-lower", db)
        loaded = load_game("old-lower", db)
        assert len(loaded.free_agents) > 200
        assert any(player.league == "1N" for player in loaded.free_agents)


def test_old_save_migrates_ratings_to_new_scale():
    state = new_game("cd-terrassa", "Test", seed=93)
    player = next(p for p in state.free_agents if p.league == "1A")
    player.overall = 99.0
    state.event_flags.pop("ratings_v3", None)
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "ratings.db"
        save_game(state, "old-ratings", db)
        loaded = load_game("old-ratings", db)
        migrated = next(p for p in loaded.free_agents if p.name == player.name and p.league == "1A")
        assert migrated.overall < 90
        assert loaded.event_flags.get("ratings_v3") is True


def test_saves_can_be_renamed_and_deleted():
    state = new_game("cd-terrassa", "Test", seed=94)
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "saves.db"
        save_game(state, "carrera-a", db)
        save_game(state, "carrera-b", db)
        assert rename_save("carrera-a", "carrera-a-renombrada", db) == "carrera-a-renombrada"
        names = {row["name"] for row in list_saves(db)}
        assert "carrera-a-renombrada" in names
        assert "carrera-a" not in names
        with pytest.raises(ValueError):
            rename_save("carrera-b", "carrera-a-renombrada", db)
        assert delete_save("carrera-a-renombrada", db) is True
        assert "carrera-a-renombrada" not in {row["name"] for row in list_saves(db)}
        assert delete_save("no-existe", db) is False
