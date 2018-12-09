# -*- coding: utf-8 -*-
from collections import namedtuple

from addonutils import get_internal_link, build_icon_path
from data import __addon__


MainMenuItem = namedtuple("MainMenuItem", ["title", "link", "icon", "is_dir", "is_displayed"])

# Use icons from lib for default headings
main_menu_items = [
    MainMenuItem(
        "Поиск",
        get_internal_link("search", type=None),
        build_icon_path('search'),
        False,
        eval(__addon__.getSetting("show_search").title())
    ),
    MainMenuItem(
        "Закладки",
        get_internal_link("bookmarks"),
        build_icon_path('bookmarks'),
        True,
        True
    ),
    MainMenuItem(
        "Я смотрю",
        get_internal_link("watching"),
        build_icon_path('watching'),
        True,
        True
    ),
    MainMenuItem(
        "Недосмотренные",
        get_internal_link("watching_movies"),
        build_icon_path('watching_movies'),
        True,
        True
    ),
    MainMenuItem(
        "Последние",
        get_internal_link("items", type=None),
        build_icon_path('new'),
        True,
        eval(__addon__.getSetting("show_last").title())
    ),
    MainMenuItem(
        "Популярные",
        get_internal_link("items", type=None, shortcut="/popular"),
        build_icon_path('popular'),
        True,
        eval(__addon__.getSetting("show_popular").title())
    ),
    MainMenuItem(
        "Горячие",
        get_internal_link("items", type=None, shortcut="/hot"),
        build_icon_path("hot"),
        True,
        eval(__addon__.getSetting("show_hot").title())
    ),
    MainMenuItem(
        "ТВ",
        get_internal_link("tv"),
        build_icon_path("tv"),
        True,
        eval(__addon__.getSetting("show_tv").title())
    ),
    MainMenuItem(
        "Подборки",
        get_internal_link("collections"),
        build_icon_path("collections"),
        True,
        eval(__addon__.getSetting("show_collections").title())
    )
]
