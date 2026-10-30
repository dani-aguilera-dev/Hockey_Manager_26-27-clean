import random

from src.models import GameState
from src.season import new_game
from src.vacancies import apply_vacancy, vacancy_overview


def test_vacancy_overview_has_candidates_and_summary():
    state = new_game("cd-terrassa", "Vacancies Test", seed=281)
    data = vacancy_overview(state)
    assert data["vacancies"]
    assert data["summary"]["vacancies"] >= len(data["vacancies"])
    assert all(vacancy["club_id"] != state.club_id for vacancy in data["vacancies"])
    assert all(0 <= vacancy["interest"] <= 1 for vacancy in data["vacancies"])


def test_apply_vacancy_accepted_creates_offer():
    state = new_game("cd-terrassa", "Vacancies Test", seed=282)
    vacancy = vacancy_overview(state)["vacancies"][0]
    result = apply_vacancy(state, vacancy["id"], rng=random.Random(1))
    assert result["ok"] is True
    assert result["accepted"] is True
    assert state.vacancy_applications[-1]["status"] == "offer"
    assert state.job_offers
    assert state.vacancy_applications[-1]["offer_id"] == state.job_offers[-1]["id"]
    assert result["offer"]["club_id"] == vacancy["club_id"]


def test_apply_vacancy_rejected_records_application():
    state = new_game("cd-terrassa", "Vacancies Test", seed=283)
    vacancy = vacancy_overview(state)["vacancies"][0]
    result = apply_vacancy(state, vacancy["id"], rng=random.Random(2))
    assert result["ok"] is True
    assert result["accepted"] is False
    assert state.vacancy_applications[-1]["status"] == "rejected"
    assert not state.job_offers


def test_vacancy_validation_duplicate_and_persistence():
    state = new_game("cd-terrassa", "Vacancies Test", seed=284)
    vacancy = vacancy_overview(state)["vacancies"][0]
    assert apply_vacancy(state, "no-existe")["ok"] is False
    assert apply_vacancy(state, vacancy["id"], rng=random.Random(1))["accepted"] is True
    assert apply_vacancy(state, vacancy["id"], rng=random.Random(1))["ok"] is False
    restored = GameState.from_dict(state.to_dict())
    assert restored.vacancy_applications[-1]["club_id"] == vacancy["club_id"]
    assert restored.job_offers
