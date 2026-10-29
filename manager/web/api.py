"""JSON API for the React web client.

The game rules stay in ``manager/src``.  This module only exposes the existing
GameState/MatchEngine operations in a stable, serialisable shape.
"""

from __future__ import annotations

import random
import uuid
from datetime import date, timedelta

from flask import Blueprint, jsonify, request, session

from src.calendar import league_table
from src.commercial import (
    accept_sponsor_offer,
    commercial_summary,
    generate_sponsor_offers,
    reject_sponsor_offer,
    run_campaign,
    set_ticket_price,
)
from src.competitions import COMPETITIONS, competition, playable_competitions
from src.conversations import (
    apply_conversation_choice,
    conversation_targets,
    create_conversation,
    random_conversation,
    target_summary,
    topics_for_target,
)
from src.cup import cup_next_user_fixture, cup_round_fixtures, cup_status_text
from src.daily import add_player_chat, next_match_date, simulate_days
from src.events import event_history as game_event_history
from src.events import pending_events as pending_game_events
from src.events import resolve_event as resolve_game_event
from src.data_loader import load_clubs
from src.ehl import ehl_next_date, ehl_status_text, simulate_ehl_round
from src.finance import finance_overview, financial_summary
from src.friendlies import (
    cancel_friendly,
    friendlies_payload,
    play_friendly,
    schedule_friendly,
)
from src.brands import (
    accept_brand_offer,
    accept_player_brand_offer,
    brand_summary,
    reject_brand_offer,
    reject_player_brand_offer,
)
from src.board import board_overview, request_board
from src.loans import loan_overview, offer_loan_out, request_loan_in
from src.datahub import datahub_overview, set_instructions
from src.history import history_overview
from src.analysis import analysis_overview
from src.affiliates import (
    affiliate_overview,
    assign_mentor,
    end_affiliate,
    end_mentoring,
    mentoring_overview,
    request_affiliate,
)
from src.player_editor import edit_player, editor_payload, find_player
from src.international import club_catalog, international_cities, load_all_teams
from src.logistics import travel_options
from src.market import (
    STAFF_LABELS,
    accept_incoming_offer,
    asking_price,
    fire_staff,
    generate_incoming_offers,
    hire_market_staff,
    hire_staff,
    list_player_for_transfer,
    make_transfer_offer,
    market_players,
    market_window,
    market_window_text,
    reject_incoming_offer,
    renew_contract,
    scout_range,
    staff_candidates,
    staff_market,
)
from src.negotiation import (
    counter_incoming_offer,
    respond_negotiation,
    start_renewal_negotiation,
    start_transfer_negotiation,
)
from src.models import FORMATION_SLOTS
from src.news import awards_for_last_match, news_feed
from src.persistence import delete_save as delete_saved_game, list_saves, load_game, rename_save as rename_saved_game
from src.press import (
    answer_post_press,
    answer_press,
    mark_press_done,
    post_press_available,
    post_press_context,
    post_press_questions,
    press_context,
    press_questions,
)
from src.objectives import competition_objectives
from src.promotion import promotion_path
from src.ratings import league_label, profile, scout_stars, stars_bar, stars_text, tier
from src.scouting import cancel_assignment, create_assignment, scouting_overview
from src.team_meeting import perform_team_meeting, team_meeting_context
from src.season import (
    advance_to_next_season,
    finish_live_round,
    make_lineup,
    new_game,
    play_round,
    prepare_live_round,
    season_summary,
    simulate_cup_remaining,
    simulate_cup_round,
)
from src.training import DAYS, PLAN_PRESETS, SESSION_ORDER, SESSION_TYPES, apply_training_plan, auto_plan, plan_name
from src.youth import CATEGORY_AGES, CATEGORY_LABELS, YOUTH_CATEGORIES, promote_youth, release_youth

api = Blueprint("api", __name__, url_prefix="/api")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _web():
    """Import the Flask module lazily to avoid an import cycle."""
    import web.app as web

    return web


def _error(message: str, status: int = 400, code: str = "bad_request"):
    return jsonify({"ok": False, "error": message, "code": code}), status


def _state():
    web = _web()
    state = web.get_state()
    if state is None:
        return None, _error("No hay una partida activa.", 401, "no_game")
    return state, None


def _ok(data=None, message: str | None = None):
    payload = {"ok": True, "data": data}
    if message:
        payload["message"] = message
    return jsonify(payload)


def _save(state):
    _web().save_state(state)


def _money(n) -> int:
    return int(round(n or 0))


def _player(p, team=None):
    web = _web()
    photo = web.photo_src(p)
    return {
        "id": p.id,
        "name": p.name,
        "team_name": p.team_name,
        "origin_team": p.origin_team,
        "team_id": team.id if team is not None else None,
        "position_group": p.position_group,
        "subposition": p.subposition,
        "age": p.age,
        "overall": round(float(p.overall), 1),
        "potential": round(float(p.potential), 1),
        "attributes": p.attributes,
        "overalls": p.overalls,
        "archetype": p.archetype,
        "perfil": p.perfil,
        "value": _money(p.value),
        "fatigue": round(float(p.fatigue), 1),
        "morale": p.morale,
        "relationship": p.relationship,
        "relationship_label": p.relationship_label,
        "absence_label": p.absence_label,
        "available": p.available,
        "form": round(float(p.form), 1),
        "injury": p.injury,
        "injury_type": p.injury_type,
        "injury_severity": p.injury_severity,
        "injury_started": p.injury_started,
        "injury_expected": p.injury_expected,
        "injury_history": p.injury_history,
        "suspension": p.suspension,
        "suspension_reason": p.suspension_reason,
        "suspension_started": p.suspension_started,
        "card_history": p.card_history,
        "traits": p.traits,
        "promises": p.promises,
        "season_goals": p.season_goals,
        "season_assists": p.season_assists,
        "apps": p.apps,
        "rating": round(float(p.rating), 2),
        "salary": _money(p.salary),
        "contract_until": p.contract_until,
        "league": p.league,
        "league_label": league_label(p.league),
        "photo": photo,
        "photo_remote": p.photo_remote,
        "initials": web.initials(p.name),
        "stars": stars_text(p.overall, p.league),
        "stars_bar": stars_bar(p.overall, p.league),
        "tier": tier(p.overall, p.league),
        "youth_category": p.youth_category,
        "career": p.career,
        "transfer_listed": p.transfer_listed,
        "transfer_asking_price": p.transfer_asking_price,
        "brand_deal": p.brand_deal,
    }


def _team_summary(t, position=None):
    web = _web()
    return {
        "id": t.id,
        "name": t.name,
        "league": t.league,
        "city": t.city,
        "community": t.community,
        "country": t.country,
        "stadium_name": t.stadium_name,
        "stadium_capacity": t.stadium_capacity,
        "board_expectation": t.board_expectation,
        "points": t.points,
        "played": t.played,
        "won": t.won,
        "drawn": t.drawn,
        "lost": t.lost,
        "goals_for": t.goals_for,
        "goals_against": t.goals_against,
        "goal_difference": t.goals_for - t.goals_against,
        "position": position,
        "crest": web.crest_src(t),
        "morale": t.morale,
        "cohesion": t.cohesion,
    }


def _team(t):
    web = _web()
    payload = _team_summary(t)
    payload.update(
        {
            "tactics": t.tactics.to_dict(),
            "budget": _money(t.budget),
            "transfer_budget": _money(t.transfer_budget),
            "wage_budget": _money(t.wage_budget),
            "board_confidence": t.board_confidence,
            "fan_confidence": t.fan_confidence,
            "manager_rating": t.manager_rating,
            "assistant_rating": t.assistant_rating,
            "academy_rating": t.academy_rating,
            "board_pressure": t.board_pressure,
            "board_patience": t.board_patience,
            "prep_bonus": round(float(t.prep_bonus), 2),
            "media_confidence": t.media_confidence,
            "equipment_bonus": round(float(t.equipment_bonus), 2),
            "equipment_deals": t.equipment_deals,
            "management_score": round(float(t.management_score()), 1),
            "brand_rating": t.brand_rating,
            "ticket_price": t.ticket_price,
            "merchandising": t.merchandising,
            "sponsor_deals": t.sponsor_deals,
            "commercial_history": t.commercial_history[-10:],
            "player_wage_bill": _money(t.player_wage_bill()),
            "staff_wage_bill": _money(t.staff_wage_bill()),
            "players": [_player(p, t) for p in t.players],
            "staff": [
                {
                    "role": m.role,
                    "role_label": STAFF_LABELS.get(m.role, m.role),
                    "name": m.name,
                    "rating": m.rating,
                    "salary": _money(m.salary),
                    "contract_until": m.contract_until,
                    "source": m.source,
                    "confidence": m.confidence,
                    "relationship": m.relationship,
                    "relationship_label": m.relationship_label,
                    "morale": m.morale,
                }
                for m in t.staff
            ],
            "board": [
                {
                    "role": m.role,
                    "name": m.name,
                    "source": m.source,
                    "confidence": m.confidence,
                }
                for m in t.board
            ],
            "youth": [_player(p, t) for p in t.youth],
        }
    )
    return payload


def _awards_payload(state, awards):
    web = _web()
    positions = {t.id: i for i, t in enumerate(state.table(), 1)}
    rows = []
    for award in awards:
        row = dict(award)
        team = state.teams.get(row.get("team_id"))
        if team:
            row["team_crest"] = web.crest_src(team)
            row["team_position"] = positions.get(team.id)
        player = next((p for t in state.teams.values() for p in t.players if p.id == row.get("player_id")), None)
        if player:
            row["photo"] = web.photo_src(player)
        rows.append(row)
    return rows


def _news_item(state, item):
    """Add real crest URLs and related entities to a news item."""
    web = _web()
    payload = dict(item)
    players_by_id = {p.id: p for t in state.teams.values() for p in t.players}
    players_by_id.update({p.id: p for p in state.free_agents})
    teams_by_id = state.teams
    related_players = []
    for player_id in payload.get("player_ids", []):
        player = players_by_id.get(player_id)
        if player:
            related_players.append(_player(player))
    positions = {t.id: i for i, t in enumerate(state.table(), 1)}
    related_teams = []
    for team_id in payload.get("team_ids", []):
        team = teams_by_id.get(team_id)
        if team:
            related_teams.append(_team_summary(team, positions.get(team.id)))
    payload["related_players"] = related_players
    payload["related_teams"] = related_teams
    if payload.get("crest_id"):
        payload["crest"] = web.crest_src(payload["crest_id"])
    if payload.get("crest_id2"):
        payload["crest2"] = web.crest_src(payload["crest_id2"])
    if payload.get("photo"):
        payload["photo_url"] = web.url_for("player_photo", filename=payload["photo"])
    payload["awards"] = _awards_payload(state, payload.get("awards", []))
    return payload


