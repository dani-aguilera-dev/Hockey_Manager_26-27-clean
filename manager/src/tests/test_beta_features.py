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
    _new_api(client, seed="1")
    start = client.post("/api/match/live/start", json={"travel": "equilibrado"})
    assert start.status_code == 200, start.get_data(as_text=True)
    data = start.get_json()["data"]
    assert data["referrals"] == [1, 1]
    for _ in range(64):
        decision = data.get("last_decision")
        if decision and decision["side"] != data["user_side"]:
            break
        if data["snapshot"]["finished"]:
            break
        advance = client.post("/api/match/live/advance", json={"mode": "moment"})
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


def test_api_scouting_assignments(client):
    _new_api(client, seed="44")
    data = client.get("/api/scouting")
    assert data.status_code == 200, data.get_data(as_text=True)
    payload = data.get_json()["data"]
    assert payload["assignment_options"]["scouts"]
    options = payload["assignment_options"]
    created = client.post(
        "/api/scouting/assignments",
        json={
            "scout_id": options["scouts"][0]["id"],
            "competition": options["competitions"][0]["code"],
            "position": "Delantero",
            "max_age": "24",
            "focus": "joven",
        },
    )
    assert created.status_code == 200, created.get_data(as_text=True)
    created_payload = created.get_json()["data"]
    assert created_payload["scouting"]["assignments"]
    assignment_id = created_payload["scouting"]["assignments"][0]["id"]
    deleted = client.delete(f"/api/scouting/assignments/{assignment_id}")
    assert deleted.status_code == 200, deleted.get_data(as_text=True)
    assert deleted.get_json()["data"]["scouting"]["assignments"] == []


def test_api_team_meeting(client):
    _new_api(client, seed="45")
    context = client.get("/api/team-meeting")
    assert context.status_code == 200, context.get_data(as_text=True)
    data = context.get_json()["data"]
    assert data["meeting_types"]
    assert data["tones"]
    assert data["players"]
    player = data["players"][0]
    response = client.post(
        "/api/team-meeting",
        json={
            "meeting_type": data["recommended_type"],
            "tone": "serena",
            "topics": ["objetivo", "vestuario"],
            "promise_player_id": player["id"],
            "promise_type": "minutes",
        },
    )
    assert response.status_code == 200, response.get_data(as_text=True)
    payload = response.get_json()["data"]
    assert payload["result"]["ok"] is True
    assert payload["meeting"]["history"]
    assert payload["state"]["team"]["name"]


def test_api_finance_overview_and_ticket(client):
    _new_api(client, seed="46")
    response = client.get("/api/finance")
    assert response.status_code == 200, response.get_data(as_text=True)
    data = response.get_json()["data"]
    assert data["cash"] >= 0
    assert data["ticket_scenarios"]
    assert data["top_earners"]
    ticket = client.post("/api/finance/ticket", json={"price": 22})
    assert ticket.status_code == 200, ticket.get_data(as_text=True)
    payload = ticket.get_json()["data"]
    assert payload["finance"]["ticket_price"] == 22
    assert any(row["price"] == 22 for row in payload["finance"]["ticket_scenarios"])


def test_api_analysis_overview_and_archive(client):
    _new_api(client, seed="47")
    quick = client.post("/api/match/quick", json={"travel": "equilibrado"})
    assert quick.status_code == 200, quick.get_data(as_text=True)
    response = client.get("/api/analysis")
    assert response.status_code == 200, response.get_data(as_text=True)
    data = response.get_json()["data"]
    assert data["match"]
    assert data["metrics"]["home"]["shots"] >= 0
    assert data["timeline"]
    assert data["players"]
    fixture_id = data["match"]["fixture_id"]
    archived = client.get(f"/api/analysis?fixture_id={fixture_id}")
    assert archived.status_code == 200, archived.get_data(as_text=True)
    assert archived.get_json()["data"]["match"]["fixture_id"] == fixture_id


