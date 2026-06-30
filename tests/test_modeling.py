import pathlib
import sys
from copy import copy
from copy import deepcopy
from unittest.mock import MagicMock

import pytest

RESOURCES = (pathlib.Path(".").parent / "src").absolute()


@pytest.fixture
def modeling_mod(monkeypatch):
    orig_sys_path = copy(sys.path)
    sys.path.append(str(RESOURCES))
    for name in ("xbmc", "xbmcgui", "xbmcaddon", "xbmcplugin", "xbmcvfs", "socks"):
        monkeypatch.setitem(sys.modules, name, MagicMock())
    for mod in list(sys.modules):
        if mod.startswith("resources.lib"):
            sys.modules.pop(mod, None)
    from resources.lib import modeling

    yield modeling
    sys.path = orig_sys_path


def _item(id_, anime=False):
    return {"id": id_, "genres": [{"id": 25 if anime else 1}]}


def _page(items, current, total, perpage=5):
    return {"items": items, "pagination": {"current": current, "total": total, "perpage": perpage}}


def _collection(modeling_mod, pages):
    """An ItemsCollection whose client returns `pages` keyed by the `page` param."""
    plugin = MagicMock()
    endpoint = MagicMock()
    # deepcopy per request: _get_anime_excluded mutates the response pagination.
    endpoint.get.side_effect = lambda data=None: deepcopy(pages[int((data or {}).get("page", 1))])
    plugin.client.return_value = endpoint
    return modeling_mod.ItemsCollection(plugin)


# Each case: pages, request data, expected item ids, expected pagination.
ANIME_EXCLUDED_CASES = [
    pytest.param(
        {1: _page([_item(i) for i in range(1, 9)], current=1, total=3)},
        {},
        [1, 2, 3, 4, 5],
        {"current": 0, "total": 3, "perpage": 5, "start_from": 5},
        id="single-page-overshoot",
    ),
    pytest.param(
        {1: _page([_item(i) for i in range(1, 6)], current=1, total=3)},
        {},
        [1, 2, 3, 4, 5],
        {"current": 0, "total": 3, "perpage": 5, "start_from": 5},
        id="exact-fill",
    ),
    pytest.param(
        {
            1: _page(
                [
                    _item(1),
                    _item(2, anime=True),
                    _item(3),
                    _item(4, anime=True),
                    _item(5),
                    _item(6),
                    _item(7),
                    _item(8),
                    _item(9),
                ],
                current=1,
                total=3,
            )
        },
        {},
        [1, 3, 5, 6, 7],
        {"current": 0, "total": 3, "perpage": 5, "start_from": 7},
        id="anime-interspersed-overshoot",
    ),
    pytest.param(
        {
            1: _page([_item(1), _item(2, anime=True), _item(3)], current=1, total=3),
            2: _page([_item(10), _item(11), _item(12), _item(13), _item(14)], current=2, total=3),
        },
        {},
        [1, 3, 10, 11, 12],
        {"current": 1, "total": 3, "perpage": 5, "start_from": 3},
        id="undershoot-then-overshoot",
    ),
    pytest.param(
        {
            1: _page([_item(1), _item(2, anime=True), _item(3)], current=1, total=3),
            2: _page([_item(10), _item(11, anime=True)], current=2, total=3),
        },
        {},
        [1, 3, 10],
        {"current": 2, "total": 3, "perpage": 5},
        id="undershoot-to-last-page-not-full",
    ),
    pytest.param(
        {1: _page([_item(i) for i in range(1, 10)], current=1, total=3)},
        {"start_from": 3},
        [4, 5, 6, 7, 8],
        {"current": 0, "total": 3, "perpage": 5, "start_from": 8},
        id="start-from-continuation",
    ),
    pytest.param(
        {
            1: _page(
                [_item(1, anime=True), _item(2, anime=True), _item(3, anime=True)],
                current=1,
                total=3,
            ),
            2: _page(
                [_item(10), _item(11), _item(12), _item(13), _item(14), _item(15)],
                current=2,
                total=3,
            ),
        },
        {},
        [10, 11, 12, 13, 14],
        {"current": 1, "total": 3, "perpage": 5, "start_from": 5},
        id="all-anime-page-then-next",
    ),
]


@pytest.mark.parametrize("pages, data, expected_ids, expected_pagination", ANIME_EXCLUDED_CASES)
def test_get_anime_excluded(modeling_mod, pages, data, expected_ids, expected_pagination):
    collection = _collection(modeling_mod, pages)
    result = collection._get_anime_excluded("items", data)
    assert [item["id"] for item in result["items"]] == expected_ids
    assert result["pagination"] == expected_pagination


def test_get_anime_excluded_does_not_mutate_caller_data(modeling_mod):
    collection = _collection(modeling_mod, {1: _page([_item(i) for i in range(1, 9)], 1, 3)})
    data = {"type": "movie", "start_from": 2}
    collection._get_anime_excluded("items", data)
    assert data == {"type": "movie", "start_from": 2}


def test_is_anime(modeling_mod):
    assert modeling_mod.ItemsCollection._is_anime(_item(1, anime=True)) is True
    assert modeling_mod.ItemsCollection._is_anime(_item(1, anime=False)) is False
    assert modeling_mod.ItemsCollection._is_anime({"genres": []}) is False