def _fixture(f, state):
    web = _web()
    home = state.teams.get(f.home_id)
    away = state.teams.get(f.away_id)
    return {
        "id": f.id,
        "round": f.round,
        "date": f.date,
        "phase": f.phase,
        "played": f.played,
        "home_id": f.home_id,
        "away_id": f.away_id,
        "home_name": home.name if home else f.home_id,
        "away_name": away.name if away else f.away_id,
        "home_crest": web.crest_src(home) if home else "",
        "away_crest": web.crest_src(away) if away else "",
        "home_goals": f.home_goals,
        "away_goals": f.away_goals,
        "home_stats": f.home_stats,
        "away_stats": f.away_stats,
        "events": f.events[-60:],
        "attendance": f.attendance,
        "travel": f.travel,
        "label": web.fixture_label(f),
        "is_cup": f.phase.startswith("cup_"),
    }


def _competition(meta):
    return {
        "code": meta.code,
        "name": meta.name,
        "short_name": meta.short_name,
        "country": meta.country,
        "country_code": meta.country_code,
        "confederation": meta.confederation,
        "standard": meta.standard,
        "start_date": meta.start_date,
        "teams": meta.teams,
        "format": meta.format,
        "playoffs": meta.playoffs,
        "relegation": meta.relegation,
        "international": meta.international,
    }


def _slot_rows(rows):
    out = []
    for row in rows:
        out.append(
            {
                "label": row["label"],
                "slots": [
                    {
                        "index": s["index"],
                        "code": s["code"],
                        "group": s["group"],
                        "mismatch": s["mismatch"],
                        "player": _player(s["player"]) if s.get("player") else None,
                    }
                    for s in row["slots"]
                ],
            }
        )
    return out


def _promotion_payload(state):
    """Enriquece la fase de ascenso con equipos, nombres y contexto de UI."""
    raw = state.promotion or {}
    if not raw or competition(state.competition).system != "regional":
        return {}

    def teams_for(ids):
        return [_team_summary(state.teams[tid]) for tid in ids if tid in state.teams]

    groups = []
    for group in raw.get("groups", []):
        row = dict(group)
        row["teams"] = teams_for(group.get("team_ids", []))
        row["winner"] = (
            state.teams[group["winner_id"]].name if group.get("winner_id") in state.teams else ""
        )
        groups.append(row)
    final_group = raw.get("final_group")
    if final_group:
        final_group = dict(final_group)
        final_group["teams"] = teams_for(final_group.get("team_ids", []))
        final_group["champion"] = (
            state.teams[final_group["champion_id"]].name
            if final_group.get("champion_id") in state.teams
            else ""
        )
    qualified_ids = [tid for group in groups for tid in group.get("team_ids", [])]
    user_group = next((group["name"] for group in groups if state.club_id in group.get("team_ids", [])), "")
    path = promotion_path(state)
    return {
        **raw,
        "groups": groups,
        "final_group": final_group,
        "qualified": teams_for(list(dict.fromkeys(qualified_ids))),
        "user_group": user_group,
        "user_qualified": bool(user_group),
        "path": path,
        "leagues": path.get("leagues", []),
    }


def _state_payload(state):
    web = _web()
    user = state.user_team
    table = state.table()
    positions = {t.id: i for i, t in enumerate(table, 1)}
    fx = state.next_user_fixture()
    meta = competition(state.competition)
    live_active = session.get("game_id") in web.LIVE
    return {
        "game": {
            "manager_name": state.manager_name,
            "club_id": state.club_id,
            "season": state.season,
            "round": state.round,
            "date": state.date,
            "competition": state.competition,
            "country": state.country,
            "phase": state.phase,
            "total_rounds": state.total_rounds,
            "save_name": session.get("save_name", ""),
            "live_active": live_active,
            "week_trained": state.week_trained,
            "dhb_group": state.dhb_group,
            "promotion_round": state.promotion_round,
        },
        "promotion": _promotion_payload(state),
        "objectives": competition_objectives(state),
        "competition": _competition(meta),
        "team": _team(user),
        "table": [_team_summary(t, positions[t.id]) for t in table],
        "fixtures": [_fixture(f, state) for f in state.fixtures],
        "next_fixture": _fixture(fx, state) if fx else None,
        "finance": financial_summary(user),
        "commercial": commercial_summary(state),
        "friendlies": friendlies_payload(state),
        "news": [_news_item(state, item) for item in news_feed(state, 20)],
        "awards": _awards_payload(state, awards_for_last_match(state)),
        "inbox": list(reversed(state.inbox[-8:])),
        "daily_events": list(reversed(state.daily_events[-20:])),
        "decisions": pending_game_events(state),
        "event_history": game_event_history(state, 20),
        "chat_messages": list(reversed(state.chat_messages[-30:])),
        "press": {
            "done": state.press_done_round == state.round,
            "history": state.press_history[-8:],
            "post_available": post_press_available(state),
            "post_done": not post_press_available(state),
        },
        "market": {
            "window": market_window(state),
            "status": market_window_text(state),
            "offers": state.transfer_offers,
            "history": state.market_history[-5:],
            "negotiations": state.negotiations[-10:],
        },
        "cup": {
            "active": state.cup_active,
            "round": state.cup_round,
            "status": cup_status_text(state),
            "fixtures": [_fixture(f, state) for f in cup_round_fixtures(state)],
            "next": _fixture(cup_next_user_fixture(state), state) if cup_next_user_fixture(state) else None,
        },
        "ehl": state.ehl,
        "ehl_next": ehl_next_date(state),
        "ehl_status": ehl_status_text(state),
        "last_result": state.last_result,
        "manual_lineup": state.manual_lineup,
        "weekly_plan": state.weekly_plan,
        "training_report": state.training_report,
        "season_end": season_summary(state) if state.phase == "season_end" else None,
        "saves": _saves_payload(),
    }


def _saves_payload():
    web = _web()
    try:
        clubs = {**load_clubs()[0], **club_catalog()}
    except Exception:
        clubs = {}
    saves = list_saves(web.WEB_DB)
    for row in saves:
        club = clubs.get(row["club_id"], {})
        row["club_name"] = club.get("name", row["club_id"])
        crest = web.crest_src(row["club_id"])
        row["crest"] = "" if "/crest/" in crest else crest
        row["is_current"] = row["name"] == session.get("save_name")
    return saves


def _difficulty(expectation):
    e = (expectation or "").lower()
    if "título" in e or "final four" in e:
        return "Muy alta"
    if "top 4" in e:
        return "Alta"
    if "top 6" in e or "consolidar" in e:
        return "Media"
    if "permanencia" in e or "salvación" in e:
        return "Baja"
    if "ascenso" in e:
        return "Alta"
    return "Media"


def _catalog():
    teams, clubs, _ = load_all_teams()
    from src.regional import load_regional_teams

    regional_teams, regional_clubs, _ = load_regional_teams()
    teams.update(regional_teams)
    clubs.update(regional_clubs)
    order = {c.code: i for i, c in enumerate(COMPETITIONS.values())}
    playable = [t for t in teams.values() if t.league in order]
    playable.sort(key=lambda t: (order.get(t.league, 99), t.name))
    groups = []
    for meta in playable_competitions():
        members = [t for t in playable if t.league == meta.code]
        if members:
            groups.append(
                {
                    "competition": _competition(meta),
                    "clubs": [
                        {
                            **_team_summary(t),
                            "stadium": clubs.get(t.id, {}).get("stadium", {}).get("name", t.stadium_name),
                            "expectation": t.board_expectation,
                            "difficulty": _difficulty(t.board_expectation),
                        }
                        for t in members
                    ],
                }
            )
    return {
        "leagues": groups,
        "clubs": [club for group in groups for club in group["clubs"]],
        "competitions": [_competition(c) for c in COMPETITIONS.values()],
    }


def _new_state(club_id: str, manager: str, seed_raw: str | None):
    web = _web()
    seed = int(seed_raw) if seed_raw and str(seed_raw).isdigit() else None
    state = new_game(club_id, manager or "Entrenador", seed)
    old_gid = session.get("game_id")
    if old_gid:
        web.LIVE.pop(old_gid, None)
    gid = uuid.uuid4().hex
    web.GAMES[gid] = state
    session["game_id"] = gid
    session["save_name"] = f"{state.user_team.name} · {state.season} · {gid[:4]}"
    web.save_state(state)
    return state


# ---------------------------------------------------------------------------
# menu / game lifecycle
# ---------------------------------------------------------------------------


@api.get("/health")
def health():
    return _ok({"service": "hockey-manager", "version": "react-1"})


@api.get("/menu")
def menu():
    web = _web()
    state = web.get_state()
    current = None
    if state is not None:
        current = {
            "team": _team_summary(state.user_team),
            "competition": _competition(competition(state.competition)),
            "season": state.season,
            "round": state.round,
            "date": state.date,
            "save_name": session.get("save_name", ""),
            "live_active": session.get("game_id") in web.LIVE,
        }
    return _ok({"current": current, "saves": _saves_payload()})


@api.get("/new-game")
def new_game_catalog():
    return _ok(_catalog())


@api.post("/new-game")
def create_game():
    payload = request.get_json(silent=True) or request.form
    club_id = str(payload.get("club_id", "")).strip()
    manager = str(payload.get("manager", "Entrenador")).strip() or "Entrenador"
    seed = str(payload.get("seed", "")).strip()
    if not club_id:
        return _error("Elige un club.", 400, "club_required")
    try:
        state = _new_state(club_id, manager, seed)
    except ValueError as exc:
        return _error(str(exc), 400, "invalid_club")
    return _ok(_state_payload(state), "Partida creada.")


@api.get("/load")
def load_catalog():
    return _ok({"saves": _saves_payload()})


