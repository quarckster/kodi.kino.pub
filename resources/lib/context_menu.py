# -*- coding: utf-8 -*-
from addonutils import get_internal_link


def add_items(list_item):
    menu_items = []
    _toggle_watched(list_item, menu_items)
    _toggle_watchlist(list_item, menu_items)
    _edit_bookmarks(list_item, menu_items)
    list_item.addContextMenuItems(menu_items)


def _toggle_watchlist(list_item, menu_items):
    in_watchlist = list_item.getProperty("in_watchlist")
    if in_watchlist == "":
        return
    label = u"Не буду смотреть" if int(in_watchlist) else u"Буду смотреть"
    link = get_internal_link(
        "toggle_watchlist",
        id=list_item.getProperty("id"),
        added=not int(in_watchlist)
    )
    menu_items.append((label, "Container.Update({})".format(link)))


def _toggle_watched(list_item, menu_items):
    item_id = list_item.getProperty("id")
    season_number = list_item.getVideoInfoTag().getSeason()
    episode_number = list_item.getVideoInfoTag().getEpisode()
    watched = int(list_item.getVideoInfoTag().getPlayCount()) > 0
    label = u"Отметить как непросмотренное" if watched else u"Отметить как просмотренное"
    if episode_number != -1 and season_number != -1:
        kwargs = {"id": item_id, "season": season_number, "video": episode_number}
    elif season_number != -1:
        kwargs = {"id": item_id, "season": season_number}
    elif list_item.getVideoInfoTag().getMediaType() == "tvshow":
        return
    else:
        kwargs = {"id": item_id}
    link = get_internal_link("toggle_watched", **kwargs)
    menu_items.append((label, "Container.Update({})".format(link)))


def _edit_bookmarks(list_item, menu_items):
    item_id = list_item.getProperty("id")
    label = u"Изменить закладки"
    link = get_internal_link("edit_bookmarks", item_id=item_id)
    menu_items.append((label, "Container.Update({})".format(link)))
