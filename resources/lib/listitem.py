# -*- coding: utf-8 -*-
import xbmcaddon
from xbmcgui import ListItem

from addonutils import get_internal_link
from data import get_adv_setting, __id__


class ExtendedListItem(ListItem):

    def __new__(cls, name, label2="", iconImage="", thumbnailImage="", path="", **kwargs):
        return super(ExtendedListItem, cls).__new__(cls, name, label2, iconImage, thumbnailImage,
                                                    path)

    def __init__(self, name, label2="", iconImage="", thumbnailImage="", path="", poster=None,
                 video_info=None, properties=None, addContextMenuItems=False, subtitles=None):
        super(ExtendedListItem, self).__init__(name, label2, iconImage, thumbnailImage, path)
        if properties:
            self.setProperties(**properties)
        if video_info:
            self.setInfo("video", video_info)
            self.setResumeTime(video_info.get("time"))
        if poster:
            self.setArt({"poster": poster})
        if subtitles:
            self.setSubtitles(subtitles)
        if addContextMenuItems:
            self.addPredefinedContextMenuItems()

    def _addWatchlistContextMenuItem(self, menu_items):
        in_watchlist = self.getProperty("in_watchlist")
        if in_watchlist == "":
            return
        label = u"Не буду смотреть" if int(in_watchlist) else u"Буду смотреть"
        link = get_internal_link(
            "toggle_watchlist",
            id=self.getProperty("id"),
            added=int(not int(in_watchlist))
        )
        menu_items.append((label, "Container.Update({})".format(link)))

    def _addWatchedContextMenuItem(self, menu_items):
        item_id = self.getProperty("id")
        season_number = self.getVideoInfoTag().getSeason()
        video_number = self.getVideoInfoTag().getEpisode()
        video_number = video_number if video_number != -1 else 1
        watched = int(self.getVideoInfoTag().getPlayCount()) > 0
        label = u"Отметить как непросмотренное" if watched else u"Отметить как просмотренное"
        if self.getVideoInfoTag().getMediaType() == "tvshow":
            return
        elif self.getVideoInfoTag().getMediaType() == "season":
            kwargs = {"id": item_id, "season": season_number}
        elif self.getProperty("subtype") == "multi":
            kwargs = {"id": item_id}
        elif season_number != -1:
            kwargs = {"id": item_id, "season": season_number, "video": video_number}
        else:
            kwargs = {"id": item_id, "video": video_number}
        link = get_internal_link("toggle_watched", **kwargs)
        menu_items.append((label, "Container.Update({})".format(link)))

    def _addBookmarksContextMenuItem(self, menu_items):
        if self.getVideoInfoTag().getMediaType() == "season":
            return
        item_id = self.getProperty("id")
        label = u"Изменить закладки"
        link = get_internal_link("edit_bookmarks", item_id=item_id)
        menu_items.append((label, "Container.Update({})".format(link)))

    def _addCommentsContextMenuItem(self, menu_items):
        item_id = self.getProperty("id")
        label = u"Комментарии KinoPub"
        link = get_internal_link("comments", item_id=item_id)
        menu_items.append((label, "Container.Update({})".format(link)))

    def _addSimilarContextMenuItem(self, menu_items):
        item_id = self.getProperty("id")
        title = self.getLabel()
        label = u"Похожие фильмы"
        link = get_internal_link("similar", item_id=item_id, title=title)
        menu_items.append((label, "Container.Update({})".format(link)))

    def _addSeparatorContextMenuItem(self, menu_items):
        # 21 is the maximum number of characters when the hosrizontal scrolling doesn't appear.
        menu_items.append(("─" * 21, ""))

    def addPredefinedContextMenuItems(self, items=None):
        items = items or ["watched", "watchlist", "bookmarks", "comments", "similar", "separator"]
        menu_items = []
        for item in items:
            getattr(self, "_add{}ContextMenuItem".format(item.capitalize()))(menu_items)
        self.addContextMenuItems(menu_items)

    def setProperties(self, **properties):
        for prop, value in properties.items():
            self.setProperty(prop, str(value))

    def setResumeTime(self, resumetime, totaltime=None):
        totaltime = float(totaltime or self.getduration())
        if (
            resumetime is not None and
            totaltime > 0 and
            100 * resumetime / totaltime <=
            get_adv_setting("video", "playcountminimumpercent") and
            resumetime > get_adv_setting("video", "ignoresecondsatstart") or
            resumetime == 0
        ):
            self.setProperties(resumetime=resumetime, totaltime=totaltime)

    def markAdvert(self, has_advert):
        if xbmcaddon.Addon(id=__id__).getSetting("mark_advert") == "true" and has_advert:
            self.setLabel("{} (!)".format(self.getLabel()))