@api.post("/load")
def load_save():
    web = _web()
    payload = request.get_json(silent=True) or request.form
    name = str(payload.get("name", "")).strip()
    if not name:
        return _error("Indica una partida.", 400, "save_required")
    try:
        state = load_game(name, web.WEB_DB)
    except Exception as exc:
        return _error(f"No se pudo cargar: {exc}", 404, "load_failed")
    old_gid = session.get("game_id")
    if old_gid:
        web.LIVE.pop(old_gid, None)
    gid = uuid.uuid4().hex
    web.GAMES[gid] = state
    session["game_id"] = gid
    session["save_name"] = name
    return _ok(_state_payload(state), "Partida cargada.")


@api.post("/save")
def save_game():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    name = str(payload.get("name", "")).strip()
    if name:
        session["save_name"] = name
    _save(state)
    return _ok(_state_payload(state), "Partida guardada.")


@api.delete("/saves")
def delete_save_route():
    web = _web()
    payload = request.get_json(silent=True) or request.form
    name = str(payload.get("name", "")).strip()
    if not name:
        return _error("Indica la partida que quieres eliminar.", 400, "save_required")
    try:
        deleted = delete_saved_game(name, web.WEB_DB)
    except Exception as exc:
        return _error(f"No se pudo eliminar: {exc}", 400, "delete_failed")
    if not deleted:
        return _error("No existe esa partida.", 404, "save_not_found")
    if session.get("save_name") == name:
        session.pop("save_name", None)
    return _ok({"saves": _saves_payload()}, "Partida eliminada.")


@api.patch("/saves")
def rename_save_route():
    web = _web()
    payload = request.get_json(silent=True) or request.form
    name = str(payload.get("name", "")).strip()
    new_name = str(payload.get("new_name", "")).strip()
    if not name or not new_name:
        return _error("Indica la partida y el nombre nuevo.", 400, "save_required")
    try:
        renamed = rename_saved_game(name, new_name, web.WEB_DB)
    except KeyError:
        return _error("No existe esa partida.", 404, "save_not_found")
    except ValueError as exc:
        return _error(str(exc), 409, "save_name_conflict")
    if session.get("save_name") == name:
        session["save_name"] = renamed
    return _ok({"saves": _saves_payload()}, "Partida renombrada.")


@api.post("/exit")
def exit_game():
    web = _web()
    state = web.get_state()
    if state:
        try:
            _save(state)
        except Exception:
            pass
    gid = session.pop("game_id", None)
    session.pop("save_name", None)
    if gid:
        web.LIVE.pop(gid, None)
    return _ok({"saves": _saves_payload()}, "Partida guardada. Has vuelto al menú.")


@api.get("/state")
def game_state():
    state, err = _state()
    if err:
        return err
    return _ok(_state_payload(state))


@api.post("/simulate")
def simulate():
    state, err = _state()
    if err:
        return err
    web = _web()
    if session.get("game_id") in web.LIVE:
        return _error("Termina primero el partido en directo.", 409, "live_active")
    payload = request.get_json(silent=True) or request.form
    mode = payload.get("mode", "day")
    target = str(payload.get("target_date", "")).strip()
    if mode == "next_match":
        match_day = next_match_date(state)
        if not match_day:
            return _error("No queda ningún partido pendiente.", 409, "no_match")
        result = simulate_days(state, target_date=match_day, stop_at_match=True, stop_at_decision=True)
    elif mode == "date":
        if not target:
            return _error("Elige una fecha.", 400, "date_required")
        try:
            result = simulate_days(state, target_date=target, stop_at_match=True, stop_at_decision=True)
        except ValueError:
            return _error("Fecha no válida.", 400, "invalid_date")
    else:
        result = simulate_days(state, days=1, stop_at_match=True, stop_at_decision=True)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo avanzar."), 409, "simulate_failed")
    _save(state)
    data = _state_payload(state)
    data["simulation"] = result
    message = f"Calendario avanzado {result['days']} día(s)."
    if result.get("stopped_at_decision"):
        message += " Hay una decisión pendiente."
    return _ok(data, message)


# ---------------------------------------------------------------------------
# decisiones / eventos
# ---------------------------------------------------------------------------


@api.get("/events")
def events_list():
    state, err = _state()
    if err:
        return err
    return _ok({"pending": pending_game_events(state), "history": game_event_history(state, 30)})


@api.post("/events/<instance_id>")
def events_resolve(instance_id: str):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    choice = payload.get("choice", payload.get("option", ""))
    result = resolve_game_event(state, instance_id, choice)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo resolver la decisión."), 409, "event_resolve_failed")
    _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message"))


# ---------------------------------------------------------------------------
# dashboard / news / chat
# ---------------------------------------------------------------------------


@api.get("/news")
def news():
    state, err = _state()
    if err:
        return err
    items = [_news_item(state, item) for item in news_feed(state, 30)]
    return _ok(
        {
            "news": items,
            "awards": _awards_payload(state, awards_for_last_match(state)),
            "daily_events": list(reversed(state.daily_events[-30:])),
        }
    )


@api.get("/medical")
def medical():
    state, err = _state()
    if err:
        return err
    team = state.user_team
    injured = sorted(
        [player for player in team.players if player.injury > 0],
        key=lambda player: (-player.injury, player.name),
    )
    suspended = sorted(
        [player for player in team.players if player.suspension > 0],
        key=lambda player: (-player.suspension, player.name),
    )
    history: list[dict] = []
    for player in team.players:
        for item in player.injury_history:
            history.append(
                {
                    **item,
                    "player_id": player.id,
                    "player_name": player.name,
                    "kind": "injury",
                }
            )
        for item in player.card_history:
            history.append(
                {
                    **item,
                    "player_id": player.id,
                    "player_name": player.name,
                    "kind": "card",
                }
            )
    history.sort(key=lambda item: (str(item.get("date", "")), int(item.get("minute", 0))), reverse=True)
    avg_fatigue = sum(player.fatigue for player in team.players) / max(1, len(team.players))
    return _ok(
        {
            "injuries": [_player(player, team) for player in injured],
            "suspensions": [_player(player, team) for player in suspended],
            "history": history[:40],
            "summary": {
                "available": len(team.available_players),
                "injured": len(injured),
                "suspended": len(suspended),
                "avg_fatigue": round(avg_fatigue, 1),
                "risk": sum(1 for player in team.players if player.fatigue >= 65),
                "physio": team.staff_rating("physio"),
                "fitness_coach": team.staff_rating("fitness_coach"),
            },
        }
    )


def _staff_payload(member):
    return {
        "role": member.role,
        "role_label": STAFF_LABELS.get(member.role, member.role),
        "name": member.name,
        "rating": member.rating,
        "salary": _money(member.salary),
        "contract_until": member.contract_until,
        "source": member.source,
        "confidence": member.confidence,
        "relationship": member.relationship,
        "relationship_label": member.relationship_label,
        "morale": member.morale,
    }


def _chat_payload(state):
    team = state.user_team
    players = {p.id: _player(p, team) for p in team.players}
    staff = {m.role: _staff_payload(m) for m in team.staff if m.role != "head_coach"}
    targets = conversation_targets(state)
    for target in targets["players"]:
        player = players.get(target["target_id"])
        if player:
            target["photo"] = player["photo"]
    messages = []
    for message in reversed(state.chat_messages[-60:]):
        row = dict(message)
        player = players.get(row.get("player_id", ""))
        if player:
            row["target_photo_url"] = player["photo"]
        messages.append(row)
    return {
        "messages": messages,
        "players": players,
        "staff": staff,
        "targets": targets,
    }


@api.get("/chat")
def chat():
    state, err = _state()
    if err:
        return err
    return _ok(_chat_payload(state))


@api.get("/chat/topics")
def chat_topics():
    state, err = _state()
    if err:
        return err
    target_type = request.args.get("target_type", "player")
    target_id = request.args.get("target_id", "")
    try:
        payload = topics_for_target(state, target_type, target_id)
    except KeyError as exc:
        return _error(str(exc), 404, "target_not_found")
    return _ok(payload)


@api.post("/chat/start")
def chat_start():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    target_type = str(payload.get("target_type", "player"))
    target_id = str(payload.get("target_id", ""))
    topic_id = payload.get("topic") or None
    try:
        message = create_conversation(state, date.fromisoformat(state.date), target_type, target_id, topic_id)
    except KeyError as exc:
        return _error(str(exc), 404, "target_not_found")
    _save(state)
    return _ok({"message": message, **_chat_payload(state)}, "Conversación abierta.")


@api.post("/chat/new")
def chat_new():
    state, err = _state()
    if err:
        return err
    message = random_conversation(state, date.fromisoformat(state.date), random.Random(state.seed + len(state.chat_messages) * 31))
    if message is None:
        return _error("No hay objetivos disponibles.", 409, "no_chat_targets")
    _save(state)
    return _ok(_chat_payload(state), "Has abierto una conversación con el vestuario.")


@api.post("/chat/<message_id>")
def chat_answer(message_id):
    state, err = _state()
    if err:
        return err
    message = next((m for m in state.chat_messages if m.get("id") == message_id), None)
    if not message or message.get("answered"):
        return _error("Esa conversación ya no está disponible.", 409, "chat_unavailable")
    payload = request.get_json(silent=True) or request.form
    try:
        choice = int(payload.get("option", 0))
    except (TypeError, ValueError):
        choice = 0
    result = apply_conversation_choice(state, message, choice)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo responder."), 409, "chat_failed")
    _save(state)
    return _ok({"result": result, **_chat_payload(state)}, result.get("message", "Conversación registrada."))


# ---------------------------------------------------------------------------
# squad / player / team
# ---------------------------------------------------------------------------


@api.get("/squad")
def squad():
    state, err = _state()
    if err:
        return err
    groups = []
    for group in ("Portero", "Defensa", "Medio", "Delantero"):
        members = [p for p in state.user_team.players if p.position_group == group]
        if members:
            groups.append({"group": group, "players": [_player(p, state.user_team) for p in sorted(members, key=lambda p: (p.subposition, -p.overall))]})
    return _ok({"groups": groups, "team": _team(state.user_team)})


