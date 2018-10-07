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
def actionIndex(mocker):

    def side_effect(value):
        if value == "types":
            return mocker.Mock(**{"get.return_value": actionIndex_response})

    mock_KinoPubClient = mocker.Mock(side_effect=side_effect)
    mocker.patch("resources.lib.addonworker.KinoPubClient", mock_KinoPubClient)
    mocker.patch.object(sys, "argv", [plugin.format(""), handle, ""])


def test_actionIndex(mocker, actionIndex, main, xbmcplugin, xbmcgui):
    main()
    c = u"[COLOR FFFFF000]{}[/COLOR]"
    expected_results = [
        (handle, plugin.format("search?type=None"), c.format(u"Поиск"), False),
        (handle, plugin.format("items?type=None"), c.format(u"Последние"), True),
        (handle, plugin.format("items?sort=-rating&type=None"), c.format(u"Популярные"), True),
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
def actionPlay(request, mocker, settings):
    settings.setSetting("stream_type", request.param[0])
    settings.setSetting("video_quality", request.param[1])
    id_ = actionPlay_response["item"]["id"]

    def side_effect(value):
        if value == "items/{}".format(id_):
            return mocker.Mock(**{"get.return_value": actionPlay_response})
        else:
            return mocker.Mock()

    mock_KinoPubClient = mocker.Mock(side_effect=side_effect)
    title = actionPlay_response["item"]["title"].encode("utf-8")
    mocker.patch.object(sys, "argv", [
        plugin.format("play"),
        handle,
        "?{}".format(urlencode({"title": title, "id": id_}))
    ])
    mocker.patch("resources.lib.addonworker.KinoPubClient", mock_KinoPubClient)
    mocker.patch("resources.lib.addonworker.auth")
    return request.param


def test_actionPlay(actionPlay, main, xbmcgui, xbmcplugin):
    stream, video_quality = actionPlay
    main()
    title = actionPlay_response["item"]["title"].encode("utf-8")
    xbmcgui.ListItem.assert_called_with(title)
    li = xbmcgui.ListItem(title)
    link = "https://example.com/{}/{}".format(stream, video_quality.rstrip("p"))
    li.setPath.assert_called_once_with(link)
    xbmcplugin.setResolvedUrl.assert_called_once_with(handle, True, li)


@pytest.fixture
def actionItems(mocker):

    def side_effect(value):
        if value == "items":
            return mocker.Mock(**{"get.return_value": actionItems_response})

    mock_KinoPubClient = mocker.Mock(side_effect=side_effect)
    mocker.patch("resources.lib.addonworker.KinoPubClient", mock_KinoPubClient)
    mocker.patch.object(sys, "argv", [plugin.format("items"), handle, ""])


def test_actionItems(main, actionItems, xbmcgui, xbmcplugin):
    main()
    s = plugin
    i = [item["id"] for item in actionItems_response["items"]]
    t = [item["title"].encode("utf-8") for item in actionItems_response["items"]]
    expected_results = [
        (handle, s.format("play?{}".format(urlencode({"id": i[0], "title": t[0]}))), t[0], False),
        (handle, s.format("play?{}".format(urlencode({"id": i[1], "title": t[1]}))), t[1], False),
        (handle, s.format("view?id={}".format(i[2])), t[2], True),
        (handle, s.format("view?id={}".format(i[3])), t[3], True),
        (handle, s.format("view?id={}".format(i[4])), t[4], True)
    ]
    for result in expected_results:
        handle_, link, title, is_directory = result
        xbmcgui.ListItem.assert_any_call(title)
        li = xbmcgui.ListItem()
        xbmcplugin.addDirectoryItem.assert_any_call(handle_, link, li, is_directory)
    xbmcplugin.endOfDirectory.assert_called_once_with(handle)


@pytest.fixture
def actionView(mocker):
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
def actionView_seasons(mocker, actionView):
    mocker.patch.object(sys, "argv", [plugin.format("view"), handle, "?id={}".format(actionView)])


def test_actionView_seasons(main, actionView_seasons, xbmcgui, xbmcplugin):
    main()
    i = actionView_seasons_response["item"]["id"]
    seasons = actionView_seasons_response["item"]["seasons"]
    for season in seasons:
        xbmcgui.ListItem.assert_any_call("Сезон {}".format(season["number"]))
        link = plugin.format("view_season_episodes?season={}&id={}".format(season["number"], i))
        xbmcplugin.addDirectoryItem.assert_any_call(handle, link, xbmcgui.ListItem(), True)
    xbmcplugin.endOfDirectory.assert_called_once_with(handle)


@pytest.fixture
def actionView_episodes(mocker, actionView):
    mocker.patch.object(sys, "argv", [
        plugin.format("view_season_episodes"),
        handle,
        "?id={}&season={}".format(actionView, 1)
    ])


def test_actionView_episodes(request, main, actionView_episodes, xbmcgui, xbmcplugin):
    main()
    item = actionView_seasons_response["item"]
    i = item["id"]
    season = item["seasons"][0]
    for episode in season["episodes"]:
        episode_title = "s{:02d}e{:02d}".format(season["number"], episode["number"])
        if episode["title"]:
            episode_title = "{} | {}".format(
                episode_title, episode["title"].encode("utf-8"))
        link = plugin.format("play?{}".format(urlencode({
            "id": i,
            "title": episode_title,
            "season": season["number"],
            "number": episode["number"],
            "video": json.dumps(episode)
        })))
        xbmcgui.ListItem.assert_any_call(
            episode_title,
            iconImage=episode["thumbnail"],
            thumbnailImage=episode["thumbnail"]
        )
        li = xbmcgui.ListItem()
        li.setInfo.assert_any_call("Video", {"playcount": episode["watched"]})
        li.setArt.assert_called_once_with({"poster": item["posters"]["big"]})
        li.setProperty.assert_called_once_with("IsPlayable", "true")
        xbmcplugin.addDirectoryItem.assert_any_call(handle, link, xbmcgui.ListItem(), False)
    xbmcplugin.setContent.assert_called_once_with(handle, "episodes")
    xbmcplugin.endOfDirectory.assert_called_once_with(handle)


@pytest.fixture
def actionView_standalone_episodes(mocker):
    id_ = actionView_without_seasons_response["item"]["id"]

    def side_effect(value):
        if value == "items/{}".format(id_):
            return mocker.Mock(**{"get.return_value": actionView_without_seasons_response})
        elif value == "watching":
            return mocker.Mock(**{"get.return_value": watching_info_response_without_seasons})

    mock_KinoPubClient = mocker.Mock(side_effect=side_effect)
    mocker.patch("resources.lib.addonworker.KinoPubClient", mock_KinoPubClient)
    mocker.patch.object(sys, "argv", [
        plugin.format("view"),
        handle,
        "?{}".format(urlencode({"id": id_}))
    ])


def test_actionView_standalone_episodes(request, main, actionView_standalone_episodes, xbmcgui,
                                        xbmcplugin):
    main()
    item = actionView_without_seasons_response["item"]
    for video in item["videos"]:
        episode_title = "e{:02d}".format(video["number"])
        if video["title"]:
            episode_title = "{} | {}".format(episode_title, video["title"].encode("utf-8"))
        link = plugin.format("play?{}".format(urlencode({
            "id": item["id"],
            "title": episode_title,
            "number": video["number"],
            "video": json.dumps(video)
        })))
        xbmcgui.ListItem.assert_any_call(
            episode_title,
            iconImage=video["thumbnail"],
            thumbnailImage=video["thumbnail"]
        )
        li = xbmcgui.ListItem()
        li.setInfo.assert_any_call("Video", {"playcount": video["watched"]})
        li.setArt.assert_any_call({"poster": item["posters"]["big"]})
        li.setProperty.assert_any_call("IsPlayable", "true")
        xbmcplugin.addDirectoryItem.assert_any_call(handle, link, xbmcgui.ListItem(), False)
    xbmcplugin.setContent.assert_called_once_with(handle, "episodes")
    xbmcplugin.endOfDirectory.assert_called_once_with(handle)
