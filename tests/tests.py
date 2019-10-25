# -*- coding: utf-8 -*-
import itertools
import json
import os
import sys
import time
from urllib import urlencode

import pytest
from responses import actionIndex_response
from responses import actionItems_response
from responses import actionPlay_response
from responses import actionView_seasons_response
from responses import actionView_without_seasons_response
from responses import watching_info_response_with_seasons
from responses import watching_info_response_without_seasons


cwd = os.path.dirname(os.path.abspath(__file__))
handle = 1
plugin = "plugin://video.kino.pub/{}"
pytestmark = pytest.mark.usefixtures("fake_kodi_api")
qualities = ["480p", "720p", "1080p"]
streams = ["hls", "hls2", "http"]


class FakeAddon(object):
    _settings = {
        "access_token_expire": str(int(time.time() + 1000)),
        "video_quality": "720p",
        "stream_type": "hls4",
    }

    def __init__(self, id="video.kino.pub"):
        self._id = id

    def getAddonInfo(self, info_id):
        return {"path": cwd, "id": self._id}.get(info_id)

    def getSetting(self, setting_id):
        if "show_" in setting_id:
            return "true"
        else:
            return self._settings.get(setting_id, "")

    def setSetting(self, setting_id, value):
        self._settings[setting_id] = value

    def getLocalizedString(self, id_):
        return {32000: u"Привет, мир!", 32001: u"Я тебя люблю."}.get(id_)


class FakeListItem(object):
    def __init__(self, *args, **kwargs):
        self._properties = {}

    def setProperty(self, key, value):
        self._properties[key] = value

    def getProperty(self, key):
        return self._properties["key"]


@pytest.fixture
def main():
    from addon import main

    return main


@pytest.fixture
def xbmcgui():
    from resources.lib.addonworker import xbmcgui

    return xbmcgui


@pytest.fixture
def xbmcplugin():
    from resources.lib.addonworker import xbmcplugin

    return xbmcplugin


@pytest.fixture
def xbmcaddon():
    from resources.lib.addonworker import xbmcaddon

    return xbmcaddon


@pytest.fixture
def ExtendedListItem():
    from resources.lib.addonworker import ExtendedListItem

    return ExtendedListItem


@pytest.fixture
def fake_kodi_api(mocker):
    """Mock Kodi Python API"""
    mock_xbmcaddon = mocker.Mock()
    mock_xbmcaddon.Addon.side_effect = FakeAddon
    mocker.patch.dict(
        "sys.modules",
        inputstreamhelper=mocker.Mock(),
        xbmcaddon=mock_xbmcaddon,
        xbmc=mocker.Mock(),
        xbmcplugin=mocker.Mock(),
        xbmcgui=mocker.Mock(),
        xbmcvfs=mocker.Mock(),
    )
    mocker.patch("resources.lib.addonworker.auth")


@pytest.fixture
def index(mocker):
    def side_effect(value):
        if value == "types":
            return mocker.Mock(**{"get.return_value": actionIndex_response})

    mock_KinoPubClient = mocker.Mock(side_effect=side_effect)
    mocker.patch("resources.lib.addonworker.KinoPubClient", mock_KinoPubClient)
    mocker.patch("resources.lib.addonworker.ExtendedListItem", mocker.Mock())
    mocker.patch.object(sys, "argv", [plugin.format(""), handle, ""])