@api.get("/player/<player_id>")
def player_detail(player_id):
    state, err = _state()
    if err:
        return err
    owner = next((t for t in state.teams.values() if any(p.id == player_id for p in t.players)), None)
    player = next((p for p in owner.players if p.id == player_id), None) if owner else None
    if player is None:
        player = next((p for p in state.free_agents if p.id == player_id), None)
    if player is None:
        return _error("Jugador no encontrado.", 404, "player_not_found")
    owner_summary = _team_summary(owner) if owner else None
    data = {
        "player": _player(player, owner),
        "owner": owner_summary,
        "owner_name": owner.name if owner else "Agente libre",
        "is_user": owner is not None and owner.id == state.club_id,
        "editor": editor_payload(player),
        "market": None,
    }
    if owner is None or owner.id != state.club_id:
        data["market"] = {
            "asking": asking_price(player),
            "scout": scout_range(player, state.user_team.staff_rating("scout")),
            "window": market_window(state),
            "window_text": market_window_text(state),
            "minimum_salary": int(max(5000, (player.overall - 45) * 900)),
        }
    return _ok(data)


@api.get("/team/<team_id>")
def team_detail(team_id):
    state, err = _state()
    if err:
        return err
    selected = state.teams.get(team_id)
    if selected is None:
        return _error("Equipo no encontrado.", 404, "team_not_found")
    if state.competition == selected.league:
        table = state.table()
    else:
        table = sorted(
            [t for t in state.teams.values() if t.league == selected.league],
            key=lambda t: (-t.points, -(t.goals_for - t.goals_against), -t.goals_for, t.name),
        )
    position = next((i for i, t in enumerate(table, 1) if t.id == selected.id), 0)
    fixtures = sorted([f for f in state.fixtures if selected.id in (f.home_id, f.away_id)], key=lambda f: (f.date, f.round))
    line, bench = selected.auto_lineup()
    web = _web()
    clubs = {**load_clubs()[0], **club_catalog()}
    club = clubs.get(selected.id, {})
    team_group = ""
    if competition(selected.league).system == "dhb_two_phase" and state.dhb_groups:
        team_group = next((g for g, ids in state.dhb_groups.items() if selected.id in ids), "")
    return _ok(
        {
            "team": _team(selected),
            "club": {
                "history": club.get("history", ""),
                "founded": club.get("founded", ""),
                "full_name": club.get("full_name", selected.name),
                "city": club.get("city", selected.city),
                "province": club.get("province", ""),
                "community": club.get("community", selected.community),
                "country": club.get("country", selected.country),
                "source_url": club.get("source_url", ""),
                "location_verified": club.get("location_verified", False),
                "stadium": club.get("stadium", {}),
                "colors": club.get("colors", []),
                "facilities": club.get("facilities", {}),
            },
            "position": position,
            "table": [_team_summary(t, i) for i, t in enumerate(table, 1)],
            "fixtures": [_fixture(f, state) for f in fixtures],
            "played": [_fixture(f, state) for f in fixtures if f.played][-5:],
            "upcoming": [_fixture(f, state) for f in fixtures if not f.played][:5],
            "probable_lineup": [_player(p, selected) for p in line],
            "probable_bench": [_player(p, selected) for p in bench],
            "probable_rows": _slot_rows(web.lineup_rows(selected, line)),
            "formation": selected.tactics.formation,
            "group": team_group,
            "is_user": selected.id == state.club_id,
        }
    )


# ---------------------------------------------------------------------------
# tactics / training
# ---------------------------------------------------------------------------


def _tactics_payload(state):
    team = state.user_team
    line, bench = make_lineup(team, state.manual_lineup or None)
    slots = FORMATION_SLOTS.get(team.tactics.formation, FORMATION_SLOTS["4-3-3"])
    slot_options = []
    for i, slot in enumerate(slots):
        candidates = sorted(team.available_players, key=lambda p: p.selection_score(slot), reverse=True)[:14]
        if i < len(line) and line[i] not in candidates:
            candidates.append(line[i])
        slot_options.append([_player(p, team) for p in candidates])
    return {
        "tactics": team.tactics.to_dict(),
        "line": [_player(p, team) for p in line],
        "bench": [_player(p, team) for p in bench],
        "slots": slots,
        "slot_rows": _slot_rows(_web().lineup_rows(team, line)),
        "slot_options": slot_options,
        "available": [_player(p, team) for p in sorted(team.available_players, key=lambda p: (p.subposition, -p.overall))],
        "squad": [_player(p, team) for p in sorted(team.players, key=lambda p: (p.position_group, -p.overall))],
        "formations": list(FORMATION_SLOTS),
        "selected": state.manual_lineup,
    }


@api.get("/tactics")
def tactics():
    state, err = _state()
    if err:
        return err
    return _ok(_tactics_payload(state))


@api.post("/tactics")
def save_tactics():
    state, err = _state()
    if err:
        return err
    team = state.user_team
    payload = request.get_json(silent=True) or request.form
    old_formation = team.tactics.formation
    for field in (
        "formation",
        "mentality",
        "press",
        "block",
        "width",
        "tempo",
        "passing",
        "pc_routine",
        "defensive_system",
        "attack_system",
        "outlet",
        "press_trigger",
    ):
        value = payload.get(field)
        if value:
            setattr(team.tactics, field, value)
    if team.tactics.defensive_system == "zona_baja":
        team.tactics.block = "bajo"
    elif team.tactics.defensive_system in ("zona_media", "individual_mixta"):
        team.tactics.block = "medio"
    elif team.tactics.defensive_system in ("zona_alta", "individual_todo_campo"):
        team.tactics.block = "alto"
    specialist_fields = (
        "pc_injector_id",
        "pc_stopper_id",
        "pc_flicker_id",
        "pc_deflector_id",
        "pc_rebounder_id",
        "pc_first_runner_id",
        "pc_goalkeeper_id",
        "stroke_taker_id",
        "stroke_goalkeeper_id",
        "free_hit_taker_id",
    )
    for field in specialist_fields:
        value = str(payload.get(field, "") or "")
        if value and not any(player.id == value for player in team.players):
            value = ""
        setattr(team.tactics, field, value)
    if team.tactics.formation != old_formation:
        state.manual_lineup = []
        message = "Formación cambiada. Once autoalineado."
    elif payload.get("auto"):
        state.manual_lineup = []
        message = "Autoalineación activada."
    else:
        slots = FORMATION_SLOTS.get(team.tactics.formation, FORMATION_SLOTS["4-3-3"])
        selected = [payload.get(f"slot_{i}", "") for i in range(len(slots))]
        selected = [x for x in selected if x]
        if len(selected) == 11 and len(set(selected)) == 11:
            state.manual_lineup = selected
            message = "Once guardado."
        else:
            return _error("El once debe tener 11 jugadores distintos.", 400, "invalid_lineup")
    _save(state)
    data = _tactics_payload(state)
    data["state"] = _state_payload(state)
    return _ok(data, message)


@api.get("/training")
def training():
    state, err = _state()
    if err:
        return err
    opponent = _opponent(state)
    default_plan = auto_plan(state.user_team, opponent, random.Random(state.seed + state.round * 53 + 11))
    return _ok(
        {
            "sessions": SESSION_TYPES,
            "session_order": SESSION_ORDER,
            "days": DAYS,
            "default_plan": default_plan,
            "plan_name": plan_name(state.weekly_plan) if state.weekly_plan else plan_name(default_plan),
            "report": state.training_report,
            "trained": state.week_trained,
            "opponent": _team_summary(opponent) if opponent else None,
            "presets": PLAN_PRESETS,
        }
    )


@api.post("/training")
def apply_training():
    state, err = _state()
    if err:
        return err
    if state.week_trained:
        return _error("La semana ya está planificada.", 409, "already_trained")
    payload = request.get_json(silent=True) or request.form
    action = payload.get("action", "auto")
    if action == "recovery":
        plan = list(PLAN_PRESETS["recuperacion"])
        delegated = False
    elif action == "edit":
        plan = [payload.get(f"session{i}", "recuperacion") for i in range(5)]
        plan = [p if p in SESSION_TYPES else "recuperacion" for p in plan]
        delegated = False
    else:
        plan = auto_plan(state.user_team, _opponent(state), random.Random(state.seed + state.round * 53 + 11))
        delegated = True
    report = apply_training_plan(
        state.user_team,
        plan,
        _opponent(state),
        random.Random(state.seed + state.round * 53 + 17),
        delegated=delegated,
    )
    state.weekly_plan = plan
    state.training_report = report
    state.week_trained = True
    _save(state)
    return _ok(
        {
            "report": report,
            "plan": plan,
            "plan_name": plan_name(plan),
            "trained": True,
            "state": _state_payload(state),
        },
        "Entrenamiento semanal aplicado.",
    )


def _opponent(state):
    fx = state.next_user_fixture()
    if not fx:
        return None
    oid = fx.away_id if fx.home_id == state.club_id else fx.home_id
    return state.teams.get(oid)


# ---------------------------------------------------------------------------
# market
# ---------------------------------------------------------------------------


def _market_player(p, state):
    owner = next((t for t in state.teams.values() if any(x.id == p.id for x in t.players)), None)
    return {
        **_player(p, owner),
        "owner": _team_summary(owner) if owner else None,
        "owner_name": owner.name if owner else "Agente libre",
        "asking": asking_price(p),
        "scout": scout_range(p, state.user_team.staff_rating("scout")),
        "minimum_salary": int(max(5000, (p.overall - 45) * 900)),
        "transfer_listed": p.transfer_listed,
        "transfer_asking_price": p.transfer_asking_price,
    }


@api.get("/scouting")
def scouting():
    state, err = _state()
    if err:
        return err
    focus = request.args.get("focus", "equilibrado")
    raw_age = str(request.args.get("max_age", "")).strip()
    max_age = int(raw_age) if raw_age.isdigit() else None
    position = request.args.get("position", "")
    payload = scouting_overview(state, focus=focus, max_age=max_age, position=position or None)
    payload["recommendations"] = [
        {
            **{key: value for key, value in row.items() if key != "player"},
            "player": _market_player(row["player"], state),
        }
        for row in payload["recommendations"]
    ]
    return _ok(payload)


