# -*- coding: utf-8 -*-
from __future__ import absolute_import

import sys
from collections import namedtuple
from urlparse import parse_qsl
from urlparse import urlsplit

import xbmcaddon

from resources.lib.auth import Auth
from resources.lib.client import KinoPubClient
from resources.lib.listitem import ExtendedListItem
from resources.lib.logger import Logger
from resources.lib.routing import Routing
from resources.lib.settings import Settings


MainMenuItem = namedtuple("MainMenuItem", ["title", "url", "icon", "is_dir", "is_displayed"])


class Plugin(object):
    PLUGIN_ID = xbmcaddon.Addon().getAddonInfo("id")
    PLUGIN_URL = "plugin://{}".format(PLUGIN_ID)
    settings = Settings()

    def __init__(self):
        self._rules = {}
        self.path = urlsplit(sys.argv[0]).path or "/"
        self.handle = int(sys.argv[1])
        self.kwargs = dict(parse_qsl(sys.argv[2].lstrip("?")))
        self.auth = Auth(self)
        self.logger = Logger(self)
        self.routing = Routing(self)
        self.main_menu_items = self._main_menu_items()

    def client(self, endpoint):
        return KinoPubClient(self, endpoint)

    def list_item(
        self,
        name,
        label2="",
        iconImage="",
        thumbnailImage="",
        path="",
        poster=None,
        video_info=None,
        properties=None,
        addContextMenuItems=False,
        subtitles=None,
    ):
        return ExtendedListItem(
            name,
            label2=label2,
            iconImage=iconImage,
            thumbnailImage=thumbnailImage,
            path=path,
            poster=poster,
            video_info=video_info,
            properties=properties,
            addContextMenuItems=addContextMenuItems,
            subtitles=subtitles,
            plugin=self,
        )

    def run(self):
        self.routing.dispatch(self.path)

    def _main_menu_items(self):
        return [
            MainMenuItem(
                "Поиск",
                self.routing.build_url("search", content_type=None),
                self.routing.build_icon_path("search"),
                False,
                eval(self.settings.show_search.title()),
            ),
            MainMenuItem(
                "Закладки",
                self.routing.build_url("bookmarks"),
                self.routing.build_icon_path("bookmarks"),
                True,
                True,
            ),
            MainMenuItem(
                "Я смотрю",
                self.routing.build_url("watching"),
                self.routing.build_icon_path("watching"),
                True,
                True,
            ),
            MainMenuItem(
                "Недосмотренные",
                self.routing.build_url("watching_movies"),
                self.routing.build_icon_path("watching_movies"),
                True,
                True,
            ),
            MainMenuItem(
                "Последние",
                self.routing.build_url("items", shortcut="/fresh", content_type=None),
                self.routing.build_icon_path("new"),
                True,
                eval(self.settings.show_last.title()),
            ),
            MainMenuItem(
                "Популярные",
                self.routing.build_url("items", shortcut="/popular", content_type=None),
                self.routing.build_icon_path("popular"),
                True,
                eval(self.settings.show_popular.title()),
            ),
            MainMenuItem(
                "Горячие",
                self.routing.build_url("items", shortcut="/hot", content_type=None),
                self.routing.build_icon_path("hot"),
                True,
                eval(self.settings.show_hot.title()),
            ),
            MainMenuItem(
                "ТВ",
                self.routing.build_url("tv"),
                self.routing.build_icon_path("tv"),
                True,
                eval(self.settings.show_tv.title()),
            ),
            MainMenuItem(
                "Подборки",
                self.routing.build_url("collections"),
                self.routing.build_icon_path("collections"),
                True,
                eval(self.settings.show_collections.title()),
            ),
        ]
