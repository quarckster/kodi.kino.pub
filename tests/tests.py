# -*- coding: utf-8 -*-
import itertools
import json
import os
import sys
import pytest
import time
from urllib import urlencode

from responses import (actionIndex_response, actionItems_response, actionPlay_response,
                       actionView_seasons_response, actionView_without_seasons_response,
                       watching_info_response_with_seasons, watching_info_response_without_seasons)


cwd = os.path.dirname(os.path.abspath(__file__))
handle = 1
plugin = "plugin://video.kino.pub/{}"
pytestmark = pytest.mark.usefixtures("fake_kodi_api")
qualities = ["480p", "720p", "1080p"]
streams = ["hls", "hls4", "http"]


class FakeAddon(object):
    def __init__(self, id="video.kino.pub"):
        self._id = id
        self._settings = {
            "access_token_expire": str(int(time.time() + 1000)),
            "video_quality": "720p",
            "stream_type": "hls4"
        }

    def getAddonInfo(self, info_id):
        return {"path": cwd, "id": self._id}.get(info_id)

    def getSetting(self, setting_id):
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
    from default import main
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
def settings():
    from resources.lib.data import __settings__
    return __settings__


@pytest.fixture
def fake_kodi_api(mocker):
    """Mock Kodi Python API"""
    mock_xbmcaddon = mocker.Mock()
    mock_xbmcaddon.Addon.side_effect = FakeAddon
    mocker.patch.dict("sys.modules", xbmcaddon=mock_xbmcaddon, xbmc=mocker.Mock(),
                      xbmcplugin=mocker.Mock(), xbmcgui=mocker.Mock())
    mocker.patch("resources.lib.addonworker.auth")


@pytest.fixture
def index(mocker):

    def side_effect(value):
        if value == "types":
            return mocker.Mock(**{"get.return_value": actionIndex_response})

    mock_KinoPubClient = mocker.Mock(side_effect=side_effect)
    mocker.patch("resources.lib.addonworker.KinoPubClient", mock_KinoPubClient)
    mocker.patch.object(sys, "argv", [plugin.format(""), handle, ""])


def test_index(mocker, index, main, xbmcplugin, xbmcgui):
    main()
    c = u"[COLOR FFFFF000]{}[/COLOR]"
    expected_results = [
        (handle, plugin.format("search?type=None"), c.format(u"Поиск"), False),
        (handle, plugin.format("items?type=None"), c.format(u"Последние"), True),
        (handle, plugin.format("items?type=None&shortcut=%2Fpopular"), c.format(u"Популярные"),
            True),
        (handle, plugin.format("items?type=None&shortcut=%2Fhot"), c.format(u"Популярные"), True),
        (handle, plugin.format("tv"), c.format(u"ТВ"), True),
        (handle, plugin.format("bookmarks"), c.format(u"Закладки"), True),
        (handle, plugin.format("watching"), c.format(u"Я смотрю"), True),
        (handle, plugin.format("collections"), c.format(u"Подборки"), True),
        (handle, plugin.format("item_index?type=movie"), u"Фильмы", True),
        (handle, plugin.format("item_index?type=serial"), u"Сериалы", True),
        (handle, plugin.format("item_index?type=tvshow"), u"ТВ шоу", True),
        (handle, plugin.format("item_index?type=4k"), u"4K", True),
        (handle, plugin.format("item_index?type=3d"), u"3D", True),
        (handle, plugin.format("item_index?type=concert"), u"Концерты", True),
        (handle, plugin.format("item_index?type=documovie"), u"Документальные фильмы", True),
        (handle, plugin.format("item_index?type=docuserial"), u"Документальные сериалы", True)
    ]
    for result in expected_results:
        handle_, link, title, is_directory = result
        xbmcgui.ListItem.assert_any_call(title.encode("utf-8"))
        li = xbmcgui.ListItem()
        xbmcplugin.addDirectoryItem.assert_any_call(handle_, link, li, is_directory)
    xbmcplugin.endOfDirectory.assert_called_once_with(handle)


