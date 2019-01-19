# -*- coding: utf-8 -*-
from collections import namedtuple

from addonutils import get_internal_link
from data import __settings__


MainMenuItem = namedtuple("MainMenuItem", ["title", "link", "is_dir", "is_displayed"])

main_menu_items = [
    MainMenuItem(
        "Поиск",
        get_internal_link("search", type=None),
        False,
        eval(__settings__.getSetting("show_search").title())
    ),
    MainMenuItem(
        "Закладки",
        get_internal_link("bookmarks"),
        True,
        True
    ),
    MainMenuItem(
        "Я смотрю",
        get_internal_link("watching"),
        True,
        True
    ),
    MainMenuItem(
        "Недосмотренные",
        get_internal_link("watching_movies"),
        True,
        True
    ),
    MainMenuItem(
        "Последние",
        get_internal_link("items", type=None),
        True,
        eval(__settings__.getSetting("show_last").title())
    ),
    MainMenuItem(
        "Популярные",
        get_internal_link("items", type=None, shortcut="/popular"),
        True,
        eval(__settings__.getSetting("show_popular").title())
    ),
    MainMenuItem(
        "Горячие",
        get_internal_link("items", type=None, shortcut="/hot"),
        True,
        eval(__settings__.getSetting("show_hot").title())
    ),
    MainMenuItem(
        "ТВ",
        get_internal_link("tv"),
        True,
        eval(__settings__.getSetting("show_tv").title())
    ),
    MainMenuItem(
        "Подборки",
        get_internal_link("collections"),
        True,
        eval(__settings__.getSetting("show_collections").title())
    ),
    MainMenuItem(
        "Спидтест",
        get_internal_link("speedtest"),
        True,
        eval(__settings__.getSetting("show_speedtest").title())
    )
]
