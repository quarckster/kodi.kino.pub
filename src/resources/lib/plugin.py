# -*- coding: utf-8 -*-
import codecs
import pickle
import sys
from collections import namedtuple
from urllib.parse import parse_qsl
from urllib.parse import urlsplit

import xbmcaddon
import xbmcgui

from resources.lib.auth import Auth
from resources.lib.client import KinoPubClient
from resources.lib.listitem import ExtendedListItem
from resources.lib.logger import Logger
from resources.lib.modeling import ItemsCollection
from resources.lib.routing import Routing
from resources.lib.search_history import SearchHistory
from resources.lib.settings import Settings


MainMenuItem = namedtuple("MainMenuItem", ["title", "url", "icon", "is_dir", "is_displayed"])


class Plugin(object):
    PLUGIN_ID = xbmcaddon.Addon().getAddonInfo("id")
    PLUGIN_URL = f"plugin://{PLUGIN_ID}"
    settings = Settings()

    def __init__(self):
        self._rules = {}
        self.path = urlsplit(sys.argv[0]).path or "/"
        self.handle = int(sys.argv[1])
        self.kwargs = dict(parse_qsl(sys.argv[2].lstrip("?")))
        self.auth = Auth(self)
        self.logger = Logger(self)
        self.routing = Routing(self)
        self.search_history = SearchHistory(self)
        self.main_menu_items = self._main_menu_items()
        self.items = ItemsCollection(self)

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
        fanart=None,
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
            fanart=fanart,
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
                "Профиль",
                self.routing.build_url("profile/"),
                self.routing.build_icon_path("profile"),
                False,
                True,
            ),
            MainMenuItem(
                "Поиск",
                self.routing.build_url("search", "all/"),
                self.routing.build_icon_path("search"),
                True,
                self.settings.show_search,
            ),
            MainMenuItem(
                "Закладки",
                self.routing.build_url("bookmarks/"),
                self.routing.build_icon_path("bookmarks"),
                True,
                True,
            ),
            MainMenuItem(
                "Я смотрю",
                self.routing.build_url("watching/"),
                self.routing.build_icon_path("watching"),
                True,
                True,
            ),
            MainMenuItem(
                "Недосмотренные",
                self.routing.build_url("watching_movies/"),
                self.routing.build_icon_path("watching_movies"),
                True,
                True,
            ),
            MainMenuItem(
                "Последние",
                self.routing.build_url("items", "all", "fresh/"),
                self.routing.build_icon_path("fresh"),
                True,
                self.settings.show_last,
            ),
            MainMenuItem(
                "Популярные",
                self.routing.build_url("items", "all", "popular/"),
                self.routing.build_icon_path("popular"),
                True,
                self.settings.show_popular,
            ),
            MainMenuItem(
                "Горячие",
                self.routing.build_url("items", "all", "hot/"),
                self.routing.build_icon_path("hot"),
                True,
                self.settings.show_hot,
            ),
            MainMenuItem(
                self.sorting_title,
                self.routing.build_url("items", "all", "sort/"),
                self.routing.build_icon_path("sort"),
                True,
                self.settings.show_sort,
            ),
            MainMenuItem(
                "ТВ",
                self.routing.build_url("tv/"),
                self.routing.build_icon_path("tv"),
                True,
                self.settings.show_tv,
            ),
            MainMenuItem(
                "Подборки",
                self.routing.build_url("collections/"),
                self.routing.build_icon_path("collections"),
                True,
                self.settings.show_collections,
            ),
            MainMenuItem(
                "Фильмы",
                self.routing.build_url("items", "movies/"),
                self.routing.build_icon_path("movies"),
                True,
                self.settings.show_movies,
            ),
            MainMenuItem(
                "Сериалы",
                self.routing.build_url("items", "serials/"),
                self.routing.build_icon_path("serials"),
                True,
                self.settings.show_serials,
            ),
            MainMenuItem(
                "ТВ шоу",
                self.routing.build_url("items", "tvshow/"),
                self.routing.build_icon_path("tvshows"),
                True,
                self.settings.show_tvshows,
            ),
            MainMenuItem(
                "3D",
                self.routing.build_url("items", "3d/"),
                self.routing.build_icon_path("3d"),
                True,
                self.settings.show_3d,
            ),
            MainMenuItem(
                "Концерты",
                self.routing.build_url("items", "concerts/"),
                self.routing.build_icon_path("concerts"),
                True,
                self.settings.show_concerts,
            ),
            MainMenuItem(
                "Документальные фильмы",
                self.routing.build_url("items", "documovies/"),
                self.routing.build_icon_path("documovies"),
                True,
                self.settings.show_documovies,
            ),
            MainMenuItem(
                "Документальные сериалы",
                self.routing.build_url("items", "docuserials/"),
                self.routing.build_icon_path("docuserials"),
                True,
                self.settings.show_docuserials,
            ),
        ]

    @property
    def sorting_title(self):
        return f"По {self.settings.sort_by} {self.settings.sort_direction}"

    @property
    def sorting_params(self):
        sorting = {
            "дате обновления": "updated",
            "дате добавления": "created",
            "году": "year",
            "названию": "title",
            "рейтингу": "rating",
            "Кинопоиску": "kinopoisk_rating",
            "IMDB": "imdb_rating",
            "просмотрам": "views",
            "зрителям": "watchers",
        }
        direction = {"по убыванию": "-", "по возрастанию": ""}
        return {
            "sort": f"{sorting[self.settings.sort_by]}{direction[self.settings.sort_direction]}"
        }

    def clear_window_property(self):
        xbmcgui.Window(10000).clearProperty("video.kino.pub-playback_data")

    def set_window_property(self, value):
        self.clear_window_property()
        pickled = codecs.encode(pickle.dumps(value), "base64").decode("utf-8")
        xbmcgui.Window(10000).setProperty("video.kino.pub-playback_data", pickled)

    def get_window_property(self, item_id):
        try:
            data = xbmcgui.Window(10000).getProperty("video.kino.pub-playback_data").encode("utf-8")
            items = pickle.loads(codecs.decode(data, "base64"))
        except EOFError:
            items = {}
        item = items.get(int(item_id), {})
        if item:
            item._plugin = self
        return item
