# -*- coding: utf-8 -*-
import os
import sys
import pytest
import time
from urllib import urlencode

from responses import actionIndex_response, actionItems_response, actionPlay_response


plugin = "plugin://video.kino.pub/{}"
pytestmark = pytest.mark.usefixtures("fake_kodi_api")
handle = 1
cwd = os.path.dirname(os.path.abspath(__file__))


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
def fake_kodi_api(mocker):
    """Mock Kodi Python API"""
    mock_xbmcaddon = mocker.Mock()
    mock_xbmcaddon.Addon = mocker.Mock(wraps=FakeAddon)
    mocker.patch.dict("sys.modules", xbmcaddon=mock_xbmcaddon, xbmc=mocker.Mock(),
                      xbmcplugin=mocker.Mock(), xbmcgui=mocker.Mock())
    mocker.patch("resources.lib.addonworker.auth")


@pytest.fixture
def actionIndex(mocker):
    mock_KinoPubClient = mocker.Mock()
    mock_KinoPubClient("types").get = mocker.Mock(return_value=actionIndex_response)
    mocker.patch("resources.lib.addonworker.KinoPubClient", mock_KinoPubClient)
    mocker.patch.object(sys, "argv", [plugin.format(""), handle, ""])


@pytest.fixture
def actionPlay(mocker):
    mock_KinoPubClient = mocker.Mock()
    mock_KinoPubClient("items/12345").get = mocker.Mock(return_value=actionPlay_response)
    mocker.patch("resources.lib.addonworker.KinoPubClient", mock_KinoPubClient)
    title = actionPlay_response["item"]["title"].encode("utf-8")
    id = actionPlay_response["item"]["id"]
    mocker.patch.object(sys, "argv", [
        plugin.format("play"),
        handle,
        "?{}".format(urlencode({"title": title, "id": id}))
    ])


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


def test_actionPlay(actionPlay, main, xbmcgui):
    main()
    title = actionPlay_response["item"]["title"].encode("utf-8")
    xbmcgui.ListItem.assert_called_with(title)
    setPath = xbmcgui.ListItem(title).setPath
    setPath.assert_called_with("https://example.com/hls4/720")


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