@pytest.fixture(params=itertools.product(streams, qualities), ids=lambda ids: "-".join(ids))
def play(request, mocker, settings):
    settings.setSetting("stream_type", request.param[0])
    settings.setSetting("video_quality", request.param[1])
    id_ = actionPlay_response["item"]["id"]
    title = actionPlay_response["item"]["title"].encode("utf-8")

    def side_effect(value):
        if value == "items/{}".format(id_):
            return mocker.Mock(**{"get.return_value": actionPlay_response})
        else:
            return mocker.Mock()

    mock_KinoPubClient = mocker.Mock(side_effect=side_effect)
    mock_Player = mocker.Mock(return_value=mocker.Mock(is_playing=False))
    mocker.patch.object(sys, "argv", [
        plugin.format("play"),
        handle,
        "?{}".format(urlencode({"title": title, "id": id_}))
    ])
    mocker.patch("resources.lib.addonworker.KinoPubClient", mock_KinoPubClient)
    mocker.patch("resources.lib.addonworker.Player", mock_Player)
    return request.param


def test_play(play, main, xbmcgui, xbmcplugin):
    stream, video_quality = play
    main()
    title = actionPlay_response["item"]["title"].encode("utf-8")
    link = "https://example.com/{}/{}".format(stream, video_quality.rstrip("p"))
    xbmcgui.ListItem.assert_called_with(title, path=link)
    li = xbmcgui.ListItem(title, path=link)
    xbmcplugin.setResolvedUrl.assert_called_once_with(handle, True, li)


@pytest.fixture
def items(mocker, xbmcgui):

    def side_effect(value):
        if value == "items":
            return mocker.Mock(**{"get.return_value": actionItems_response})
        if value == "watching":
            return mocker.Mock(**{"get.return_value": {"item": {"status": 0}}})

    mock_KinoPubClient = mocker.Mock(side_effect=side_effect)
    xbmcgui.ListItem().getVideoInfoTag().getPlayCount.return_value = 0
    xbmcgui.ListItem().getProperty.return_value = 0
    mocker.patch("resources.lib.addonworker.KinoPubClient", mock_KinoPubClient)
    mocker.patch.object(sys, "argv", [plugin.format("items"), handle, "?type=None"])


def test_items(main, items, xbmcgui, xbmcplugin, mocker):
    from resources.lib.addonutils import video_info, trailer_link
    from resources.lib.addonworker import mediatype_map
    main()
    s = plugin
    i = [item["id"] for item in actionItems_response["items"]]
    t = [item["title"].encode("utf-8") for item in actionItems_response["items"]]
    arts = [item["posters"]["big"] for item in actionItems_response["items"]]

    def make_info(item):
        extra_info = {"trailer": trailer_link(item), "mediatype": mediatype_map[item["type"]]}
        return video_info(item, extra_info)

    info = [make_info(item) for item in actionItems_response["items"]]

    expected_results = [
        (handle, s.format("play?{}".format(
            urlencode({"id": i[0], "title": t[0], "info": info[0], "art": arts[0]}))), t[0], False),
        (handle, s.format("play?{}".format(
            urlencode({"id": i[1], "title": t[1], "info": info[1], "art": arts[1]}))), t[1], False),
        (handle, s.format("view_seasons?id={}".format(i[2])), t[2], True),
        (handle, s.format("view_seasons?id={}".format(i[3])), t[3], True),
        (handle, s.format("view_seasons?id={}".format(i[4])), t[4], True)
    ]
    for result in expected_results:
        handle_, link, title, is_directory = result
        xbmcgui.ListItem.assert_any_call(title)
        li = xbmcgui.ListItem()
        xbmcplugin.addDirectoryItem.assert_any_call(handle_, link, li, is_directory)
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
    return id_


@pytest.fixture
def view_seasons(mocker, view):
    mocker.patch.object(sys, "argv", [plugin.format("view_seasons"), handle, "?id={}".format(view)])


def test_view_seasons(main, view_seasons, xbmcgui, xbmcplugin):
    main()
    i = actionView_seasons_response["item"]["id"]
    seasons = actionView_seasons_response["item"]["seasons"]
    for season in seasons:
        xbmcgui.ListItem.assert_any_call("Сезон {}".format(season["number"]))
        link = plugin.format("view_season_episodes?season_number={}&id={}".format(
                             season["number"], i))
        xbmcplugin.addDirectoryItem.assert_any_call(handle, link, xbmcgui.ListItem(), True)
    xbmcplugin.endOfDirectory.assert_called_once_with(handle)