def test_api_report_has_added_time_and_discipline_stats(client):
    _new_api(client, seed="48")
    quick = client.post("/api/match/quick", json={"travel": "equilibrado"})
    assert quick.status_code == 200, quick.get_data(as_text=True)
    report = client.get("/api/match/report").get_json()["data"]["report"]
    assert "added_time" in report
    assert set(report["added_time"]) >= {"1", "2", "3", "4"}
    assert "dissent" in report["home_stats"]
    assert "unsportsmanlike" in report["away_stats"]
    for key in ("advantage_failed", "dangerous_sanction", "free_hit_10m", "pc_retake", "stroke_retake"):
        assert key in report["home_stats"]
        assert key in report["away_stats"]


def test_api_live_protest_once_per_match(client):
    _new_api(client, seed="49")
    start = client.post("/api/match/live/start", json={"travel": "equilibrado"})
    assert start.status_code == 200, start.get_data(as_text=True)
    assert start.get_json()["data"]["protest_available"] is True
    protest = client.post("/api/match/live/protest", json={"tone": "respetuosa"})
    assert protest.status_code == 200, protest.get_data(as_text=True)
    payload = protest.get_json()["data"]
    assert payload["protest_available"] is False
    assert payload["protest_used"][payload["user_side"]] is True
    second = client.post("/api/match/live/protest", json={"tone": "respetuosa"})
    assert second.status_code == 409


def test_api_responsibilities_assignment(client):
    _new_api(client, seed="50")
    data = client.get("/api/responsibilities")
    assert data.status_code == 200, data.get_data(as_text=True)
    payload = data.get_json()["data"]
    assert payload["areas"]
    staff = payload["staff"][0]
    response = client.post("/api/responsibilities", json={"area": "attack", "staff_name": staff["name"]})
    assert response.status_code == 200, response.get_data(as_text=True)
    result = response.get_json()["data"]
    assert result["responsibilities"]["areas"][1]["staff_name"] == staff["name"]
    assert result["state"]["team"]["name"]


def test_api_development_plan(client):
    _new_api(client, seed="51")
    data = client.get("/api/development")
    assert data.status_code == 200, data.get_data(as_text=True)
    payload = data.get_json()["data"]
    player = payload["players"][0]
    response = client.post(
        f"/api/development/{player['player_id']}",
        json={"focus": "tecnica", "intensity": "normal", "notes": "mejorar pase"},
    )
    assert response.status_code == 200, response.get_data(as_text=True)
    result = response.get_json()["data"]
    assert result["development"]["active"] == 1
    assert result["development"]["players"][0]["focus"] == "tecnica"
    cleared = client.delete(f"/api/development/{player['player_id']}")
    assert cleared.status_code == 200, cleared.get_data(as_text=True)
    assert cleared.get_json()["data"]["development"]["active"] == 0


def test_api_awards_overview(client):
    _new_api(client, seed="52")
    quick = client.post("/api/match/quick", json={"travel": "equilibrado"})
    assert quick.status_code == 200, quick.get_data(as_text=True)
    response = client.get("/api/awards")
    assert response.status_code == 200, response.get_data(as_text=True)
    data = response.get_json()["data"]
    assert data["awards"]
    assert len(data["best_xi"]) == 11
    assert data["last_match"]


def test_api_contracts_overview(client):
    _new_api(client, seed="53")
    response = client.get("/api/contracts")
    assert response.status_code == 200, response.get_data(as_text=True)
    data = response.get_json()["data"]
    assert data["players"]
    assert data["summary"]["players"] == len(data["players"])
    assert data["renewal_candidates"]


def test_api_facilities_overview_and_upgrade(client):
    _new_api(client, seed="54")
    response = client.get("/api/facilities")
    assert response.status_code == 200, response.get_data(as_text=True)
    data = response.get_json()["data"]
    assert data["facilities"]
    assert data["upgrades"]
    request_id = data["upgrades"][0]["id"]
    upgrade = client.post("/api/facilities/upgrade", json={"request_id": request_id})
    assert upgrade.status_code == 200, upgrade.get_data(as_text=True)
    payload = upgrade.get_json()["data"]
    assert payload["facilities"]["history"]
    assert payload["state"]["team"]["name"]


