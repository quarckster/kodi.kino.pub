import pathlib
import sys
from copy import copy
from unittest.mock import MagicMock

import pytest

RESOURCES = (pathlib.Path(".").parent / "src").absolute()

TOGGLEABLE = [
    "show_search",
    "show_sort",
    "show_tv",
    "show_collections",
    "show_movies",
    "show_serials",
    "show_tvshows",
    "show_3d",
    "show_concerts",
    "show_documovies",
    "show_docuserials",
]


@pytest.fixture
def plugin_mod(monkeypatch):
    orig_sys_path = copy(sys.path)
    sys.path.append(str(RESOURCES))
    for name in ("xbmc", "xbmcgui", "xbmcaddon", "xbmcplugin", "xbmcvfs", "socks"):
        monkeypatch.setitem(sys.modules, name, MagicMock())
    for mod in list(sys.modules):
        if mod.startswith("resources.lib"):
            sys.modules.pop(mod, None)
    from resources.lib import plugin

    yield plugin
    sys.path = orig_sys_path


def make_plugin_self(disabled=()):
    """A stand-in for a Plugin instance so _main_menu_items can be called without
    going through the heavy Plugin.__init__."""
    fake = MagicMock()
    for name in TOGGLEABLE:
        setattr(fake.settings, name, name not in disabled)
    fake.sorting_title = "By rating"
    fake.routing.build_url.side_effect = lambda *args, **kwargs: "/".join(str(a) for a in args)
    fake.routing.build_icon_path.side_effect = lambda name: name
    return fake


def test_all_menu_items_displayed_by_default(plugin_mod):
    menu = plugin_mod.Plugin._main_menu_items(make_plugin_self())
    assert menu, "menu should not be empty"
    assert all(item.is_displayed for item in menu)


def test_disabled_setting_hides_exactly_one_item(plugin_mod):
    menu = plugin_mod.Plugin._main_menu_items(make_plugin_self(disabled=["show_movies"]))
    hidden = [item for item in menu if not item.is_displayed]
    assert len(hidden) == 1
    assert hidden[0].url == "items/movies/"


def test_non_toggleable_items_stay_displayed(plugin_mod):
    # Disable every toggleable item; the always-on items (profile, bookmarks,
    # "I'm watching", watching movies) must still be displayed.
    menu = plugin_mod.Plugin._main_menu_items(make_plugin_self(disabled=TOGGLEABLE))
    displayed = [item for item in menu if item.is_displayed]
    assert len(displayed) == 4
