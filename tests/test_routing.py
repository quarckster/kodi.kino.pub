import pathlib
import sys
from copy import copy
from unittest.mock import MagicMock

import pytest


RESOURCES = (pathlib.Path(".").parent / "src").absolute()


@pytest.fixture
def routing_mod(monkeypatch):
    orig_sys_path = copy(sys.path)
    sys.path.append(str(RESOURCES))
    for name in ("xbmc", "xbmcvfs"):
        monkeypatch.setitem(sys.modules, name, MagicMock())
    sys.modules.pop("resources.lib.routing", None)
    from resources.lib import routing

    yield routing
    sys.path = orig_sys_path


def test_urlrule_match_extracts_keywords(routing_mod):
    rule = routing_mod.UrlRule("/items/<content_type>/<heading>/")
    assert rule.match("/items/movies/fresh/") == {
        "content_type": "movies",
        "heading": "fresh",
    }


def test_urlrule_match_returns_none_for_non_matching_path(routing_mod):
    rule = routing_mod.UrlRule("/items/<content_type>/")
    assert rule.match("/seasons/42/") is None


def test_urlrule_make_path_fills_keywords(routing_mod):
    rule = routing_mod.UrlRule("/season_episodes/<item_id>/<season_number>/")
    assert rule.make_path(item_id="8632", season_number="1") == "/season_episodes/8632/1/"


def test_build_url_joins_args_and_encodes_kwargs(routing_mod):
    plugin = MagicMock()
    plugin.PLUGIN_ID = "video.kino.pub"
    routing = routing_mod.Routing(plugin)

    url = routing.build_url("items", "movies", "fresh/", page=2)

    assert url == "plugin://video.kino.pub/items/movies/fresh/?page=2"


def test_route_decorator_registers_view(routing_mod):
    plugin = MagicMock()
    plugin.PLUGIN_URL = "plugin://video.kino.pub"
    routing = routing_mod.Routing(plugin)

    @routing.route("/seasons/<item_id>/")
    def seasons(item_id):
        return item_id

    assert routing.route_for("plugin://video.kino.pub/seasons/42/") is seasons


def test_dispatch_calls_matching_view(routing_mod):
    plugin = MagicMock()
    routing = routing_mod.Routing(plugin)
    called = {}

    @routing.route("/play/<item_id>")
    def play(item_id):
        called["item_id"] = item_id

    routing.dispatch("/play/777")
    assert called == {"item_id": "777"}


def test_dispatch_unknown_path_raises(routing_mod):
    plugin = MagicMock()
    routing = routing_mod.Routing(plugin)
    with pytest.raises(routing_mod.RoutingException):
        routing.dispatch("/does/not/exist/")
