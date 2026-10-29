import pytest

from src.brands import (
    accept_brand_offer,
    accept_player_brand_offer,
    brand_summary,
    load_brands,
)
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


def test_player_brand_contract_is_individual():
    state = new_game("cd-terrassa", "Beta Test", seed=36)
    summary = brand_summary(state)
    assert summary["player_offers"]
    offer = summary["player_offers"][0]
    player = next(item for item in state.user_team.players if item.id == offer["player_id"])
    result = accept_player_brand_offer(state, offer["id"])
    assert result["ok"] is True
    assert player.brand_deal["brand"] == offer["brand"]
    assert summary["player_offers"][0]["player_name"] == player.name


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
    assert brands["brands"]["player_offers"]
    player_offer_id = brands["brands"]["player_offers"][0]["id"]
    player_signed = client.post(f"/api/brands/players/{player_offer_id}", json={"action": "accept"})
    assert player_signed.status_code == 200, player_signed.get_data(as_text=True)
    assert player_signed.get_json()["data"]["state"]["team"]["players"]

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

    # Flujo E2E de partido y rueda posterior.
    quick = client.post("/api/match/quick", json={"travel": "equilibrado"})
    assert quick.status_code == 200, quick.get_data(as_text=True)
    assert quick.get_json()["data"]["report"]["referee"]["name"]
    post = client.get("/api/press/post").get_json()["data"]
    assert post["available"] is True
    assert len(post["questions"]) == 4
    post_answers = {question["id"]: 0 for question in post["questions"]}
    post_response = client.post("/api/press/post", json={"answers": post_answers})
    assert post_response.status_code == 200, post_response.get_data(as_text=True)
    assert post_response.get_json()["data"]["state"]["press"]["post_done"] is True

    live_start = client.post("/api/match/live/start", json={"travel": "equilibrado"})
    assert live_start.status_code == 200, live_start.get_data(as_text=True)
    live = live_start.get_json()["data"]
    assert live["line"] and live["bench"]
    out_id = live["line"][0]["id"]
    in_id = live["bench"][0]["id"]
    sub = client.post("/api/match/live/sub", json={"out_id": out_id, "in_id": in_id})
    assert sub.status_code == 200, sub.get_data(as_text=True)
    assert sub.get_json()["data"]["events"]


def test_api_video_review_flow(client):
    _new_api(client, seed="38")
    start = client.post("/api/match/live/start", json={"travel": "equilibrado"})
    assert start.status_code == 200, start.get_data(as_text=True)
    data = start.get_json()["data"]
    assert data["referrals"] == [1, 1]
    for _ in range(4):
        decision = data.get("last_decision")
        if decision and decision["side"] != data["user_side"]:
            break
        advance = client.post("/api/match/live/advance", json={"mode": "quarter"})
        assert advance.status_code == 200, advance.get_data(as_text=True)
        data = advance.get_json()["data"]
    decision = data.get("last_decision")
    assert decision, "El partido debe generar alguna decisión revisable"
    assert decision["side"] != data["user_side"], decision
    review = client.post("/api/match/live/review", json={"decision": decision["type"]})
    assert review.status_code == 200, review.get_data(as_text=True)
    payload = review.get_json()["data"]
    assert payload["reviews"], payload
    assert payload["last_decision"]["reviewed"] is True
    assert payload["reviews"][-1]["type"] == decision["type"]
    assert payload["referrals"][payload["user_side"]] in (0, 1)


def test_api_board_overview_and_request(client):
    _new_api(client, seed="39")
    board = client.get("/api/board")
    assert board.status_code == 200, board.get_data(as_text=True)
    data = board.get_json()["data"]
    assert data["confidence"] >= 0
    assert len(data["requests"]) == 7
    assert len(data["facilities"]) == 6
    request = client.post("/api/board/request", json={"request_id": "training"})
    assert request.status_code == 200, request.get_data(as_text=True)
    payload = request.get_json()["data"]
    assert payload["result"]["ok"] is True
    assert payload["board"]["history"]
    assert payload["board"]["history"][0]["request_id"] == "training"
    assert payload["state"]["team"]["name"]


