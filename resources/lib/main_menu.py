# -*- coding: utf-8 -*-
from collections import namedtuple

from addonutils import get_internal_link
from data import __settings__


MainMenuItem = namedtuple("MainMenuItem", ["title", "link", "is_dir", "is_displayed"])

main_menu_items = [
    MainMenuItem(
        "[COLOR FFFFF000]Закладки[/COLOR]",
        get_internal_link("bookmarks"),
        True,
        True
    ),
    MainMenuItem(
        "[COLOR FFFFF000]Я смотрю[/COLOR]",
        get_internal_link("watching"),
        True,
        True
    ),
    MainMenuItem(
        "[COLOR FFFFF000]Недосмотренные[/COLOR]",
        get_internal_link("watching_movies"),
        True,
        True
    ),
    MainMenuItem(
        "[COLOR FFFFF000]Поиск[/COLOR]",
        get_internal_link("search", type=None),
        False,
        eval(__settings__.getSetting("show_search").title())
    ),
    MainMenuItem(
        "[COLOR FFFFF000]Последние[/COLOR]",
        get_internal_link("items", type=None),
        True,
        eval(__settings__.getSetting("show_last").title())
    ),
    MainMenuItem(
        "[COLOR FFFFF000]Популярные[/COLOR]",
        get_internal_link("items", type=None, shortcut="/popular"),
        True,
        eval(__settings__.getSetting("show_popular").title())
    ),
    MainMenuItem(
        "[COLOR FFFFF000]Горячие[/COLOR]",
        get_internal_link("items", type=None, shortcut="/hot"),
        True,
        eval(__settings__.getSetting("show_hot").title())
    ),
    MainMenuItem(
        "[COLOR FFFFF000]ТВ[/COLOR]",
        get_internal_link("tv"),
        True,
        eval(__settings__.getSetting("show_tv").title())
    ),
    MainMenuItem(
        "[COLOR FFFFF000]Подборки[/COLOR]",
        get_internal_link("collections"),
        True,
        eval(__settings__.getSetting("show_collections").title())
    )
]
