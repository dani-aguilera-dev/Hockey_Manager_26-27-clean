import pytest


@pytest.fixture()
def client(tmp_path):
    import web.app as web

    web.WEB_DB = tmp_path / "web.db"
    web.GAMES.clear()
    web.LIVE.clear()
    web.app.config.update(TESTING=True)
    with web.app.test_client() as c:
        yield c


def _new(client, club="cd-terrassa", seed="10"):
    response = client.post("/api/new-game", json={"club_id": club, "manager": "API Test", "seed": seed})
    assert response.status_code == 200, response.get_data(as_text=True)
    payload = response.get_json()
    assert payload["ok"] is True
    return payload["data"]


def test_api_new_game_state_and_sections(client):
    state = _new(client)
    assert state["team"]["name"]
    assert len(state["table"]) == 12
    assert state["game"]["save_name"]
    for path in ("/api/state", "/api/squad", "/api/tactics", "/api/training", "/api/medical", "/api/events", "/api/market", "/api/staff", "/api/youth", "/api/press", "/api/table", "/api/chat", "/api/news"):
        response = client.get(path)
        assert response.status_code == 200, path
        assert response.get_json()["ok"] is True


def test_api_tactics_training_and_market(client):
    _new(client)
    tactics = client.get("/api/tactics").get_json()["data"]
    assert len(tactics["slot_rows"]) >= 3
    formation = "4-4-2" if tactics["tactics"]["formation"] != "4-4-2" else "4-3-3"
    response = client.post("/api/tactics", json={"formation": formation})
    assert response.status_code == 200
    assert response.get_json()["data"]["tactics"]["formation"] == formation

    response = client.post("/api/training", json={"action": "auto"})
    assert response.status_code == 200
    assert response.get_json()["data"]["trained"] is True

    market = client.get("/api/market").get_json()["data"]
    assert market["total"] > 0
    assert market["players"]


def test_api_live_match_and_report(client):
    _new(client, seed="12")
    started = client.post("/api/match/live/start", json={"travel": "equilibrado"})
    assert started.status_code == 200, started.get_data(as_text=True)
    live = started.get_json()["data"]
    assert live["fixture"]
    assert client.get("/api/match/live").status_code == 200
    assert client.post("/api/match/live/advance", json={"mode": "quarter"}).status_code == 200
    assert client.post("/api/match/live/advance", json={"mode": "rest"}).status_code == 200
    finished = client.post("/api/match/live/finish")
    assert finished.status_code == 200
    assert finished.get_json()["data"]["report"]["result"] in ("Victoria", "Empate", "Derrota")
    report = client.get("/api/match/report")
    assert report.status_code == 200
    report_data = report.get_json()["data"]["report"]
    assert "injuries" in report_data
    assert "cards" in report_data


def test_api_chat_and_press(client):
    _new(client, seed="17")
    chat = client.get("/api/chat").get_json()["data"]
    assert "messages" in chat
    assert chat["targets"]["players"]
    assert chat["targets"]["staff"]
    target = chat["targets"]["players"][0]
    topics = client.get(f"/api/chat/topics?target_type=player&target_id={target['target_id']}").get_json()["data"]
    assert topics["topics"]
    started = client.post(
        "/api/chat/start",
        json={"target_type": "player", "target_id": target["target_id"], "topic": topics["topics"][0]["id"]},
    )
    assert started.status_code == 200
    message = started.get_json()["data"]["message"]
    assert message["context"]
    first = client.post(f"/api/chat/{message['id']}", json={"option": 0})
    assert first.status_code == 200
    first_message = next(item for item in first.get_json()["data"]["messages"] if item["id"] == message["id"])
    assert first_message["answered"] is False
    assert first_message["turns"]
    answered = client.post(f"/api/chat/{message['id']}", json={"option": 0})
    assert answered.status_code == 200
    final_message = next(item for item in answered.get_json()["data"]["messages"] if item["id"] == message["id"])
    assert final_message["answered"] is True

    staff = chat["targets"]["staff"][0]
    staff_topics = client.get(f"/api/chat/topics?target_type=staff&target_id={staff['target_id']}").get_json()["data"]
    assert staff_topics["topics"]
    staff_started = client.post(
        "/api/chat/start",
        json={"target_type": "staff", "target_id": staff["target_id"], "topic": staff_topics["topics"][0]["id"]},
    )
    assert staff_started.status_code == 200

    opened = client.post("/api/chat/new")
    assert opened.status_code == 200
    messages = opened.get_json()["data"]["messages"]
    assert messages

    press = client.get("/api/press").get_json()["data"]
    assert press["questions"]
    answers = {question["id"]: 0 for question in press["questions"]}
    response = client.post("/api/press", json={"answers": answers})
    assert response.status_code == 200
    assert response.get_json()["data"]["state"]["press"]["done"] is True


def test_api_news_has_awards_and_related_data(client):
    _new(client, seed="18")
    client.post("/api/match/quick", json={"travel": "equilibrado"})
    news = client.get("/api/news").get_json()["data"]
    assert news["awards"]
    assert news["news"]
    match_item = next(item for item in news["news"] if item["category"] == "Partido")
    assert match_item["awards"]
    assert match_item["related_players"]
    assert match_item["related_teams"]
    assert match_item["crest"].startswith("/")


def test_api_pending_event_can_be_resolved(client):
    from datetime import date

    from src.events import trigger_event

    import web.app as web

    _new(client, seed="21")
    state = list(web.GAMES.values())[-1]
    for player in state.user_team.players:
        player.fatigue = 80
    event = trigger_event(state, date.fromisoformat(state.date), event_id="medical_hamstring_warning")
    assert event is not None

    listed = client.get("/api/events")
    assert listed.status_code == 200
    assert listed.get_json()["data"]["pending"][0]["event_id"] == "medical_hamstring_warning"

    resolved = client.post(f"/api/events/{event['id']}", json={"choice": "rest"})
    assert resolved.status_code == 200, resolved.get_data(as_text=True)
    payload = resolved.get_json()["data"]
    assert payload["result"]["ok"] is True
    assert payload["state"]["decisions"] == []
    assert payload["state"]["event_history"]