@api.post("/scouting/assignments")
def scouting_assignment_create():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    raw_age = str(payload.get("max_age", "")).strip()
    max_age = int(raw_age) if raw_age.isdigit() else None
    result = create_assignment(
        state,
        str(payload.get("scout_id", "")),
        str(payload.get("competition", "")),
        str(payload.get("position", "")),
        max_age,
        str(payload.get("focus", "equilibrado") or "equilibrado"),
    )
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo crear la asignación."), 409, "scouting_failed")
    _save(state)
    overview = scouting_overview(state)
    overview["recommendations"] = [
        {**{key: value for key, value in row.items() if key != "player"}, "player": _market_player(row["player"], state)}
        for row in overview["recommendations"]
    ]
    return _ok({"result": result, "scouting": overview, "state": _state_payload(state)}, result["message"])


@api.delete("/scouting/assignments/<assignment_id>")
def scouting_assignment_delete(assignment_id: str):
    state, err = _state()
    if err:
        return err
    result = cancel_assignment(state, assignment_id)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo cancelar la asignación."), 409, "scouting_failed")
    _save(state)
    overview = scouting_overview(state)
    overview["recommendations"] = [
        {**{key: value for key, value in row.items() if key != "player"}, "player": _market_player(row["player"], state)}
        for row in overview["recommendations"]
    ]
    return _ok({"result": result, "scouting": overview, "state": _state_payload(state)}, result["message"])


@api.get("/market")
def market():
    state, err = _state()
    if err:
        return err
    def number_arg(name, cast=int):
        raw = str(request.args.get(name, "")).strip()
        if not raw:
            return None
        try:
            return cast(raw)
        except ValueError:
            return None

    max_value = number_arg("max_value")
    min_age = number_arg("min_age")
    max_age = number_arg("max_age")
    min_overall = number_arg("min_overall", float)
    max_overall = number_arg("max_overall", float)
    min_attribute = number_arg("min_attribute")
    position = request.args.get("position", "")
    club_id = request.args.get("club_id", "")
    league = request.args.get("league", "")
    query = request.args.get("q", "").strip()
    attribute = request.args.get("attribute", "")
    listed_only = request.args.get("listed") == "1"
    free_agents_only = request.args.get("free_agents") == "1"
    staff_role = request.args.get("staff_role", "")
    staff_min_rating = number_arg("staff_min_rating")
    staff_max_salary = number_arg("staff_max_salary")
    players = market_players(
        state,
        limit=3000,
        max_value=max_value,
        position=position or None,
        min_age=min_age,
        max_age=max_age,
        min_overall=min_overall,
        max_overall=max_overall,
        league=league or None,
        club_id=club_id or None,
        query=query or None,
        attribute=attribute or None,
        min_attribute=min_attribute,
        listed_only=listed_only,
        free_agents_only=free_agents_only,
    )
    owners = {p.id: t for t in state.teams.values() for p in t.players}
    regular_players = [p for p in players if p.id in owners]
    free_agents = [p for p in players if p.id not in owners]
    all_teams = sorted(state.teams.values(), key=lambda t: (t.league, t.name))
    leagues = []
    seen = set()
    for team in all_teams:
        if team.league in seen:
            continue
        seen.add(team.league)
        meta = competition(team.league)
        leagues.append(
            {
                "code": meta.code,
                "name": meta.name,
                "short_name": meta.short_name,
                "country": meta.country,
                "standard": meta.standard,
            }
        )
    for code in sorted({p.league for p in state.free_agents}):
        if code in seen:
            continue
        seen.add(code)
        meta = profile(code)
        leagues.append(
            {
                "code": code,
                "name": league_label(code),
                "short_name": league_label(code),
                "country": "España",
                "standard": meta.standard,
            }
        )
    leagues.sort(key=lambda row: row["standard"], reverse=True)
    staff = staff_market(
        state,
        limit=80,
        role=staff_role or None,
        min_rating=staff_min_rating,
        max_salary=staff_max_salary,
    )
    return _ok(
        {
            "players": [_market_player(p, state) for p in regular_players],
            "free_agents": [_market_player(p, state) for p in free_agents],
            "staff": staff,
            "staff_roles": STAFF_LABELS,
            "teams": [_team_summary(t) for t in all_teams],
            "leagues": leagues,
            "attributes": sorted({key for player in players for key in player.attributes}),
            "listed": [
                _player(p, state.user_team)
                for p in state.user_team.players
                if p.transfer_listed
            ],
            "pending_transfers": state.pending_transfers,
            "own_players": [_player(p, state.user_team) for p in state.user_team.players],
            "window": market_window(state),
            "window_text": market_window_text(state),
            "offers": state.transfer_offers,
            "negotiations": state.negotiations[-10:],
            "query": query,
            "max_value": max_value,
            "min_age": min_age,
            "max_age": max_age,
            "min_overall": min_overall,
            "max_overall": max_overall,
            "position": position,
            "club_id": club_id,
            "league": league,
            "attribute": attribute,
            "min_attribute": min_attribute,
            "listed_only": listed_only,
            "free_agents_only": free_agents_only,
            "total": len(players),
            "free_agent_total": len(free_agents),
            "staff_total": len(staff),
        }
    )


@api.get("/board")
def board():
    state, err = _state()
    if err:
        return err
    return _ok(board_overview(state))


@api.post("/board/request")
def board_request():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    result = request_board(state, str(payload.get("request_id", "")))
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo procesar la petición."), 409, "board_request_failed")
    _save(state)
    return _ok(
        {"result": result, "board": board_overview(state), "state": _state_payload(state)},
        result.get("message", "Petición registrada."),
    )


@api.get("/analysis")
def analysis():
    state, err = _state()
    if err:
        return err
    return _ok(analysis_overview(state, str(request.args.get("fixture_id", ""))))


@api.get("/finance")
def finance():
    state, err = _state()
    if err:
        return err
    return _ok(finance_overview(state))


@api.post("/finance/ticket")
def finance_ticket():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    try:
        price = int(payload.get("price", state.user_team.ticket_price))
    except (TypeError, ValueError):
        return _error("Precio no válido.", 400, "invalid_price")
    result = set_ticket_price(state, price)
    _save(state)
    return _ok(
        {"result": result, "finance": finance_overview(state), "state": _state_payload(state)},
        result.get("message", ""),
    )


@api.get("/commercial")
def commercial():
    state, err = _state()
    if err:
        return err
    generate_sponsor_offers(state)
    return _ok(
        {
            "commercial": commercial_summary(state),
            "brands": brand_summary(state),
            "finance": financial_summary(state.user_team),
            "team": _team(state.user_team),
        }
    )


@api.post("/commercial/offers/<offer_id>")
def commercial_offer_action(offer_id):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    action = payload.get("action", "accept")
    result = accept_sponsor_offer(state, offer_id) if action == "accept" else reject_sponsor_offer(state, offer_id)
    if result.get("ok"):
        _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message", "")) if result.get("ok") else _error(result.get("message", "No se pudo procesar."), 409, "sponsor_failed")


@api.post("/commercial/ticket")
def commercial_ticket():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    try:
        price = int(payload.get("price", state.user_team.ticket_price))
    except (TypeError, ValueError):
        return _error("Precio no válido.", 400, "invalid_price")
    result = set_ticket_price(state, price)
    _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message", ""))


@api.post("/commercial/campaign")
def commercial_campaign():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    result = run_campaign(state, str(payload.get("campaign_id", "")))
    if result.get("ok"):
        _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message", "")) if result.get("ok") else _error(result.get("message", "No se pudo lanzar."), 409, "campaign_failed")


@api.post("/market/list/<player_id>")
def market_list(player_id):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    result = list_player_for_transfer(
        state,
        player_id,
        bool(payload.get("listed", True)),
        int(payload.get("asking_price", 0) or 0),
    )
    if result.get("ok"):
        _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message", "")) if result.get("ok") else _error(result.get("message", "No se pudo actualizar."), 409, "list_failed")


@api.post("/market/staff/hire")
def market_staff_hire():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    candidate_id = str(payload.get("candidate_id", ""))
    result = hire_market_staff(state, candidate_id)
    if result.get("ok"):
        _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message", "")) if result.get("ok") else _error(result.get("message", "No se pudo contratar."), 409, "hire_failed")


@api.post("/market/offer/<player_id>")
def market_offer(player_id):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    try:
        fee = int(payload.get("fee", 0) or 0)
        salary = int(payload.get("salary", 0) or 0)
        years = int(payload.get("years", 3) or 3)
    except (TypeError, ValueError):
        return _error("Oferta no válida.", 400, "invalid_offer")
    result = make_transfer_offer(state, player_id, fee, salary, years)
    if result.get("ok"):
        _save(state)
    return _ok(
        {"result": result, "state": _state_payload(state) if result.get("ok") else None},
        result.get("message", ""),
    ) if result.get("ok") else _error(result.get("message", "Oferta rechazada."), 409, "offer_rejected")


@api.post("/market/negotiate/<player_id>")
def market_negotiate(player_id):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    try:
        fee = int(payload.get("fee", 0) or 0)
        salary = int(payload.get("salary", 0) or 0)
        years = int(payload.get("years", 3) or 3)
    except (TypeError, ValueError):
        return _error("Oferta no válida.", 400, "invalid_negotiation")
    result = start_transfer_negotiation(state, player_id, fee, salary, years)
    if result.get("ok"):
        _save(state)
    return _ok(
        {"result": result, "negotiation": result.get("negotiation"), "state": _state_payload(state) if result.get("ok") else None},
        result.get("message", ""),
    ) if result.get("ok") else _error(result.get("message", "No se pudo abrir la negociación."), 409, "negotiation_failed")


@api.post("/market/renew-negotiate/<player_id>")
def market_renew_negotiate(player_id):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    try:
        salary = int(payload.get("salary", 0) or 0)
        years = int(payload.get("years", 3) or 3)
    except (TypeError, ValueError):
        return _error("Contrato no válido.", 400, "invalid_negotiation")
    result = start_renewal_negotiation(state, player_id, salary, years)
    if result.get("ok"):
        _save(state)
    return _ok(
        {"result": result, "negotiation": result.get("negotiation"), "state": _state_payload(state) if result.get("ok") else None},
        result.get("message", ""),
    ) if result.get("ok") else _error(result.get("message", "No se pudo abrir la renovación."), 409, "negotiation_failed")