def test_index(mocker, index, main, xbmcplugin, ExtendedListItem):
    from resources.lib.addonutils import build_icon_path

    main()
    expected_results = [
        (handle, plugin.format("profile"), u"Профиль", "profile", False),
        (handle, plugin.format("search?type=None"), u"Поиск", "search", False),
        (handle, plugin.format("bookmarks"), u"Закладки", "bookmarks", True),
        (handle, plugin.format("watching"), u"Я смотрю", "watching", True),
        (handle, plugin.format("watching_movies"), u"Недосмотренные", "watching_movies", True),
        (handle, plugin.format("items?type=None"), u"Последние", "new", True),
        (
            handle,
            plugin.format("items?type=None&shortcut=%2Fpopular"),
            u"Популярные",
            "popular",
            True,
        ),
        (handle, plugin.format("items?type=None&shortcut=%2Fhot"), u"Горячие", "hot", True),
        (handle, plugin.format("tv"), u"ТВ", "tv", True),
        (handle, plugin.format("collections"), u"Подборки", "collections", True),
        (handle, plugin.format("item_index?type=movie"), u"Фильмы", "movie", True),
        (handle, plugin.format("item_index?type=serial"), u"Сериалы", "serial", True),
        (handle, plugin.format("item_index?type=tvshow"), u"ТВ шоу", "tvshow", True),
        (handle, plugin.format("item_index?type=4k"), u"4K", "4k", True),
        (handle, plugin.format("item_index?type=3d"), u"3D", "3d", True),
        (handle, plugin.format("item_index?type=concert"), u"Концерты", "concert", True),
        (
            handle,
            plugin.format("item_index?type=documovie"),
            u"Документальные фильмы",
            "documovie",
            True,
        ),
        (
            handle,
            plugin.format("item_index?type=docuserial"),
            u"Документальные сериалы",
            "docuserial",
            True,
        ),
    ]
    for result in expected_results:
        handle_, link, title, icon, is_directory = result
        img = build_icon_path(icon)
        ExtendedListItem.assert_any_call(title.encode("utf-8"), iconImage=img, thumbnailImage=img)
        li = ExtendedListItem()
        xbmcplugin.addDirectoryItem.assert_any_call(handle_, link, li, is_directory)
    xbmcplugin.endOfDirectory.assert_called_once_with(handle)


@pytest.fixture(params=itertools.product(streams, qualities), ids=lambda ids: "-".join(ids))
def play(request, mocker, xbmcaddon):
    from resources.lib.data import __id__

    xbmcaddon.Addon(id=__id__).setSetting("stream_type", request.param[0])
    xbmcaddon.Addon(id=__id__).setSetting("video_quality", request.param[1])
    id_ = actionPlay_response["item"]["id"]
    title = actionPlay_response["item"]["title"].encode("utf-8")

    def side_effect(value):
        if value == "items/{}".format(id_):
            return mocker.Mock(**{"get.return_value": actionPlay_response})
        else:
            return mocker.Mock()

    mock_KinoPubClient = mocker.Mock(side_effect=side_effect)
    mock_Player = mocker.Mock(return_value=mocker.Mock(is_playing=False))
    mock_get_window_property = mocker.Mock(
        return_value={
            "title": title,
            "poster": None,
            "video_info": {"playcount": 0, "time": 0, "duration": 0},
        }
    )
    mocker.patch.object(
        sys,
        "argv",
        [plugin.format("play"), handle, "?{}".format(urlencode({"id": id_, "index": "1"}))],
    )
    mocker.patch("resources.lib.addonworker.KinoPubClient", mock_KinoPubClient)
    mocker.patch("resources.lib.addonworker.Player", mock_Player)
    mocker.patch("resources.lib.addonworker.ExtendedListItem", mocker.Mock())
    mocker.patch("resources.lib.addonworker.get_window_property", mock_get_window_property)
    return request.param


def test_play(play, main, ExtendedListItem, xbmcplugin):
    stream, video_quality = play
    main()
    title = actionPlay_response["item"]["title"].encode("utf-8")
    link = "https://example.com/{}/{}".format(stream, video_quality.rstrip("p"))
    ExtendedListItem.assert_called_with(
        title,
        path=link,
        properties={
            "id": str(actionPlay_response["item"]["id"]),
            "play_duration": 0,
            "play_resumetime": 0,
            "video_number": 1,
            "season_number": "",
            "playcount": 0,
            "imdbnumber": actionPlay_response["item"]["imdb"],
        },
        poster=None,
        subtitles=[],
    )
    li = ExtendedListItem(title, path=link)
    xbmcplugin.setResolvedUrl.assert_called_once_with(handle, True, li)


@pytest.fixture
def items(mocker):
    def side_effect(value):
        if value == "items":
            return mocker.Mock(**{"get.return_value": actionItems_response})
        if value == "watching":
            return mocker.Mock(
                **{
                    "get.return_value": {
                        "item": {"videos": [{"time": 0, "duration": 1, "status": 0}]}
                    }
                }
            )

    mock_KinoPubClient = mocker.Mock(side_effect=side_effect)
    mock_ExtendedListItem = mocker.Mock()
    mock_ExtendedListItem().getVideoInfoTag().getPlayCount.return_value = 0
    mock_ExtendedListItem().getProperty.return_value = 0
    mocker.patch("resources.lib.addonworker.KinoPubClient", mock_KinoPubClient)
    mocker.patch("resources.lib.addonworker.ExtendedListItem", mock_ExtendedListItem)
    mocker.patch.object(sys, "argv", [plugin.format("items"), handle, "?type=None"])


