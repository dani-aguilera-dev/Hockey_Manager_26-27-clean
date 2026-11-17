"""Composición de la API: helpers compartidos y blueprints por dominio."""

from __future__ import annotations

from flask import Flask
from web.api.career import api as career_api
from web.api.club import api as club_api
from web.api.common import _promotion_payload, _state_payload
from web.api.core import api as core_api
from web.api.market import api as market_api
from web.api.match import api as match_api
from web.api.press import api as press_api

BLUEPRINTS = [
    career_api,
    club_api,
    core_api,
    market_api,
    match_api,
    press_api,
]


def register_api(app: Flask) -> None:
    """Registra todos los blueprints de la API en la app Flask."""
    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)


__all__ = ["BLUEPRINTS", "register_api", "_promotion_payload", "_state_payload"]