@api.post("/market/negotiations/<negotiation_id>")
def market_negotiation_action(negotiation_id):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    try:
        fee = int(payload["fee"]) if payload.get("fee") not in (None, "") else None
        salary = int(payload["salary"]) if payload.get("salary") not in (None, "") else None
        years = int(payload["years"]) if payload.get("years") not in (None, "") else None
    except (TypeError, ValueError):
        return _error("Datos de negociación no válidos.", 400, "invalid_negotiation")
    result = respond_negotiation(state, negotiation_id, str(payload.get("action", "counter")), fee, salary, years)
    if result.get("ok"):
        _save(state)
    return _ok(
        {"result": result, "negotiation": result.get("negotiation"), "state": _state_payload(state) if result.get("ok") else None},
        result.get("message", ""),
    ) if result.get("ok") else _error(result.get("message", "No se pudo continuar la negociación."), 409, "negotiation_failed")


@api.post("/market/offers/<offer_id>/counter")
def market_offer_counter(offer_id):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    try:
        fee = int(payload.get("fee", 0) or 0)
        salary = int(payload["salary"]) if payload.get("salary") not in (None, "") else None
        years = int(payload["years"]) if payload.get("years") not in (None, "") else None
    except (TypeError, ValueError):
        return _error("Contraoferta no válida.", 400, "invalid_counter")
    result = counter_incoming_offer(state, offer_id, fee, salary, years)
    if result.get("ok"):
        _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message", "")) if result.get("ok") else _error(result.get("message", "No se pudo enviar la contraoferta."), 409, "counter_failed")


@api.get("/market/offers")
def market_offers():
    state, err = _state()
    if err:
        return err
    offers = generate_incoming_offers(state)
    return _ok({"offers": offers, "state": _state_payload(state)})


@api.post("/market/offers/<offer_id>")
def market_offer_action(offer_id):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    action = payload.get("action", "reject")
    if action == "accept":
        result = accept_incoming_offer(state, offer_id)
    else:
        reject_incoming_offer(state, offer_id)
        result = {"ok": True, "message": "Oferta rechazada."}
    _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message", ""))


@api.get("/market/renew")
def market_renew():
    state, err = _state()
    if err:
        return err
    return _ok({"players": [_player(p, state.user_team) for p in sorted(state.user_team.players, key=lambda p: (p.contract_until, -p.overall))]})


@api.post("/market/renew/<player_id>")
def market_renew_player(player_id):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    try:
        salary = int(payload.get("salary", 0) or 0)
        years = int(payload.get("years", 3) or 3)
    except (TypeError, ValueError):
        return _error("Datos de contrato no válidos.", 400, "invalid_contract")
    result = renew_contract(state, player_id, salary, years)
    if result.get("ok"):
        _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message", "")) if result.get("ok") else _error(result.get("message", "No se pudo renovar."), 409, "renew_rejected")


# ---------------------------------------------------------------------------
# staff / youth
# ---------------------------------------------------------------------------


@api.get("/loans")
def loans():
    state, err = _state()
    if err:
        return err
    return _ok(loan_overview(state))


@api.post("/loans/in")
def loan_in():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    result = request_loan_in(
        state,
        str(payload.get("player_id", "")),
        int(payload.get("wage_share", 50) or 50),
        str(payload.get("playing_time", "rotacion") or "rotacion"),
    )
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo cerrar la cesión."), 409, "loan_in_failed")
    _save(state)
    return _ok({"result": result, "loans": loan_overview(state), "state": _state_payload(state)}, result.get("message", ""))


@api.post("/loans/out")
def loan_out():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    result = offer_loan_out(
        state,
        str(payload.get("player_id", "")),
        str(payload.get("club_id", "")),
        int(payload.get("wage_share", 50) or 50),
        str(payload.get("playing_time", "rotacion") or "rotacion"),
    )
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo ofrecer la cesión."), 409, "loan_out_failed")
    _save(state)
    return _ok({"result": result, "loans": loan_overview(state), "state": _state_payload(state)}, result.get("message", ""))


@api.get("/datahub")
def datahub():
    state, err = _state()
    if err:
        return err
    return _ok(datahub_overview(state))


@api.post("/datahub/instructions")
def datahub_instructions():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    instructions = payload.get("instructions", {})
    if not isinstance(instructions, dict):
        instructions = {}
    result = set_instructions(state, str(payload.get("opponent_id", "")), instructions)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudieron guardar las instrucciones."), 409, "datahub_failed")
    _save(state)
    return _ok({"result": result, "datahub": datahub_overview(state), "state": _state_payload(state)}, result["message"])


@api.get("/affiliates")
def affiliates():
    state, err = _state()
    if err:
        return err
    return _ok({"affiliates": affiliate_overview(state), "mentoring": mentoring_overview(state)})


@api.post("/affiliates/request")
def affiliate_request():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    result = request_affiliate(state, str(payload.get("club_id", "")))
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo firmar la afiliación."), 409, "affiliate_failed")
    _save(state)
    return _ok(
        {
            "result": result,
            "affiliates": affiliate_overview(state),
            "mentoring": mentoring_overview(state),
            "state": _state_payload(state),
        },
        result.get("message", ""),
    )


@api.post("/affiliates/<affiliate_id>/end")
def affiliate_end(affiliate_id: str):
    state, err = _state()
    if err:
        return err
    result = end_affiliate(state, affiliate_id)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo finalizar la afiliación."), 409, "affiliate_failed")
    _save(state)
    return _ok(
        {
            "result": result,
            "affiliates": affiliate_overview(state),
            "mentoring": mentoring_overview(state),
            "state": _state_payload(state),
        },
        result.get("message", ""),
    )


@api.post("/mentoring")
def mentoring_create():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    result = assign_mentor(
        state,
        str(payload.get("mentor_id", "")),
        str(payload.get("mentee_id", "")),
        str(payload.get("focus", "tecnica") or "tecnica"),
    )
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo crear el plan de mentoría."), 409, "mentoring_failed")
    _save(state)
    return _ok(
        {
            "result": result,
            "affiliates": affiliate_overview(state),
            "mentoring": mentoring_overview(state),
            "state": _state_payload(state),
        },
        result.get("message", ""),
    )


@api.delete("/mentoring/<pair_id>")
def mentoring_delete(pair_id: str):
    state, err = _state()
    if err:
        return err
    result = end_mentoring(state, pair_id)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo finalizar el plan."), 409, "mentoring_failed")
    _save(state)
    return _ok(
        {
            "result": result,
            "affiliates": affiliate_overview(state),
            "mentoring": mentoring_overview(state),
            "state": _state_payload(state),
        },
        result.get("message", ""),
    )


@api.get("/history")
def history():
    state, err = _state()
    if err:
        return err
    try:
        limit = max(1, min(500, int(request.args.get("limit", 200))))
    except (TypeError, ValueError):
        limit = 200
    return _ok(
        history_overview(
            state,
            season=str(request.args.get("season", "")),
            competition_code=str(request.args.get("competition", "")),
            team_id=str(request.args.get("team_id", "")),
            player_query=str(request.args.get("player", "")),
            limit=limit,
        )
    )


@api.get("/team-meeting")
def team_meeting():
    state, err = _state()
    if err:
        return err
    return _ok(team_meeting_context(state))


@api.post("/team-meeting")
def team_meeting_perform():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    topics = payload.get("topics", [])
    if not isinstance(topics, list):
        topics = []
    result = perform_team_meeting(
        state,
        str(payload.get("meeting_type", "pre_match") or "pre_match"),
        str(payload.get("tone", "serena") or "serena"),
        [str(item) for item in topics],
        str(payload.get("promise_player_id", "")),
        str(payload.get("promise_type", "")),
    )
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo celebrar la reunión."), 409, "team_meeting_failed")
    _save(state)
    return _ok(
        {"result": result, "meeting": team_meeting_context(state), "state": _state_payload(state)},
        result.get("message", "Reunión celebrada."),
    )


@api.get("/staff")
def staff():
    state, err = _state()
    if err:
        return err
    hireable = (
        "assistant",
        "fitness_coach",
        "gk_coach",
        "performance_analyst",
        "scout",
        "physio",
        "technical_director",
        "commercial_director",
        "marketing_manager",
    )
    free_roles = [r for r in hireable if not any(m.role == r for m in state.user_team.staff)]
    return _ok(
        {
            "team": _team(state.user_team),
            "staff_labels": STAFF_LABELS,
            "free_roles": free_roles,
        }
    )


@api.get("/staff/<role>/candidates")
def staff_candidates_route(role):
    state, err = _state()
    if err:
        return err
    if role not in STAFF_LABELS:
        return _error("Rol no válido.", 400, "invalid_role")
    rng = random.Random(state.seed * 1000 + state.round * 61 + len(state.user_team.staff))
    candidates = staff_candidates(state.user_team, role, rng)
    return _ok(
        {
            "role": role,
            "role_label": STAFF_LABELS[role],
            "candidates": [
                {
                    "role": c.role,
                    "name": c.name,
                    "rating": c.rating,
                    "salary": _money(c.salary),
                    "contract_until": c.contract_until,
                    "source": c.source,
                    "confidence": c.confidence,
                }
                for c in candidates
            ],
        }
    )


@api.post("/staff/hire/<role>")
def staff_hire(role):
    state, err = _state()
    if err:
        return err
    if role not in STAFF_LABELS:
        return _error("Rol no válido.", 400, "invalid_role")
    if any(m.role == role for m in state.user_team.staff):
        return _error("Ese rol ya está cubierto.", 409, "role_filled")
    rng = random.Random(state.seed * 1000 + state.round * 61 + len(state.user_team.staff))
    candidates = staff_candidates(state.user_team, role, rng)
    payload = request.get_json(silent=True) or request.form
    try:
        idx = int(payload.get("candidate", -1))
    except (TypeError, ValueError):
        idx = -1
    if not (0 <= idx < len(candidates)):
        return _error("Candidato no válido.", 400, "invalid_candidate")
    result = hire_staff(state, candidates[idx])
    if result.get("ok"):
        _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message", "")) if result.get("ok") else _error(result.get("message", "No se pudo contratar."), 409, "hire_rejected")


@api.post("/staff/fire/<role>")
def staff_fire(role):
    state, err = _state()
    if err:
        return err
    result = fire_staff(state, role)
    if result.get("ok"):
        _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message", "")) if result.get("ok") else _error(result.get("message", "No se pudo despedir."), 409, "fire_rejected")


