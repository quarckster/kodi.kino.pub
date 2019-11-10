# -*- coding: utf-8 -*-
from __future__ import absolute_import

from collections import namedtuple

from resources.lib.routing import plugin
from resources.lib.settings import settings
from resources.lib.utils import build_icon_path


MainMenuItem = namedtuple("MainMenuItem", ["title", "url", "icon", "is_dir", "is_displayed"])

main_menu_items = [
    MainMenuItem(
        "Поиск",
        plugin.build_url("search", content_type=None),
        build_icon_path("search"),
        False,
        eval(settings.show_search.title()),
    ),
    MainMenuItem(
        "Закладки", plugin.build_url("bookmarks"), build_icon_path("bookmarks"), True, True
    ),
    MainMenuItem("Я смотрю", plugin.build_url("watching"), build_icon_path("watching"), True, True),
    MainMenuItem(
        "Недосмотренные",
        plugin.build_url("watching_movies"),
        build_icon_path("watching_movies"),
        True,
        True,
    ),
    MainMenuItem(
        "Последние",
        plugin.build_url("items", shortcut="/fresh", content_type=None),
        build_icon_path("new"),
        True,
        eval(settings.show_last.title()),
    ),
    MainMenuItem(
        "Популярные",
        plugin.build_url("items", shortcut="/popular", content_type=None),
        build_icon_path("popular"),
        True,
        eval(settings.show_popular.title()),
    ),
    MainMenuItem(
        "Горячие",
        plugin.build_url("items", shortcut="/hot", content_type=None),
        build_icon_path("hot"),
        True,
        eval(settings.show_hot.title()),
    ),
    MainMenuItem(
        "ТВ", plugin.build_url("tv"), build_icon_path("tv"), True, eval(settings.show_tv.title())
    ),
    MainMenuItem(
        "Подборки",
        plugin.build_url("collections"),
        build_icon_path("collections"),
        True,
        eval(settings.show_collections.title()),
    ),
]
