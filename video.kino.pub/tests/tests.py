# -*- coding: utf-8 -*-
import itertools
import json
import os
import sys
import pytest
import time
from urllib import urlencode

from responses import (actionIndex_response, actionItems_response, actionPlay_response,
                       actionView_seasons_response, actionView_without_seasons_response)


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


@pytest.fixture(params=["seasons_view", "episodes_in_season_view", "standalone_episodes_view"])
def actionView_seasons_view(mocker):
    mock_KinoPubClient = mocker.Mock()
    mock_KinoPubClient("watching").get.side_effect = mocker.Mock()
    if request.param == "seasons_view":
        id_ = actionView_seasons_response["item"]["id"]
        mock_KinoPubClient("items/{}".format(id_)).get = mocker.Mock(
            return_value=actionView_seasons_response)
        mocker.patch.object(sys, "argv", [plugin.format("view"), handle, "?id={}".format(id_)])
    elif request.param == "episodes_in_season_view":
        id_ = actionView_seasons_response["item"]["id"]
        mock_KinoPubClient("items/{}".format(id_)).get = mocker.Mock(
            return_value=actionView_seasons_response)
        mocker.patch.object(sys, "argv", [
            plugin.format("view"),
            handle,
            "?id={}".format(id_)
        ])
    elif request.param == "standalone_episodes_view":
        id_ = actionView_without_seasons_response["item"]["id"]
        mock_KinoPubClient("items/{}".format(id_)).get = mocker.Mock(
            return_value=actionView_without_seasons_response)
        mocker.patch.object(sys, "argv", [
            plugin.format("view"),
            handle,
            "?id={}&season={}".format(id_, 1)
        ])
    mocker.patch("resources.lib.addonworker.KinoPubClient", mock_KinoPubClient)
    return request.param


@pytest.fixture
def actionItems(mocker):
    mock_KinoPubClient = mocker.Mock()
    mock_KinoPubClient("items").get = mocker.Mock(return_value=actionItems_response)
    mocker.patch("resources.lib.addonworker.KinoPubClient", mock_KinoPubClient)
    mocker.patch.object(sys, "argv", [plugin.format("items"), handle, ""])


def test_actionIndex(mocker, actionIndex, main, xbmcplugin, xbmcgui):
    main()
    c = u"[COLOR FFFFF000]{}[/COLOR]"
    expected_results = [
        (handle, plugin.format("search"), c.format(u"Поиск"), False),
        (handle, plugin.format("items"), c.format(u"Последние"), True),
        (handle, plugin.format("items?sort=-rating"), c.format(u"Популярные"), True),
        (handle, plugin.format("tv"), c.format(u"ТВ"), True),
        (handle, plugin.format("bookmarks"), c.format(u"Закладки"), True),
        (handle, plugin.format("watching"), c.format(u"Я смотрю"), True),
        (handle, plugin.format("collections"), c.format(u"Подборки"), True),
        (handle, plugin.format("index?type=movie"), u"Фильмы", True),
        (handle, plugin.format("index?type=serial"), u"Сериалы", True),
        (handle, plugin.format("index?type=tvshow"), u"ТВ шоу", True),
        (handle, plugin.format("index?type=4k"), u"4K", True),
        (handle, plugin.format("index?type=3d"), u"3D", True),
        (handle, plugin.format("index?type=concert"), u"Концерты", True),
        (handle, plugin.format("index?type=documovie"), u"Документальные фильмы", True),
        (handle, plugin.format("index?type=docuserial"), u"Документальные сериалы", True)
    ]
    for result in expected_results:
        handle_, link, title, is_directory = result
        xbmcgui.ListItem.assert_any_call(title.encode("utf-8"))
        li = xbmcgui.ListItem()
        xbmcplugin.addDirectoryItem.assert_any_call(handle_, link, li, is_directory)
    xbmcplugin.endOfDirectory.assert_called_once_with(handle)


@pytest.fixture(params=itertools.product(streams, qualities), ids=lambda ids: "-".join(ids))
def actionPlay(request, mocker, settings):
    orig_video_quality = settings.getSetting("video_quality")
    orig_stream = settings.getSetting("stream_type")
    settings.setSetting("stream_type", request.param[0])
    settings.setSetting("video_quality", request.param[1])
    mock_KinoPubClient = mocker.Mock()
    id_ = actionPlay_response["item"]["id"]
    mock_KinoPubClient("items/{}".format(id_)).get = mocker.Mock(return_value=actionPlay_response)
    mocker.patch("resources.lib.addonworker.KinoPubClient", mock_KinoPubClient)
    title = actionPlay_response["item"]["title"].encode("utf-8")
    mocker.patch.object(sys, "argv", [
        plugin.format("play"),
        handle,
        "?{}".format(urlencode({"title": title, "id": id_}))
    ])
    yield request.param
    settings.setSetting("video_quality", orig_video_quality)
    settings.setSetting("stream_type", orig_stream)


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
def actionIndex(mocker):
    mock_KinoPubClient = mocker.Mock()
    mock_KinoPubClient("types").get = mocker.Mock(return_value=actionIndex_response)
    mocker.patch("resources.lib.addonworker.KinoPubClient", mock_KinoPubClient)
    mocker.patch.object(sys, "argv", [plugin.format(""), handle, ""])


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


def test_actionView(request, main, actionView, xbmcgui, xbmcplugin):
    main()
    s = plugin
    if actionView == "seasons_view":
        i = actionView_seasons_response["item"]["id"]
        t = actionView_seasons_response["item"]["title"].encode("utf-8")
        seasons = actionView_seasons_response["item"]["seasons"]
        link = s.format("view?id={}&season={}".format(i, seasons["number"]))
        xbmcgui.ListItem.assert_any_call(t)
        xbmcplugin.addDirectoryItem.assert_any_call(handle, link, xbmcgui.ListItem(), True)
    elif actionView == "episodes_in_season_view":
        i = actionView_seasons_response["item"]["id"]
        t = actionView_seasons_response["item"]["title"].encode("utf-8")
        v = actionView_seasons_response["item"]["season"]["episodes"][0]
        link = s.format("play?".format(urlencode({
            "id": i,
            "title": "s01e01 | {}".format(v.title),
            "season": actionView_seasons_response["item"]["season"]["number"],
            "number": v["number"],
            "video": json.dumps(v)
        })))
        xbmcplugin.setContent.assert_called_once_with(handle, "episodes")
        xbmcgui.ListItem.assert_any_call(t)
        xbmcplugin.addDirectoryItem.assert_any_call(handle, link, xbmcgui.ListItem(), False)
    elif actionView == "standalone_episodes_view":
        # r = actionView_without_seasons_response
        # i = [video["id"] for video in r["item"]["video"]]
        # t = [video["title"].encode("utf-8") for video in r["item"]["videos"]]
        # expected_results = [
        #     (handle, s.format("play?{}".format(urlencode({"id": i[0], "title": t[0]}))), t[0], False),
        #     (handle, s.format("play?{}".format(urlencode({"id": i[1], "title": t[1]}))), t[1], False),
        # ]
        pass
    xbmcplugin.endOfDirectory.assert_called_once_with(handle)
