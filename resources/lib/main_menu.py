# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from collections import namedtuple

from resources.lib.settings import settings
from resources.lib.utils import build_icon_path
from resources.lib.utils import get_internal_link


MainMenuItem = namedtuple("MainMenuItem", ["title", "link", "icon", "is_dir", "is_displayed"])

main_menu_items = [
    MainMenuItem(
        "Поиск",
        get_internal_link("search", type=None),
        build_icon_path("search"),
        False,
        eval(settings.show_search.title()),
    ),
    MainMenuItem(
        "Закладки", get_internal_link("bookmarks"), build_icon_path("bookmarks"), True, True
    ),
    MainMenuItem(
        "Я смотрю", get_internal_link("watching"), build_icon_path("watching"), True, True
    ),
    MainMenuItem(
        "Недосмотренные",
        get_internal_link("watching_movies"),
        build_icon_path("watching_movies"),
        True,
        True,
    ),
    MainMenuItem(
        "Последние",
        get_internal_link("items", type=None),
        build_icon_path("new"),
        True,
        eval(settings.show_last.title()),
    ),
    MainMenuItem(
        "Популярные",
        get_internal_link("items", type=None, shortcut="/popular"),
        build_icon_path("popular"),
        True,
        eval(settings.show_popular.title()),
    ),
    MainMenuItem(
        "Горячие",
        get_internal_link("items", type=None, shortcut="/hot"),
        build_icon_path("hot"),
        True,
        eval(settings.show_hot.title()),
    ),
    MainMenuItem(
        "ТВ", get_internal_link("tv"), build_icon_path("tv"), True, eval(settings.show_tv.title())
    ),
    MainMenuItem(
        "Подборки",
        get_internal_link("collections"),
        build_icon_path("collections"),
        True,
        eval(settings.show_collections.title()),
    ),
]
