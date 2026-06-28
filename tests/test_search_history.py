import pathlib
import sys
from copy import copy
from unittest.mock import MagicMock

import pytest


RESOURCES = (pathlib.Path(".").parent / "src").absolute()


@pytest.fixture
def search_history_mod(monkeypatch):
    orig_sys_path = copy(sys.path)
    sys.path.append(str(RESOURCES))
    monkeypatch.setitem(sys.modules, "xbmcvfs", MagicMock())
    sys.modules.pop("resources.lib.search_history", None)
    from resources.lib import search_history

    yield search_history
    sys.path = orig_sys_path


def make_history(mod, max_qty="10", initial="[]"):
    plugin = MagicMock()
    plugin.settings.history_max_qty = max_qty
    fake_file = MagicMock()
    fake_file.read.return_value = initial
    mod.xbmcvfs.File.return_value = fake_file
    return mod.SearchHistory(plugin)


def test_save_inserts_at_top(search_history_mod):
    history = make_history(search_history_mod, initial='["old"]')
    history.save("new")
    assert history.items == ["new", "old"]


def test_save_moves_duplicate_to_top(search_history_mod):
    history = make_history(search_history_mod, initial='["a", "b"]')
    history.save("b")
    assert history.items == ["b", "a"]


def test_recent_is_limited_to_max_qty(search_history_mod):
    history = make_history(search_history_mod, max_qty="2", initial='["a", "b", "c"]')
    assert history.recent == ["a", "b"]


def test_clean_empties_history(search_history_mod):
    history = make_history(search_history_mod, initial='["a", "b"]')
    history.clean()
    assert history.items == []


def test_load_handles_invalid_json(search_history_mod):
    history = make_history(search_history_mod, initial="not valid json")
    assert history.items == []