@api.get("/youth")
def youth():
    state, err = _state()
    if err:
        return err
    groups = []
    for category in YOUTH_CATEGORIES:
        members = [p for p in state.user_team.youth if p.youth_category == category]
        if members:
            groups.append(
                {
                    "category": category,
                    "label": CATEGORY_LABELS[category],
                    "ages": CATEGORY_AGES[category],
                    "players": [_player(p, state.user_team) for p in members],
                }
            )
    return _ok({"groups": groups, "team": _team(state.user_team)})


@api.post("/youth/<action>/<player_id>")
def youth_action(action, player_id):
    state, err = _state()
    if err:
        return err
    if action == "promote":
        ok, message = promote_youth(state.user_team, player_id)
    elif action == "release":
        ok, message = release_youth(state.user_team, player_id)
    else:
        return _error("Acción no válida.", 400, "invalid_action")
    if ok:
        _save(state)
    return _ok({"state": _state_payload(state)}, message) if ok else _error(message, 409, "youth_action_failed")


# ---------------------------------------------------------------------------
# calendar / friendlies / brands / player editor
# ---------------------------------------------------------------------------


@api.get("/calendar")
def calendar():
    state, err = _state()
    if err:
        return err
    official = sorted(
        [fixture for fixture in state.fixtures if fixture.phase in ("regular", "cup", "promotion")],
        key=lambda fixture: (fixture.date, fixture.round, fixture.id),
    )
    friendly_payload = friendlies_payload(state)
    pending_friendlies = [item for item in friendly_payload["items"] if not item["played"]]
    return _ok(
        {
            "friendlies": friendly_payload,
            "fixtures": [_fixture(fixture, state) for fixture in official],
            "next_fixture": _fixture(state.next_user_fixture(), state) if state.next_user_fixture() else None,
            "next_friendly": pending_friendlies[0] if pending_friendlies else None,
            "today": state.date,
            "season": state.season,
            "competition": _competition(competition(state.competition)),
        }
    )


@api.post("/friendlies")
def friendly_create():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    result = schedule_friendly(
        state,
        str(payload.get("opponent_id", "")),
        str(payload.get("date", "")),
        home=str(payload.get("home", "1")) not in ("0", "false", "False", ""),
        notes=str(payload.get("notes", "")),
    )
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo programar el amistoso."), 409, "friendly_failed")
    _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message", ""))


@api.post("/friendlies/<friendly_id>/play")
def friendly_play(friendly_id: str):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    lineup = payload.get("lineup") if isinstance(payload, dict) else None
    result = play_friendly(state, friendly_id, lineup if isinstance(lineup, list) else None)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo jugar el amistoso."), 409, "friendly_failed")
    _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message", ""))


@api.delete("/friendlies/<friendly_id>")
def friendly_delete(friendly_id: str):
    state, err = _state()
    if err:
        return err
    result = cancel_friendly(state, friendly_id)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo cancelar el amistoso."), 409, "friendly_failed")
    _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message", ""))


@api.get("/brands")
def brands():
    state, err = _state()
    if err:
        return err
    return _ok({"brands": brand_summary(state), "team": _team(state.user_team)})


@api.post("/brands/<offer_id>")
def brand_action(offer_id: str):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    action = payload.get("action", "accept")
    result = accept_brand_offer(state, offer_id) if action == "accept" else reject_brand_offer(state, offer_id)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo procesar la marca."), 409, "brand_failed")
    _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message", ""))


@api.post("/brands/players/<offer_id>")
def player_brand_action(offer_id: str):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    action = payload.get("action", "accept")
    result = accept_player_brand_offer(state, offer_id) if action == "accept" else reject_player_brand_offer(state, offer_id)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo procesar el contrato individual."), 409, "player_brand_failed")
    _save(state)
    return _ok({"result": result, "state": _state_payload(state)}, result.get("message", ""))


@api.post("/player/<player_id>/edit")
def player_edit(player_id: str):
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    changes = payload.get("changes", payload) if isinstance(payload, dict) else {}
    result = edit_player(state, player_id, changes if isinstance(changes, dict) else {})
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo editar la ficha."), 400, "player_edit_failed")
    _save(state)
    player, owner_id = find_player(state, player_id)
    owner = state.teams.get(owner_id) if owner_id else None
    return _ok(
        {
            "result": result,
            "player": _player(player, owner) if player else None,
            "editor": editor_payload(player) if player else None,
            "state": _state_payload(state),
        },
        result.get("message", ""),
    )


# ---------------------------------------------------------------------------
# press / cup / ehl / table
# ---------------------------------------------------------------------------


@api.get("/press")
def press():
    state, err = _state()
    if err:
        return err
    questions = []
    for q in press_questions(state):
        questions.append(
            {
                "id": q["id"],
                "question": q["question"],
                "topic": q.get("topic", ""),
                "player_id": q.get("player_id", ""),
                "options": [
                    {"label": label, "effects": effects, "headline": headline}
                    for label, effects, headline in q["options"]
                ],
            }
        )
    return _ok(
        {
            "questions": questions,
            "context": press_context(state),
            "done": state.press_done_round == state.round,
            "post_available": post_press_available(state),
            "history": state.press_history[-8:],
        }
    )


@api.get("/press/post")
def post_press():
    state, err = _state()
    if err:
        return err
    questions = []
    for q in post_press_questions(state):
        questions.append(
            {
                "id": q["id"],
                "question": q["question"],
                "topic": q.get("topic", ""),
                "options": [
                    {"label": label, "effects": effects, "headline": headline}
                    for label, effects, headline in q["options"]
                ],
            }
        )
    return _ok(
        {
            "questions": questions,
            "context": post_press_context(state),
            "done": not post_press_available(state),
            "available": post_press_available(state),
            "history": [item for item in state.press_history if item.get("kind") == "post"][-8:],
        }
    )


@api.post("/press/post")
def post_press_answer():
    state, err = _state()
    if err:
        return err
    if not post_press_available(state):
        return _error("No hay una rueda de prensa posterior disponible.", 409, "post_press_unavailable")
    payload = request.get_json(silent=True) or request.form
    answers = payload.get("answers", {})
    questions = post_press_questions(state)
    results = []
    for q in questions:
        raw = answers.get(q["id"], 0) if isinstance(answers, dict) else 0
        try:
            idx = int(raw)
        except (TypeError, ValueError):
            idx = 0
        results.append(answer_post_press(state, q["id"], idx))
    _save(state)
    return _ok({"results": results, "state": _state_payload(state)}, "Rueda de prensa posterior completada.")


@api.post("/press")
def press_answer():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    answers = payload.get("answers", {})
    questions = press_questions(state)
    results = []
    for q in questions:
        raw = answers.get(q["id"], 0) if isinstance(answers, dict) else 0
        try:
            idx = int(raw)
        except (TypeError, ValueError):
            idx = 0
        results.append(answer_press(state, q["id"], idx))
    mark_press_done(state)
    _save(state)
    return _ok({"results": results, "state": _state_payload(state)}, "Rueda de prensa completada.")


@api.get("/cup")
def cup():
    state, err = _state()
    if err:
        return err
    if competition(state.competition).system not in ("dha", "dhb_two_phase"):
        return _error("La Copa del Rey solo existe en las ligas españolas.", 400, "cup_unavailable")
    fixtures = [_fixture(f, state) for f in cup_round_fixtures(state)]
    nxt = cup_next_user_fixture(state)
    return _ok(
        {
            "status": cup_status_text(state),
            "active": state.cup_active,
            "round": state.cup_round,
            "fixtures": fixtures,
            "next": _fixture(nxt, state) if nxt else None,
        }
    )


@api.post("/cup")
def cup_action():
    state, err = _state()
    if err:
        return err
    if competition(state.competition).system not in ("dha", "dhb_two_phase"):
        return _error("La Copa del Rey solo existe en las ligas españolas.", 400, "cup_unavailable")
    payload = request.get_json(silent=True) or request.form
    action = payload.get("action", "round")
    if action == "all":
        simulate_cup_remaining(state)
    else:
        simulate_cup_round(state, state.manual_lineup or None)
    _save(state)
    return _ok({"state": _state_payload(state)}, "Copa actualizada.")


@api.get("/ehl")
def ehl():
    state, err = _state()
    if err:
        return err
    if competition(state.competition).system not in ("dha", "dhb_two_phase"):
        return _error("La EHL se gestiona desde las ligas europeas españolas.", 400, "ehl_unavailable")
    return _ok({"ehl": state.ehl, "next": ehl_next_date(state), "status": ehl_status_text(state)})


@api.post("/ehl")
def ehl_action():
    state, err = _state()
    if err:
        return err
    if competition(state.competition).system not in ("dha", "dhb_two_phase"):
        return _error("La EHL se gestiona desde las ligas europeas españolas.", 400, "ehl_unavailable")
    if state.ehl.get("active"):
        simulate_ehl_round(state)
        _save(state)
    return _ok({"ehl": state.ehl, "next": ehl_next_date(state), "status": ehl_status_text(state), "state": _state_payload(state)}, "Ronda de EHL simulada.")


@api.get("/promotion")
def promotion():
    state, err = _state()
    if err:
        return err
    return _ok(_promotion_payload(state))


@api.get("/table")
def table():
    state, err = _state()
    if err:
        return err
    code = str(request.args.get("league") or state.competition)
    meta = competition(code)
    teams = [t for t in state.teams.values() if t.league == code]
    if not teams:
        return _error("Esa liga no está disponible.", 404, "league_not_found")
    rows = sorted(teams, key=lambda t: (-t.points, -(t.goals_for - t.goals_against), -t.goals_for, t.name))
    fixtures = state.league_fixtures.get(code, [])
    if not fixtures and code == state.competition:
        fixtures = state.fixtures
    regular = [f for f in fixtures if f.phase == "regular"]
    leagues = [
        {
            "code": item.code,
            "name": item.name,
            "short_name": item.short_name,
            "country": item.country,
            "teams": len([t for t in state.teams.values() if t.league == item.code]),
        }
        for item in COMPETITIONS.values()
        if any(t.league == item.code for t in state.teams.values())
    ]
    return _ok(
        {
            "competition": _competition(meta),
            "table": [_team_summary(t, i) for i, t in enumerate(rows, 1)],
            "fixtures": [_fixture(f, state) for f in sorted(regular, key=lambda f: (f.round, f.date))],
            "leagues": leagues,
        }
    )