def test_api_loans_in_and_active_list(client):
    _new_api(client, seed="40")
    loans = client.get("/api/loans")
    assert loans.status_code == 200, loans.get_data(as_text=True)
    data = loans.get_json()["data"]
    assert data["targets"] and data["outgoing"]
    accepted = None
    for target in data["targets"][:10]:
        response = client.post(
            "/api/loans/in",
            json={"player_id": target["id"], "wage_share": 100, "playing_time": "titular"},
        )
        assert response.status_code == 200, response.get_data(as_text=True)
        payload = response.get_json()["data"]
        if payload["result"]["accepted"]:
            accepted = payload
            break
    assert accepted is not None, "Al menos una cesión debe aceptarse en la ventana de prueba"
    assert accepted["loans"]["active"]
    assert accepted["loans"]["active"][0]["is_incoming"] is True
    assert accepted["loans"]["history"]


def test_api_datahub_and_opposition_instructions(client):
    _new_api(client, seed="41")
    datahub = client.get("/api/datahub")
    assert datahub.status_code == 200, datahub.get_data(as_text=True)
    data = datahub.get_json()["data"]
    assert data["fixture"]
    assert data["key_players"]
    opponent_id = data["opponent"]["id"]
    player_id = data["key_players"][0]["id"]
    response = client.post(
        "/api/datahub/instructions",
        json={"opponent_id": opponent_id, "instructions": {player_id: "tight_marking"}},
    )
    assert response.status_code == 200, response.get_data(as_text=True)
    payload = response.get_json()["data"]
    assert payload["datahub"]["instructions"][player_id] == "tight_marking"
    assert payload["state"]["team"]["name"]
    refreshed = client.get("/api/datahub").get_json()["data"]
    assert refreshed["instructions"][player_id] == "tight_marking"


def test_api_affiliates_and_mentoring(client):
    _new_api(client, seed="42")
    response = client.get("/api/affiliates")
    assert response.status_code == 200, response.get_data(as_text=True)
    data = response.get_json()["data"]
    assert data["affiliates"]["candidates"]
    assert data["mentoring"]["mentors"]
    assert data["mentoring"]["mentees"]
    candidate = data["affiliates"]["candidates"][0]
    affiliate = client.post("/api/affiliates/request", json={"club_id": candidate["id"]})
    assert affiliate.status_code == 200, affiliate.get_data(as_text=True)
    assert affiliate.get_json()["data"]["affiliates"]["history"]
    mentor = data["mentoring"]["mentors"][0]
    mentee = data["mentoring"]["mentees"][0]
    created = client.post(
        "/api/mentoring",
        json={"mentor_id": mentor["id"], "mentee_id": mentee["id"], "focus": "tecnica"},
    )
    assert created.status_code == 200, created.get_data(as_text=True)
    payload = created.get_json()["data"]
    assert payload["mentoring"]["pairs"]
    pair_id = payload["mentoring"]["pairs"][0]["id"]
    deleted = client.delete(f"/api/mentoring/{pair_id}")
    assert deleted.status_code == 200, deleted.get_data(as_text=True)
    assert deleted.get_json()["data"]["mentoring"]["pairs"] == []


def test_api_history_and_filters(client):
    _new_api(client, seed="43")
    quick = client.post("/api/match/quick", json={"travel": "equilibrado"})
    assert quick.status_code == 200, quick.get_data(as_text=True)
    history = client.get("/api/history")
    assert history.status_code == 200, history.get_data(as_text=True)
    data = history.get_json()["data"]
    assert data["matches"]
    assert data["players"]
    assert data["summary"]["matches"] > 0
    assert data["options"]["seasons"]
    team_id = data["matches"][0]["home_id"]
    filtered = client.get(f"/api/history?team_id={team_id}").get_json()["data"]
    assert filtered["matches"]
    assert all(team_id in (row["home_id"], row["away_id"]) for row in filtered["matches"])
