import pathlib
import sys
from copy import copy
from unittest.mock import MagicMock

import pytest

RESOURCES = (pathlib.Path(".").parent / "src").absolute()


@pytest.fixture
def utils_mod(monkeypatch):
    orig_sys_path = copy(sys.path)
    sys.path.append(str(RESOURCES))
    for name in ("xbmc", "xbmcgui", "xbmcaddon"):
        monkeypatch.setitem(sys.modules, name, MagicMock())
    sys.modules.pop("resources.lib.utils", None)
    from resources.lib import utils

    yield utils
    sys.path = orig_sys_path


def test_natural_sort_orders_qualities_numerically(utils_mod):
    assert utils_mod.natural_sort(["1080p", "360p", "720p", "480p"]) == [
        "360p",
        "480p",
        "720p",
        "1080p",
    ]


def test_natural_sort_is_case_insensitive(utils_mod):
    assert utils_mod.natural_sort(["B", "a", "C"]) == ["a", "B", "C"]


def test_cached_property_is_computed_once(utils_mod):
    calls = []

    class Item:
        @utils_mod.cached_property
        def value(self):
            calls.append(1)
            return 42

    item = Item()
    assert item.value == 42
    assert item.value == 42
    assert len(calls) == 1
