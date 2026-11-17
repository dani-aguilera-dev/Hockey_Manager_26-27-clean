"""Helpers compartidos por los blueprints de la API."""

from __future__ import annotations

import uuid

from flask import jsonify, session
from src.commercial import commercial_summary
from src.competitions import COMPETITIONS, competition, playable_competitions
from src.conversations import conversation_targets
from src.cup import cup_next_user_fixture, cup_round_fixtures, cup_status_text
from src.data_loader import load_clubs
from src.ehl import ehl_next_date, ehl_status_text
from src.events import event_history as game_event_history
from src.events import pending_events as pending_game_events
from src.finance import financial_summary
from src.friendlies import friendlies_payload
from src.international import club_catalog, international_cities, load_all_teams
from src.logistics import travel_options
from src.market import STAFF_LABELS, asking_price, market_window, market_window_text, scout_range
from src.models import FORMATION_SLOTS
from src.news import awards_for_last_match, news_feed
from src.objectives import competition_objectives
from src.persistence import list_saves
from src.press import post_press_available
from src.promotion import promotion_path
from src.ratings import league_label, stars_bar, stars_text, tier
from src.season import make_lineup, new_game, season_summary


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
        "manager_name": t.manager_name,
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
            "user_sacked": state.user_sacked,
            "user_sacking": state.user_sacking,
            "user_pressure": state.user_pressure,
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


def _opponent(state):
    fx = state.next_user_fixture()
    if not fx:
        return None
    oid = fx.away_id if fx.home_id == state.club_id else fx.home_id
    return state.teams.get(oid)


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


def _travel_options(state, fixture):
    user = state.user_team
    if fixture.away_id != user.id:
        return []
    home = state.teams[fixture.home_id]
    cities = load_clubs()[1]
    if competition(state.competition).international:
        cities.update(international_cities())
    return travel_options(user, home, cities, squad_size=18)


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
        "protest_used": [engine.protest_used.get(0, False), engine.protest_used.get(1, False)],
        "protest_available": not engine.protest_used.get(user_side, False),
        "last_decision": engine.last_decision,
        "reviews": engine.reviews,
    }