# ---------------------------------------------------------------------------
# match preview / live / report
# ---------------------------------------------------------------------------


def _travel_options(state, fixture):
    user = state.user_team
    if fixture.away_id != user.id:
        return []
    home = state.teams[fixture.home_id]
    cities = load_clubs()[1]
    if competition(state.competition).international:
        cities.update(international_cities())
    return travel_options(user, home, cities, squad_size=18)


@api.get("/match")
def match_preview():
    state, err = _state()
    if err:
        return err
    web = _web()
    gid = session.get("game_id")
    if gid in web.LIVE:
        return _ok({"live": True})
    fx = state.next_user_fixture()
    if not fx:
        return _error("No hay partido pendiente.", 409, "no_match")
    home, away = state.teams[fx.home_id], state.teams[fx.away_id]
    user = state.user_team
    line, bench = make_lineup(user, state.manual_lineup or None)
    travel = _travel_options(state, fx)

    def top_scorer(t):
        return max(t.players, key=lambda p: (p.season_goals, p.overall), default=None)

    def absences(t):
        return [p for p in t.players if p.injury or p.suspension]

    return _ok(
        {
            "live": False,
            "fixture": _fixture(fx, state),
            "is_cup": fx.phase.startswith("cup_"),
            "home": _team_summary(home),
            "away": _team_summary(away),
            "line": [_player(p, user) for p in line],
            "bench": [_player(p, user) for p in bench],
            "travel": travel,
            "home_top": _player(top_scorer(home), home) if top_scorer(home) else None,
            "away_top": _player(top_scorer(away), away) if top_scorer(away) else None,
            "home_absences": [_player(p, home) for p in absences(home)],
            "away_absences": [_player(p, away) for p in absences(away)],
            "home_form": web.team_form(state, home.id),
            "away_form": web.team_form(state, away.id),
            "slot_rows": _slot_rows(web.lineup_rows(user, line)),
            "press_context": press_context(state),
        }
    )


def _live_payload(state, ctx):
    engine = ctx.engine
    events = [
        e
        for e in engine.events
        if e.get("type")
        in (
            "goal",
            "pc",
            "stroke",
            "save",
            "card",
            "card_return",
            "injury",
            "substitution",
            "chance",
            "circle_entry",
            "talk",
            "tactic",
            "review",
            "goal_disallowed",
            "advantage",
            "dangerous_play",
            "distance_5m",
            "pc_decision",
            "protest",
            "unsportsmanlike",
            "added_time",
        )
    ]
    user_side = ctx.user_side
    home = state.teams[ctx.fixture.home_id]
    away = state.teams[ctx.fixture.away_id]
    return {
        "fixture": _fixture(ctx.fixture, state),
        "user_side": user_side,
        "home": _team_summary(home),
        "away": _team_summary(away),
        "score": list(engine.score),
        "quarter": engine.quarter,
        "minute": engine.minute,
        "finished": engine.finished,
        "stats": {"home": engine.stats[0], "away": engine.stats[1]},
        "events": events[-60:],
        "line": [_player(p, state.user_team) for p in engine._field_lineup(user_side)],
        "bench": [_player(p, state.user_team) for p in engine._bench(user_side)],
        "player_rows": engine.player_live_rows(user_side),
        "bench_rows": engine.bench_live_rows(user_side),
        "tactics": state.user_team.tactics.to_dict(),
        "travel": ctx.travel,
        "snapshot": engine.live_snapshot(),
        "subs_left": max(0, 5 - engine._subs[user_side]),
        "referrals": [engine.referrals.get(0, 0), engine.referrals.get(1, 0)],
        "last_decision": engine.last_decision,
        "reviews": engine.reviews,
    }


@api.post("/match/live/start")
def match_live_start():
    state, err = _state()
    if err:
        return err
    web = _web()
    gid = session.get("game_id")
    if gid in web.LIVE:
        return _ok(_live_payload(state, web.LIVE[gid]))
    next_fixture = state.next_user_fixture()
    if next_fixture and next_fixture.phase.startswith("cup_"):
        return _error("La Copa del Rey se juega en simulación rápida.", 400, "cup_quick_only")
    payload = request.get_json(silent=True) or request.form
    travel_id = payload.get("travel") or None
    try:
        ctx = prepare_live_round(state, state.manual_lineup or None, travel_id)
    except Exception as exc:
        return _error(f"No se pudo iniciar el directo: {exc}", 409, "live_start_failed")
    web.LIVE[gid] = ctx
    return _ok(_live_payload(state, ctx), "Partido en directo iniciado.")


@api.get("/match/live")
def match_live():
    state, err = _state()
    if err:
        return err
    web = _web()
    ctx = web.LIVE.get(session.get("game_id"))
    if not ctx:
        return _error("No hay partido en directo.", 409, "no_live")
    return _ok(_live_payload(state, ctx))


@api.post("/match/live/advance")
def match_live_advance():
    state, err = _state()
    if err:
        return err
    web = _web()
    ctx = web.LIVE.get(session.get("game_id"))
    if not ctx:
        return _error("No hay partido en directo.", 409, "no_live")
    payload = request.get_json(silent=True) or request.form
    mode = payload.get("mode", "quarter")
    engine = ctx.engine
    if mode == "moment":
        engine.advance_moment()
    elif mode == "rest":
        while not engine.finished:
            engine.advance_quarter()
    else:
        engine.advance_quarter()
    return _ok(_live_payload(state, ctx))


@api.post("/match/live/tactics")
def match_live_tactics():
    state, err = _state()
    if err:
        return err
    web = _web()
    ctx = web.LIVE.get(session.get("game_id"))
    if not ctx:
        return _error("No hay partido en directo.", 409, "no_live")
    payload = request.get_json(silent=True) or request.form
    for field in ("mentality", "press", "block", "width", "tempo", "passing", "pc_routine"):
        value = payload.get(field)
        if value:
            setattr(state.user_team.tactics, field, value)
    return _ok(_live_payload(state, ctx), "Táctica actualizada.")


@api.post("/match/live/sub")
def match_live_sub():
    state, err = _state()
    if err:
        return err
    web = _web()
    ctx = web.LIVE.get(session.get("game_id"))
    if not ctx:
        return _error("No hay partido en directo.", 409, "no_live")
    payload = request.get_json(silent=True) or request.form
    ok, message = ctx.engine.manual_substitute(ctx.user_side, payload.get("out_id", ""), payload.get("in_id", ""), coaching=True)
    if not ok:
        return _error(message, 409, "sub_failed")
    return _ok(_live_payload(state, ctx), message)


@api.post("/match/live/review")
def match_live_review():
    state, err = _state()
    if err:
        return err
    web = _web()
    ctx = web.LIVE.get(session.get("game_id"))
    if not ctx:
        return _error("No hay partido en directo.", 409, "no_live")
    payload = request.get_json(silent=True) or request.form
    decision = str(payload.get("decision", "") or "")
    result = ctx.engine.review_decision(ctx.user_side, decision)
    if not result.get("ok"):
        return _error(result.get("message", "No se pudo revisar la decisión."), 409, "review_failed")
    return _ok(_live_payload(state, ctx), result.get("message", "Revisión completada."))


@api.post("/match/live/finish")
def match_live_finish():
    state, err = _state()
    if err:
        return err
    web = _web()
    ctx = web.LIVE.get(session.get("game_id"))
    if not ctx:
        return _error("No hay partido en directo.", 409, "no_live")
    if not ctx.engine.finished:
        ctx.engine.simulate()
    payload = finish_live_round(state, ctx)
    web.LIVE.pop(session.get("game_id"), None)
    _save(state)
    return _ok({"report": payload, "state": _state_payload(state)}, "Partido finalizado.")


@api.post("/match/quick")
def match_quick():
    state, err = _state()
    if err:
        return err
    payload = request.get_json(silent=True) or request.form
    travel_id = payload.get("travel") or None
    next_fixture = state.next_user_fixture()
    if next_fixture and next_fixture.phase.startswith("cup_"):
        result = simulate_cup_round(state, state.manual_lineup or None)
        if result:
            state.date = (date.fromisoformat(next_fixture.date) + timedelta(days=1)).isoformat()
            _save(state)
            return _ok({"report": state.last_result, "state": _state_payload(state)}, "Eliminatoria de Copa simulada.")
        return _error("No se pudo simular la eliminatoria de Copa.", 409, "cup_sim_failed")
    result = play_round(state, state.manual_lineup or None, travel_id)
    if not result:
        return _error("No se pudo simular el partido.", 409, "match_sim_failed")
    _save(state)
    return _ok({"report": result, "state": _state_payload(state)}, "Partido simulado.")


@api.get("/match/report")
def match_report():
    state, err = _state()
    if err:
        return err
    if not state.last_result:
        return _error("No hay parte de partido.", 404, "no_report")
    return _ok({"report": state.last_result, "state": _state_payload(state)})


# ---------------------------------------------------------------------------
# season / options
# ---------------------------------------------------------------------------


@api.get("/season/end")
def season_end():
    state, err = _state()
    if err:
        return err
    if state.phase != "season_end":
        return _error("La temporada todavía no ha terminado.", 409, "season_active")
    return _ok({"summary": season_summary(state), "state": _state_payload(state)})


@api.post("/season/continue")
def season_continue():
    state, err = _state()
    if err:
        return err
    if state.phase != "season_end":
        return _error("La temporada todavía no ha terminado.", 409, "season_active")
    advance_to_next_season(state)
    _save(state)
    return _ok(_state_payload(state), f"Nueva temporada: {state.season} · {state.competition}.")


@api.get("/options")
def get_options():
    web = _web()
    return _ok({"prefs": web.ui_prefs()})


@api.post("/options")
def set_options():
    web = _web()
    payload = request.get_json(silent=True) or request.form
    if payload.get("reset"):
        session.pop("ui_prefs", None)
        return _ok({"prefs": web.ui_prefs()}, "Opciones restablecidas.")
    session["ui_prefs"] = {
        "text_size": "large" if payload.get("text_size") == "large" else "normal",
        "compact": bool(payload.get("compact")),
        "confirm_exit": bool(payload.get("confirm_exit")),
    }
    return _ok({"prefs": web.ui_prefs()}, "Opciones guardadas.")