def test_api_clauses_update(client):
    _new_api(client, seed="55")
    data = client.get("/api/clauses")
    assert data.status_code == 200, data.get_data(as_text=True)
    payload = data.get_json()["data"]
    player = payload["players"][0]
    response = client.post(
        f"/api/clauses/{player['id']}",
        json={"release_clause": 1_000_000, "renewal_bonus": 50_000},
    )
    assert response.status_code == 200, response.get_data(as_text=True)
    result = response.get_json()["data"]
    assert result["clauses"]["summary"]["protected"] == 1
    assert result["state"]["team"]["name"]


def test_api_shortlist_add_update_remove(client):
    _new_api(client, seed="56")
    overview = client.get("/api/shortlist")
    assert overview.status_code == 200, overview.get_data(as_text=True)
    assert overview.get_json()["data"]["entries"] == []
    candidates = client.get("/api/shortlist/candidates")
    assert candidates.status_code == 200, candidates.get_data(as_text=True)
    candidate = candidates.get_json()["data"]["candidates"][0]
    added = client.post(
        "/api/shortlist",
        json={"player_id": candidate["id"], "priority": "alta", "note": "Objetivo prioritario"},
    )
    assert added.status_code == 200, added.get_data(as_text=True)
    payload = added.get_json()["data"]
    assert payload["shortlist"]["summary"]["total"] == 1
    assert payload["shortlist"]["entries"][0]["priority"] == "alta"
    detail = client.get(f"/api/player/{candidate['id']}")
    assert detail.status_code == 200, detail.get_data(as_text=True)
    assert detail.get_json()["data"]["shortlisted"] is True
    updated = client.post(
        f"/api/shortlist/{candidate['id']}",
        json={"priority": "baja", "note": "Esperar"},
    )
    assert updated.status_code == 200, updated.get_data(as_text=True)
    assert updated.get_json()["data"]["shortlist"]["entries"][0]["note"] == "Esperar"
    removed = client.delete(f"/api/shortlist/{candidate['id']}")
    assert removed.status_code == 200, removed.get_data(as_text=True)
    assert removed.get_json()["data"]["shortlist"]["entries"] == []


def test_api_match_plans_create_update_delete(client):
    _new_api(client, seed="57")
    overview = client.get("/api/match-plans")
    assert overview.status_code == 200, overview.get_data(as_text=True)
    data = overview.get_json()["data"]
    assert data["plans"] == []
    assert data["fields"]
    created = client.post(
        "/api/match-plans",
        json={
            "name": "Cerrar el partido",
            "situation": "leading",
            "from_minute": 45,
            "instructions": {"mentality": "defensiva", "press": "baja"},
            "enabled": True,
        },
    )
    assert created.status_code == 200, created.get_data(as_text=True)
    payload = created.get_json()["data"]
    plan = payload["match_plans"]["plans"][0]
    assert plan["name"] == "Cerrar el partido"
    assert plan["enabled"] is True
    updated = client.post(
        f"/api/match-plans/{plan['id']}",
        json={
            "name": plan["name"],
            "situation": "leading",
            "from_minute": 50,
            "instructions": {"mentality": "muy_defensiva"},
            "enabled": False,
        },
    )
    assert updated.status_code == 200, updated.get_data(as_text=True)
    assert updated.get_json()["data"]["match_plans"]["plans"][0]["enabled"] is False
    deleted = client.delete(f"/api/match-plans/{plan['id']}")
    assert deleted.status_code == 200, deleted.get_data(as_text=True)
    assert deleted.get_json()["data"]["match_plans"]["plans"] == []


def test_api_manager_profile_and_career_record(client):
    _new_api(client, seed="58")
    profile = client.get("/api/manager")
    assert profile.status_code == 200, profile.get_data(as_text=True)
    data = profile.get_json()["data"]
    assert data["manager"]["name"]
    assert data["current"]["position"] >= 1
    assert data["record"]["matches"] == 0
    assert data["milestones"]
    quick = client.post("/api/match/quick", json={"travel": "equilibrado"})
    assert quick.status_code == 200, quick.get_data(as_text=True)
    refreshed = client.get("/api/manager").get_json()["data"]
    record = refreshed["record"]
    assert record["matches"] >= 1
    assert record["wins"] + record["draws"] + record["losses"] == record["matches"]
    assert refreshed["recent"]