@pytest.fixture
def view_episodes(mocker, view, xbmcgui):
    mocker.patch.object(sys, "argv", [
        plugin.format("view_season_episodes"),
        handle,
        "?id={}&season_number={}".format(view, 1)
    ])
    xbmcgui.ListItem().getVideoInfoTag().getPlayCount.return_value = 0
    xbmcgui.ListItem().getProperty.return_value = 0


def test_view_episodes(request, main, view_episodes, xbmcgui, xbmcplugin):
    from resources.lib.addonutils import video_info
    main()
    item = actionView_seasons_response["item"]
    i = item["id"]
    season = item["seasons"][0]
    for episode in season["episodes"]:
        episode_title = "s{:02d}e{:02d}".format(season["number"], episode["number"])
        if episode["title"]:
            episode_title = "{} | {}".format(
                episode_title, episode["title"].encode("utf-8"))
        info = video_info(item, {
            "season": season["number"],
            "episode": episode["number"],
            "duration": episode["duration"],
            "playcount": episode["watched"],
            "mediatype": "episode"
        })
        link = plugin.format("play?{}".format(urlencode({
            "id": i,
            "title": episode_title,
            "season_number": season["number"],
            "episode_number": episode["number"],
            "video_data": json.dumps(episode),
            "info": info,
            "art": item["posters"]["big"]
        })))
        xbmcgui.ListItem.assert_any_call(episode_title, thumbnailImage=episode["thumbnail"])
        li = xbmcgui.ListItem()
        li.setArt.assert_called_once_with({"poster": item["posters"]["big"]})
        xbmcplugin.addDirectoryItem.assert_any_call(handle, link, xbmcgui.ListItem(), False)
    xbmcplugin.setContent.assert_called_once_with(handle, "episodes")
    xbmcplugin.endOfDirectory.assert_called_once_with(handle)


@pytest.fixture
def view_standalone_episodes(mocker, xbmcgui):
    id_ = actionView_without_seasons_response["item"]["id"]

    def side_effect(value):
        if value == "items/{}".format(id_):
            return mocker.Mock(**{"get.return_value": actionView_without_seasons_response})
        elif value == "watching":
            return mocker.Mock(**{"get.return_value": watching_info_response_without_seasons})

    mock_KinoPubClient = mocker.Mock(side_effect=side_effect)
    mocker.patch("resources.lib.addonworker.KinoPubClient", mock_KinoPubClient)
    xbmcgui.ListItem().getVideoInfoTag().getPlayCount.return_value = 0
    xbmcgui.ListItem().getProperty.return_value = 0
    mocker.patch.object(sys, "argv", [
        plugin.format("view_episodes"),
        handle,
        "?{}".format(urlencode({"id": id_}))
    ])


def test_view_standalone_episodes(request, main, view_standalone_episodes, xbmcgui, xbmcplugin):
    from resources.lib.addonutils import video_info
    main()
    item = actionView_without_seasons_response["item"]
    for video in item["videos"]:
        episode_title = "e{:02d}".format(video["number"])
        if video["title"]:
            episode_title = "{} | {}".format(episode_title, video["title"].encode("utf-8"))
        info = video_info(item, {
            "season": 1,
            "episode": video["number"],
            "playcount": video["watched"],
            "mediatype": "episode"
        })
        link = plugin.format("play?{}".format(urlencode({
            "id": item["id"],
            "title": episode_title,
            "episode_number": video["number"],
            "video_data": json.dumps(video),
            "info": info,
            "art": item["posters"]["big"]
        })))
        xbmcgui.ListItem.assert_any_call(episode_title, thumbnailImage=video["thumbnail"])
        li = xbmcgui.ListItem()
        li.setArt.assert_any_call({"poster": item["posters"]["big"]})
        xbmcplugin.addDirectoryItem.assert_any_call(handle, link, xbmcgui.ListItem(), False)
    xbmcplugin.setContent.assert_called_once_with(handle, "episodes")
    xbmcplugin.endOfDirectory.assert_called_once_with(handle)