def test_api_medical_center_payload(client):
    import web.app as web

    _new(client, seed="22")
    state = list(web.GAMES.values())[-1]
    player = state.user_team.players[0]
    player.injury = 3
    player.injury_type = "muscular"
    player.injury_severity = "moderada"
    player.injury_expected = 3
    player.injury_history.append(
        {"date": state.date, "type": "muscular", "severity": "moderada", "matches": 3, "source": "test"}
    )
    response = client.get("/api/medical")
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["summary"]["injured"] == 1
    assert data["injuries"][0]["id"] == player.id
    assert data["history"][0]["kind"] == "injury"


def test_api_simulation_stops_when_a_decision_appears(client):
    import web.app as web

    _new(client, seed="23")
    state = list(web.GAMES.values())[-1]
    for player in state.user_team.players:
        player.fatigue = 80
    response = client.post("/api/simulate", json={"mode": "date", "target_date": "2026-09-01"})
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["simulation"]["stopped_at_decision"] is True
    assert data["decisions"]


def test_api_transfer_negotiation_flow(client):
    import web.app as web
    from src.market import market_players

    _new(client, seed="24")
    state = list(web.GAMES.values())[-1]
    state.user_team.transfer_budget = 3_000_000
    state.user_team.budget = 3_000_000
    player = min(market_players(state, limit=20, max_value=1_000_000), key=lambda item: item.value)
    started = client.post(
        f"/api/market/negotiate/{player.id}",
        json={"fee": 50_000, "salary": player.salary * 2, "years": 3},
    )
    assert started.status_code == 200, started.get_data(as_text=True)
    negotiation = started.get_json()["data"]["negotiation"]
    assert negotiation["status"] == "open"
    accepted = client.post(
        f"/api/market/negotiations/{negotiation['id']}",
        json={"action": "accept"},
    )
    assert accepted.status_code == 200, accepted.get_data(as_text=True)
    assert accepted.get_json()["data"]["negotiation"]["status"] == "accepted"


def test_api_market_has_lower_division_free_agents(client):
    _new(client, seed="25")
    market = client.get("/api/market?free_agents=1").get_json()["data"]
    assert market["free_agent_total"] >= 200
    assert market["free_agents"]
    assert {player["league"] for player in market["free_agents"]} & {"1A", "1N", "1M", "1G", "1C"}
    filtered = client.get("/api/market?free_agents=1&league=1N").get_json()["data"]
    assert filtered["free_agents"]
    assert all(player["league"] == "1N" for player in filtered["free_agents"])


def test_api_catalog_includes_regional_leagues(client):
    response = client.get("/api/new-game")
    assert response.status_code == 200
    data = response.get_json()["data"]
    codes = {group["competition"]["code"] for group in data["leagues"]}
    assert {"1N", "1A", "1G", "1M", "1C"} <= codes
    assert any(club["id"] == "reg-codema" for club in data["clubs"])


def test_api_save_manager_rename_and_delete(client):
    _new(client, seed="22")
    saves = client.get("/api/load").get_json()["data"]["saves"]
    assert saves
    original = saves[0]["name"]
    renamed = original + " (renombrada)"
    response = client.patch("/api/saves", json={"name": original, "new_name": renamed})
    assert response.status_code == 200, response.get_data(as_text=True)
    names = {row["name"] for row in response.get_json()["data"]["saves"]}
    assert renamed in names and original not in names

    duplicate = client.patch("/api/saves", json={"name": renamed, "new_name": renamed})
    assert duplicate.status_code == 200

    response = client.delete("/api/saves", json={"name": renamed})
    assert response.status_code == 200, response.get_data(as_text=True)
    names = {row["name"] for row in response.get_json()["data"]["saves"]}
    assert renamed not in names


def test_promotion_payload_has_groups_teams_and_qualified():
    import web.app as web
    from src.season import _create_promotion_groups, new_game, play_round
    from web.api import _promotion_payload

    state = new_game("reg-codema", "Promotion API", seed=1214)
    for _ in range(state.total_rounds):
        play_round(state, None, "equilibrado")
    group = state.promotion["groups"][0]
    state.club_id = group["team_ids"][0]
    state.promotion = {}
    state.promotion_round = 0
    _create_promotion_groups(state)
    with web.app.test_request_context("/"):
        payload = _promotion_payload(state)
    assert len(payload["groups"]) == 4
    assert payload["groups"][0]["teams"]
    assert payload["qualified"]
    assert payload["user_qualified"] is True
    assert payload["user_group"]
    assert len(payload["path"]["objectives"]) == 3
    assert payload["path"]["objectives"][0]["status"] == "completed"
    assert payload["path"]["objectives"][0]["state_text"]
    assert payload["path"]["objectives"][1]["status"] == "active"
    assert payload["path"]["leagues"]


def test_dhb_objectives_have_dhb_identity():
    from src.objectives import competition_objectives
    from src.season import new_game

    state = new_game("aticos-san-fernando", "DHB Objectives", seed=1215)
    data = competition_objectives(state)
    assert data["system"] == "dhb_two_phase"
    assert [objective["key"] for objective in data["objectives"]] == ["group", "final4", "promotion"]
    assert all("regional" not in objective["title"].lower() for objective in data["objectives"])
    assert all(objective["state_text"] for objective in data["objectives"])
