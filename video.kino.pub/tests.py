# -*- coding: utf-8 -*-
import os
import sys
import pytest
import time
from collections import defaultdict


plugin = "plugin://video.kino.pub"
pytestmark = pytest.mark.usefixtures("fake_kodi_api")
handle = 1
cwd = os.path.dirname(os.path.abspath(__file__))


class FakeAddon(object):
    def __init__(self, id="test.addon"):
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


class FakeWindow(object):
    def __init__(self, id_=-1):
        self._contents = defaultdict(str)

    def getProperty(self, key):
        return self._contents[key]

    def setProperty(self, key, value):
        self._contents[key] = value

    def clearProperty(self, key):
        del self._contents[key]


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
    mock_xbmc = mocker.MagicMock()
    mock_xbmc.LOGDEBUG = 0
    mock_xbmc.LOGNOTICE = 2
    mock_xbmcplugin = mocker.Mock()
    mock_xbmcgui = mocker.Mock()
    mock_xbmcgui
    mocker.patch.dict("sys.modules", xbmcaddon=mock_xbmcaddon, xbmc=mock_xbmc,
                      xbmcplugin=mock_xbmcplugin, xbmcgui=mock_xbmcgui)
    mocker.patch("resources.lib.addonworker.auth")


@pytest.fixture
def actionIndex(mocker):
    mock_KinoPubClient = mocker.Mock()
    mock_KinoPubClient("types").get = mocker.Mock(return_value={
        u"status": 200, u"items": [
            {u"id": u"movie", u"title": u"Фильмы"},
            {u"id": u"serial", u"title": u"Сериалы"},
            {u"id": u"tvshow", u"title": u"ТВ шоу"},
            {u"id": u"4k", u"title": u"4K"},
            {u"id": u"3d", u"title": u"3D"},
            {u"id": u"concert", u"title": u"Концерты"},
            {u"id": u"documovie", u"title": u"Документальные фильмы"},
            {u"id": u"docuserial", u"title": u"Документальные сериалы"}
        ]
    })
    mocker.patch("resources.lib.addonworker.KinoPubClient", mock_KinoPubClient)
    mocker.patch.object(sys, "argv", [plugin, handle, ""])


@pytest.fixture
def actionPlay(mocker):
    mock_KinoPubClient = mocker.Mock()
    mock_KinoPubClient("items/12345").get = mocker.Mock(return_value={
        u"status": 200,
        u"item": {
            u"videos": [
                {u"files": [
                    {u"url": {
                        u"hls": u"https://example.com/hls/480",
                        u"hls2": u"https://example.com/hls2/480",
                        u"http": u"https://example.com/http/480",
                        u"hls4": u"https://example.com/hls4/480"
                    }, u"h": 306, u"quality": u"480p", u"w": 720},
                    {u"url": {
                        u"hls": u"https://example.com/hls/720",
                        u"hls2": u"https://example.com/hls2/720",
                        u"http": u"https://example.com/http/720",
                        u"hls4": u"https://example.com/hls4/720"
                    }, u"h": 544, u"quality": u"720p", u"w": 1280}
                ],
                    u"subtitles": [{u"url": ""}],
                    u"number": 1
                }
            ],
        }
    })
    mocker.patch("resources.lib.addonworker.KinoPubClient", mock_KinoPubClient)
    mocker.patch.object(sys, "argv", [
        "{}/play".format(plugin),
        handle,
        "?id=12345&title=%D0%9A%D0%B0%D0%B1%D0%B0%D0%BD+%2F+Boar"
    ])


def test_actionIndex(mocker, actionIndex, main, xbmcplugin, xbmcgui):
    main()
    s = "plugin://video.kino.pub/{}"
    c = u"[COLOR FFFFF000]{}[/COLOR]"
    expected_results = [
        (handle, s.format("search"), c.format(u"Поиск"), False),
        (handle, s.format("items"), c.format(u"Последние"), True),
        (handle, s.format("items?sort=-rating"), c.format(u"Популярные"), True),
        (handle, s.format("tv"), c.format(u"ТВ"), True),
        (handle, s.format("bookmarks"), c.format(u"Закладки"), True),
        (handle, s.format("watching"), c.format(u"Я смотрю"), True),
        (handle, s.format("collections"), c.format(u"Подборки"), True),
        (handle, s.format("index?type=movie"), u"Фильмы", True),
        (handle, s.format("index?type=serial"), u"Сериалы", True),
        (handle, s.format("index?type=tvshow"), u"ТВ шоу", True),
        (handle, s.format("index?type=4k"), u"4K", True),
        (handle, s.format("index?type=3d"), u"3D", True),
        (handle, s.format("index?type=concert"), u"Концерты", True),
        (handle, s.format("index?type=documovie"), u"Документальные фильмы", True),
        (handle, s.format("index?type=docuserial"), u"Документальные сериалы", True)
    ]
    directory_items = xbmcplugin.addDirectoryItem.call_args_list
    list_items = xbmcgui.ListItem.call_args_list
    for result, dir_item, list_item in zip(expected_results, directory_items, list_items):
        handle_, link, title, is_directory = result
        list_item.assert_called_with(title.encode("utf-8"))
        dir_item.assert_called_with(handle_, link, list_item, is_directory)


def test_actionPlay(actionPlay, main, xbmcgui):
    main()
    title = xbmcgui.ListItem.call_args[0][0]
    xbmcgui.ListItem.assert_called_with(u"Кабан / Boar".encode("utf-8"))
    setPath = xbmcgui.ListItem(title).setPath
    setPath.assert_called_with("https://example.com/hls4/720")