@pytest.mark.skip
def test_items(main, items, ExtendedListItem, xbmcplugin, mocker):
    from resources.lib.addonutils import video_info, trailer_link
    from resources.lib.addonworker import mediatype_map

    main()

    def make_info(item):
        extra_info = {"trailer": trailer_link(item), "mediatype": mediatype_map[item["type"]]}
        if item["type"] not in ["serial", "docuserial", "tvshow"]:
            extra_info.update({"time": 0, "duration": 1, "playcount": 0})
        return json.dumps(video_info(item, extra_info))

    expected_results = []
    for item in actionItems_response["items"]:
        expected_results.append(
            {
                "title": item["title"].encode("utf-8"),
                "id": item["id"],
                "poster": item["posters"]["big"],
                "video_info": make_info(item),
            }
        )
    links = [
        plugin.format("play?{}".format(urlencode(expected_results[0]))),
        plugin.format("play?{}".format(urlencode(expected_results[1]))),
        plugin.format("view_seasons?id={}".format(expected_results[2]["id"])),
        plugin.format("view_seasons?id={}".format(expected_results[3]["id"])),
        plugin.format("view_seasons?id={}".format(expected_results[4]["id"])),
    ]
    is_dirs = [False, False, True, True, True]
    for result, link, is_dir in zip(expected_results, links, is_dirs):
        ExtendedListItem.assert_any_call(
            result["title"], poster=result["poster"], properties={"id": result["id"]}
        )
        li = ExtendedListItem()
        xbmcplugin.addDirectoryItem.assert_any_call(handle, link, li, is_dir)
    xbmcplugin.endOfDirectory.assert_called_once_with(handle)


@pytest.fixture
def view(mocker):
    id_ = actionView_seasons_response["item"]["id"]

    def side_effect(value):
        if value == "items/{}".format(id_):
            return mocker.Mock(**{"get.return_value": actionView_seasons_response})
        elif value == "watching":
            return mocker.Mock(**{"get.return_value": watching_info_response_with_seasons})

    mock_KinoPubClient = mocker.Mock(side_effect=side_effect)
    mocker.patch("resources.lib.addonworker.KinoPubClient", mock_KinoPubClient)
    mocker.patch("resources.lib.addonworker.ExtendedListItem", mocker.Mock())
    return id_


@pytest.fixture
def view_seasons(mocker, view):
    mocker.patch.object(sys, "argv", [plugin.format("view_seasons"), handle, "?id={}".format(view)])


def test_view_seasons(main, view_seasons, ExtendedListItem, xbmcplugin):
    from resources.lib.addonutils import video_info

    main()
    item = actionView_seasons_response["item"]
    i = actionView_seasons_response["item"]["id"]
    seasons = actionView_seasons_response["item"]["seasons"]
    for season in seasons:
        ExtendedListItem.assert_any_call(
            "Сезон {}".format(season["number"]),
            video_info=video_info(
                item, {"season": season["number"], "playcount": -1, "mediatype": "season"}
            ),
            poster=item["posters"]["big"],
            properties={"id": item["id"]},
            addContextMenuItems=True,
        )
        link = plugin.format(
            "view_season_episodes?season_number={}&id={}".format(season["number"], i)
        )
        xbmcplugin.addDirectoryItem.assert_any_call(handle, link, ExtendedListItem(), True)
    xbmcplugin.endOfDirectory.assert_called_once_with(handle, cacheToDisc=False)


@pytest.fixture
def view_season_episodes(mocker, view, ExtendedListItem):
    id_ = actionView_seasons_response["item"]["id"]

    def side_effect(value):
        if value == "items/{}".format(id_):
            return mocker.Mock(**{"get.return_value": actionView_seasons_response})
        elif value == "watching":
            return mocker.Mock(**{"get.return_value": watching_info_response_with_seasons})

    mock_KinoPubClient = mocker.Mock(side_effect=side_effect)
    mocker.patch("resources.lib.addonworker.KinoPubClient", mock_KinoPubClient)
    mocker.patch.object(
        sys,
        "argv",
        [plugin.format("view_season_episodes"), handle, "?id={}&season_number={}".format(view, 1)],
    )
    ExtendedListItem().getVideoInfoTag().getPlayCount.return_value = 0
    ExtendedListItem().getProperty.return_value = 0


