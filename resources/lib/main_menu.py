# -*- coding: utf-8 -*-
from collections import namedtuple

import xbmcaddon
from addonutils import build_icon_path
from addonutils import get_internal_link
from data import __id__


MainMenuItem = namedtuple("MainMenuItem", ["title", "link", "icon", "is_dir", "is_displayed"])

main_menu_items = [
    MainMenuItem(
        "Поиск",
        get_internal_link("search", type=None),
        build_icon_path("search"),
        False,
        eval(xbmcaddon.Addon(id=__id__).getSetting("show_search").title()),
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
        eval(xbmcaddon.Addon(id=__id__).getSetting("show_last").title()),
    ),
    MainMenuItem(
        "Популярные",
        get_internal_link("items", type=None, shortcut="/popular"),
        build_icon_path("popular"),
        True,
        eval(xbmcaddon.Addon(id=__id__).getSetting("show_popular").title()),
    ),
    MainMenuItem(
        "Горячие",
        get_internal_link("items", type=None, shortcut="/hot"),
        build_icon_path("hot"),
        True,
        eval(xbmcaddon.Addon(id=__id__).getSetting("show_hot").title()),
    ),
    MainMenuItem(
        "ТВ",
        get_internal_link("tv"),
        build_icon_path("tv"),
        True,
        eval(xbmcaddon.Addon(id=__id__).getSetting("show_tv").title()),
    ),
    MainMenuItem(
        "Подборки",
        get_internal_link("collections"),
        build_icon_path("collections"),
        True,
        eval(xbmcaddon.Addon(id=__id__).getSetting("show_collections").title()),
    ),
]
