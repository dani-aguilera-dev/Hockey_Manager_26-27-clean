import pytest

from src.brands import accept_brand_offer, brand_summary, load_brands
from src.data_loader import load_clubs
from src.friendlies import (
    available_friendly_dates,
    friendly_candidates,
    play_friendly,
    schedule_friendly,
)
from src.international import international_data
from src.player_editor import edit_player, find_player
from src.press import answer_press, press_context, press_questions
from src.season import new_game


@pytest.fixture()
def client(tmp_path):
    import web.app as web

    web.WEB_DB = tmp_path / "web.db"
    web.GAMES.clear()
    web.LIVE.clear()
    web.app.config.update(TESTING=True)
    with web.app.test_client() as test_client:
        yield test_client


def _new_api(client, club="cd-terrassa", seed="31"):
    response = client.post("/api/new-game", json={"club_id": club, "manager": "Beta Test", "seed": seed})
    assert response.status_code == 200, response.get_data(as_text=True)
    return response.get_json()["data"]


def test_staff_are_not_loaded_as_players():
    state = new_game("cd-terrassa", "Beta Test", seed=30)
    profiles = {player.perfil for team in state.teams.values() for player in team.players}
    assert profiles <= {"Jugador", "Invitado"}
    names = {player.name for team in state.teams.values() for player in team.players}
    assert "BERTA PUENTE SABATES" not in names
    assert "NURIA ALVAREZ PASCUAL" not in names
    assert "MARIA LAURA PERRONE" not in names
    # Los perfiles de cuerpo técnico siguen existiendo en el staff del club.
    assert any(member.role == "head_coach" for member in state.user_team.staff)


def test_clubs_have_verified_location_and_description():
    clubs, _ = load_clubs()
    assert len(clubs) == 29
    assert all(club.get("city") for club in clubs.values())
    assert all(club.get("province") for club in clubs.values())
    assert all(club.get("history") for club in clubs.values())
    assert all(club.get("source_url", "").startswith("http") for club in clubs.values())
    assert all(club.get("description_verified") for club in clubs.values())
    giner = clubs["cd-giner"]
    assert giner["city"] == "Valencia"
    assert giner["province"] == "Valencia"
    assert giner["community"] == "Comunidad Valenciana"
    assert giner["founded"] == 1993
    assert "Campanar" in giner["history"]
    intl = international_data()["clubs"]
    assert len(intl) == 70
    assert all(club.get("city") and club.get("country") and club.get("history") for club in intl)
    assert all(club.get("source_url", "").startswith("http") for club in intl)
    assert all(club.get("description_verified") for club in intl)
    assert all(len(club.get("history", "")) >= 120 for club in intl)


def test_friendlies_are_scheduled_and_do_not_touch_league_table():
    state = new_game("cd-terrassa", "Beta Test", seed=31)
    before_points = {team.id: team.points for team in state.teams.values()}
    dates = available_friendly_dates(state)
    candidates = friendly_candidates(state)
    assert dates and candidates
    result = schedule_friendly(state, candidates[0]["id"], dates[0], home=True, notes="probar el once")
    assert result["ok"] is True
    friendly_id = result["friendly"]["id"]
    state.date = result["friendly"]["date"]
    played = play_friendly(state, friendly_id)
    assert played["ok"] is True
    assert played["report"]["phase"] == "friendly"
    assert state.friendlies[0].played is True
    assert before_points == {team.id: team.points for team in state.teams.values()}


def test_brand_offers_and_equipment_bonus():
    state = new_game("cd-terrassa", "Beta Test", seed=32)
    summary = brand_summary(state)
    assert summary["offers"]
    assert any(brand["name"] == "Osaka" for brand in load_brands())
    offer = summary["offers"][0]
    result = accept_brand_offer(state, offer["id"])
    assert result["ok"] is True
    assert state.user_team.equipment_deals
    assert state.user_team.equipment_bonus > 0


def test_player_editor_can_fix_position_and_attributes():
    state = new_game("cd-terrassa", "Beta Test", seed=33)
    player = state.user_team.players[0]
    result = edit_player(
        state,
        player.id,
        {
            "position_group": "Medio",
            "subposition": "Medio",
            "overall": 77,
            "attributes": {"pase": 91},
        },
    )
    assert result["ok"] is True
    found, owner_id = find_player(state, player.id)
    assert found is player
    assert owner_id == state.club_id
    assert player.position_group == "Medio"
    assert player.subposition == "Medio"
    assert player.attributes["pase"] == 91
    assert state.event_flags["player_edits"][-1]["player_id"] == player.id


def test_press_has_journalist_media_and_six_topics():
    state = new_game("cd-terrassa", "Beta Test", seed=34)
    context = press_context(state)
    assert context["journalist"]
    assert context["outlet"]
    assert "media_confidence" in context
    questions = press_questions(state)
    assert len(questions) == 6
    assert {question["id"] for question in questions} >= {"partido", "vestuario", "objetivo"}
    before = state.user_team.media_confidence
    result = answer_press(state, "vestuario", 0)
    assert result["ok"] is True
    assert state.user_team.media_confidence >= before
    assert state.press_history[-1]["journalist"]


def test_api_calendar_brands_editor_and_press(client):
    _new_api(client, seed="35")
    calendar = client.get("/api/calendar").get_json()["data"]
    assert calendar["friendlies"]["dates"]
    assert calendar["friendlies"]["candidates"]
    opponent = calendar["friendlies"]["candidates"][0]["id"]
    day = calendar["friendlies"]["dates"][0]
    created = client.post("/api/friendlies", json={"opponent_id": opponent, "date": day, "home": True})
    assert created.status_code == 200, created.get_data(as_text=True)
    friendly_id = created.get_json()["data"]["result"]["friendly"]["id"]
    played = client.post(f"/api/friendlies/{friendly_id}/play", json={})
    assert played.status_code == 200, played.get_data(as_text=True)
    assert played.get_json()["data"]["result"]["report"]["phase"] == "friendly"

    brands = client.get("/api/brands").get_json()["data"]
    assert brands["brands"]["offers"]
    offer_id = brands["brands"]["offers"][0]["id"]
    signed = client.post(f"/api/brands/{offer_id}", json={"action": "accept"})
    assert signed.status_code == 200, signed.get_data(as_text=True)

    player_id = brands["team"]["players"][0]["id"]
    edited = client.post(
        f"/api/player/{player_id}/edit",
        json={"changes": {"position_group": "Medio", "subposition": "Medio", "overall": 76}},
    )
    assert edited.status_code == 200, edited.get_data(as_text=True)
    assert edited.get_json()["data"]["player"]["position_group"] == "Medio"

    press = client.get("/api/press").get_json()["data"]
    assert press["context"]["journalist"]
    assert len(press["questions"]) == 6
    answers = {question["id"]: 0 for question in press["questions"]}
    response = client.post("/api/press", json={"answers": answers})
    assert response.status_code == 200
    assert response.get_json()["data"]["state"]["press"]["done"] is True