def test_view_season_episodes(request, main, view_season_episodes, ExtendedListItem, xbmcplugin):
    from resources.lib.addonutils import video_info

    main()
    item = actionView_seasons_response["item"]
    season = item["seasons"][0]
    watching_season = watching_info_response_with_seasons["item"]["seasons"][season["number"] - 1]
    i = item["id"]
    for episode in season["episodes"]:
        watching_episode = watching_season["episodes"][episode["number"] - 1]
        episode_title = "s{:02d}e{:02d}".format(season["number"], episode["number"])
        if episode["title"]:
            episode_title = "{} | {}".format(episode_title, episode["title"].encode("utf-8"))
        info = video_info(
            item,
            {
                "season": season["number"],
                "episode": episode["number"],
                "tvshowtitle": episode["title"],
                "time": watching_episode["time"],
                "duration": watching_episode["duration"],
                "playcount": watching_episode["status"],
                "mediatype": "episode",
            },
        )
        link = plugin.format("play?{}".format(urlencode({"id": i, "index": episode["number"]})))
        ExtendedListItem.assert_any_call(
            episode_title,
            thumbnailImage=episode["thumbnail"],
            poster=item["posters"]["big"],
            video_info=info,
            properties={"id": item["id"], "isPlayable": "true"},
            addContextMenuItems=True,
        )
        xbmcplugin.addDirectoryItem.assert_any_call(handle, link, ExtendedListItem(), False)
    xbmcplugin.setContent.assert_called_once_with(handle, "episodes")
    xbmcplugin.endOfDirectory.assert_called_once_with(handle, cacheToDisc=False)


@pytest.fixture
def view_episodes(mocker, xbmcgui):
    id_ = actionView_without_seasons_response["item"]["id"]

    def side_effect(value):
        if value == "items/{}".format(id_):
            return mocker.Mock(**{"get.return_value": actionView_without_seasons_response})
        elif value == "watching":
            return mocker.Mock(**{"get.return_value": watching_info_response_without_seasons})

    mock_KinoPubClient = mocker.Mock(side_effect=side_effect)
    mock_ExtendedListItem = mocker.Mock()
    mocker.patch("resources.lib.addonworker.KinoPubClient", mock_KinoPubClient)
    mocker.patch("resources.lib.addonworker.ExtendedListItem", mock_ExtendedListItem)
    mock_ExtendedListItem().getVideoInfoTag().getPlayCount.return_value = 0
    mock_ExtendedListItem().getProperty.return_value = 0
    mocker.patch.object(
        sys, "argv", [plugin.format("view_episodes"), handle, "?{}".format(urlencode({"id": id_}))]
    )


def test_view_episodes(request, main, view_episodes, ExtendedListItem, xbmcplugin):
    from resources.lib.addonutils import video_info

    main()
    item = actionView_without_seasons_response["item"]
    watching_info = watching_info_response_without_seasons["item"]
    for video in item["videos"]:
        watching_episode = watching_info["videos"][video["number"] - 1]
        episode_title = "e{:02d}".format(video["number"])
        if video["title"]:
            episode_title = "{} | {}".format(episode_title, video["title"].encode("utf-8"))
        info = video_info(
            item,
            {
                "episode": video["number"],
                "tvshowtitle": video["title"],
                "playcount": video["watched"],
                "time": watching_episode["time"],
                "duration": watching_episode["duration"],
                "mediatype": "episode",
            },
        )
        link = plugin.format(
            "play?{}".format(urlencode({"id": item["id"], "index": video["number"]}))
        )
        ExtendedListItem.assert_any_call(
            episode_title,
            thumbnailImage=video["thumbnail"],
            video_info=info,
            poster=item["posters"]["big"],
            properties={"id": item["id"], "isPlayable": "true"},
            addContextMenuItems=True,
        )
        xbmcplugin.addDirectoryItem.assert_any_call(handle, link, ExtendedListItem(), False)
    xbmcplugin.setContent.assert_called_once_with(handle, "episodes")
    xbmcplugin.endOfDirectory.assert_called_once_with(handle, cacheToDisc=False)
