from urllib.parse import quote

import pytest
from src.cup import cup_round_fixtures
from src.season import play_round


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
    r = client.post("/new", data={"club_id": club, "manager": "WebTest", "seed": seed}, follow_redirects=True)
    assert r.status_code == 200
    return r


def test_web_new_and_main_routes(client):
    assert client.get("/", follow_redirects=True).status_code == 200
    assert client.get("/app").status_code == 200
    r = _new(client)
    assert "Dashboard".encode() in r.data
    for path in (
        "/dashboard",
        "/squad",
        "/tactics",
        "/training",
        "/market",
        "/staff",
        "/youth",
        "/press",
        "/cup",
        "/table",
        "/match",
    ):
        rr = client.get(path)
        assert rr.status_code == 200, path


def test_web_player_photo_and_cards(client):
    import web.app as web

    _new(client, seed="14")
    state = list(web.GAMES.values())[-1]
    player = next((p for p in state.user_team.players if p.photo), None)
    assert player is not None
    r = client.get("/photo/" + quote(player.photo))
    assert r.status_code == 200
    assert r.mimetype.startswith("image/")
    html = client.get("/squad").get_data(as_text=True)
    assert "avatar" in html
    assert "archetype" in html or "Central" in html


def test_web_training_and_quick_match(client):
    import web.app as web

    _new(client, seed="11")
    state = list(web.GAMES.values())[-1]
    line, _ = state.user_team.auto_lineup()
    r = client.post("/training", data={"action": "auto"}, follow_redirects=True)
    assert r.status_code == 200
    data = {
        "formation": "4-3-3",
        "mentality": "equilibrada",
        "press": "media",
        "block": "medio",
        "width": "normal",
        "tempo": "normal",
        "passing": "mixto",
        "pc_routine": "directa",
    }
    data.update({f"slot_{i}": p.id for i, p in enumerate(line)})
    r = client.post("/tactics", data=data, follow_redirects=True)
    assert r.status_code == 200
    assert len(state.manual_lineup) == 11
    r = client.post("/tactics", data={"formation": "4-4-2"}, follow_redirects=True)
    assert r.status_code == 200
    assert state.manual_lineup == []
    assert state.user_team.tactics.formation == "4-4-2"
    r = client.post("/match/quick", data={"travel": "equilibrado"}, follow_redirects=True)
    assert r.status_code == 200
    assert client.get("/match/report").status_code == 200


def test_web_crests_and_news(client):
    _new(client, seed="15")
    r = client.get("/new")
    assert r.status_code == 200
    assert b"crests/cd-terrassa.png" in r.data
    assert client.get("/static/crests/cd-terrassa.png").status_code == 200
    assert client.get("/static/crests/cd-terrassa.png").mimetype == "image/png"
    r = client.get("/news")
    assert r.status_code == 200
    assert "Actualidad".encode() in r.data
    assert "Noticias".encode() in r.data


def test_web_live_match(client):
    _new(client, seed="12")
    r = client.post("/match/live/start", data={"travel": "equilibrado"}, follow_redirects=True)
    assert r.status_code == 200
    assert client.get("/match/live").status_code == 200
    assert client.post("/match/live/advance", data={"mode": "quarter"}, follow_redirects=True).status_code == 200
    assert client.post("/match/live/advance", data={"mode": "rest"}, follow_redirects=True).status_code == 200
    r = client.post("/match/live/finish", follow_redirects=True)
    assert r.status_code == 200
    assert client.get("/match/report").status_code == 200


def test_web_daily_calendar_teams_and_chat(client):
    import web.app as web

    _new(client, seed="17")
    state = list(web.GAMES.values())[-1]
    assert state.date == "2026-08-01"
    r = client.post("/simulate", data={"mode": "day"}, follow_redirects=True)
    assert r.status_code == 200
    assert state.date != "2026-08-01"
    assert client.get("/news").status_code == 200
    team_html = client.get("/team/" + state.club_id).get_data(as_text=True)
    assert "Once probable" in team_html
    assert "avatar-table" in team_html
    assert "Cuerpo técnico" in team_html
    assert "Tú" in team_html
    rival = next(t for t in state.teams.values() if t.id != state.club_id)
    rival_html = client.get("/team/" + rival.id).get_data(as_text=True)
    assert "Cuerpo técnico" in rival_html
    assert "Entrenador" in rival_html
    state.date = "2026-10-01"
    market_html = client.get("/market").get_data(as_text=True)
    assert "Mercado cerrado" in market_html
    assert "jugadores encontrados" in market_html
    other = next(p for t in state.teams.values() if t.id != state.club_id for p in t.players)
    assert client.get("/player/" + other.id).status_code == 200
    assert client.post("/chat/new", follow_redirects=True).status_code == 200
    assert state.chat_messages
    message = state.chat_messages[-1]
    assert client.post("/chat/" + message["id"], data={"option": "0"}, follow_redirects=True).status_code == 200
    assert message["answered"]


def test_web_cup_calendar_and_ehl_page(client):
    import web.app as web

    _new(client, seed="18")
    state = list(web.GAMES.values())[-1]
    for _ in range(11):
        play_round(state, None, "equilibrado")
    state.club_id = cup_round_fixtures(state)[0].home_id
    preview = client.get("/match")
    assert preview.status_code == 200
    assert "Copa del Rey" in preview.get_data(as_text=True)
    quick = client.post("/match/quick", follow_redirects=True)
    assert quick.status_code == 200
    assert state.cup_round == 2
    assert client.get("/ehl").status_code == 200


def test_web_international_game_and_crest(client):
    r = _new(client, club="ned-amsterdam", seed="19")
    assert "Amsterdam" in r.get_data(as_text=True)
    assert client.get("/dashboard").status_code == 200
    assert client.get("/table").status_code == 200
    assert client.get("/team/ned-amsterdam").status_code == 200
    assert client.get("/crest/ned-amsterdam.svg").status_code == 200
    assert client.get("/crest/ned-amsterdam.svg").mimetype == "image/svg+xml"


def test_web_game_menu_options_and_exit(client):
    _new(client, seed="16")
    dashboard = client.get("/dashboard").get_data(as_text=True)
    assert 'id="game-menu"' in dashboard
    assert "Guardar partida" in dashboard
    assert client.get("/main-menu").status_code == 200
    assert client.get("/options").status_code == 200
    r = client.post("/options", data={"text_size": "large", "compact": "1", "confirm_exit": "1"}, follow_redirects=True)
    assert r.status_code == 200
    assert "Grande" in r.get_data(as_text=True)
    assert "text-large" in client.get("/dashboard").get_data(as_text=True)
    r = client.post("/exit-game", follow_redirects=True)
    assert r.status_code == 200
    assert "Hockey Manager".encode() in r.data


def test_web_save_and_load(client):
    _new(client, seed="13")
    r = client.post("/save", data={"name": "web-test-save"}, follow_redirects=True)
    assert r.status_code == 200
    r = client.get("/load")
    assert b"web-test-save" in r.data


def test_league_logo_assets_are_served(client):
    for code in ("es", "es-an", "es-pv", "es-md", "es-ga", "es-cn", "es-vc", "es-ct", "nl", "be", "de", "gb-eng", "ar", "in"):
        response = client.get(f"/static/league-logos/{code}.png")
        assert response.status_code == 200, code
        assert response.mimetype == "image/png"