def test_api_compare_players(client):
    _new_api(client, seed="59")
    candidates = client.get("/api/compare/players")
    assert candidates.status_code == 200, candidates.get_data(as_text=True)
    players = candidates.get_json()["data"]["players"]
    assert len(players) >= 2
    response = client.get(
        f"/api/compare?player_a={players[0]['id']}&player_b={players[1]['id']}"
    )
    assert response.status_code == 200, response.get_data(as_text=True)
    data = response.get_json()["data"]
    assert data["a"]["id"] != data["b"]["id"]
    assert data["attributes"]
    assert data["summary"]["attributes"] == len(data["attributes"])
    same = client.get(f"/api/compare?player_a={players[0]['id']}&player_b={players[0]['id']}")
    assert same.status_code == 409


def test_api_jobs_generate_accept_and_reject(client):
    _new_api(client, seed="60")
    jobs = client.get("/api/jobs")
    assert jobs.status_code == 200, jobs.get_data(as_text=True)
    initial = jobs.get_json()["data"]
    assert initial["club"]["name"]
    assert initial["contract"]["club_id"] == initial["club"]["id"]
    generated = client.post("/api/jobs/offers", json={"force": True})
    assert generated.status_code == 200, generated.get_data(as_text=True)
    offers = generated.get_json()["data"]["jobs"]["offers"]
    assert offers
    rejected = client.post(f"/api/jobs/offers/{offers[-1]['id']}/reject")
    assert rejected.status_code == 200, rejected.get_data(as_text=True)
    accepted = client.post(f"/api/jobs/offers/{offers[0]['id']}/accept")
    assert accepted.status_code == 200, accepted.get_data(as_text=True)
    payload = accepted.get_json()["data"]
    assert payload["state"]["team"]["name"] == offers[0]["club_name"]
    assert payload["jobs"]["club"]["name"] == offers[0]["club_name"]
    assert payload["jobs"]["contract"]["club_id"] == offers[0]["club_id"]
    assert payload["jobs"]["history"]


def test_api_trials_invite_and_end(client):
    _new_api(client, seed="61")
    data = client.get("/api/trials")
    assert data.status_code == 200, data.get_data(as_text=True)
    payload = data.get_json()["data"]
    assert payload["candidates"]
    candidate = payload["candidates"][0]
    invited = client.post("/api/trials", json={"player_id": candidate["id"], "days": 14})
    assert invited.status_code == 200, invited.get_data(as_text=True)
    invited_payload = invited.get_json()["data"]
    assert invited_payload["trials"]["active"]
    trial_id = invited_payload["trials"]["active"][0]["trial_id"]
    ended = client.post(f"/api/trials/{trial_id}/end")
    assert ended.status_code == 200, ended.get_data(as_text=True)
    ended_payload = ended.get_json()["data"]
    assert ended_payload["trials"]["active"] == []
    assert ended_payload["trials"]["history"]
    assert ended_payload["trials"]["history"][0]["report"]["summary"]


def test_api_cross_league_job_pending(client):
    _new_api(client, seed="62")
    generated = client.post("/api/jobs/offers", json={"force": True, "cross_league": True})
    assert generated.status_code == 200, generated.get_data(as_text=True)
    offers = generated.get_json()["data"]["jobs"]["offers"]
    cross = [offer for offer in offers if offer["cross_league"]]
    assert cross, offers
    accepted = client.post(f"/api/jobs/offers/{cross[0]['id']}/accept")
    assert accepted.status_code == 200, accepted.get_data(as_text=True)
    payload = accepted.get_json()["data"]
    assert payload["result"]["pending"] is True
    assert payload["jobs"]["pending_job"]["club_id"] == cross[0]["club_id"]
    assert payload["jobs"]["pending_job"]["effective_season"]
    assert payload["state"]["team"]["name"] != cross[0]["club_name"]
