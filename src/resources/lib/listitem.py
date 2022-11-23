from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from xbmcgui import ListItem

from resources.lib.plugin import Plugin


class ExtendedListItem(ListItem):
    def __new__(cls, name: str, label2: str = "", path: str = "", **kwargs) -> "ExtendedListItem":
        return super().__new__(cls, name, label2, path)

    def __init__(
        self,
        *,
        name: str,
        plugin: Plugin,
        label2: str = "",
        iconImage: str = "",
        thumbnailImage: str = "",
        path: str = "",
        poster: Optional[str] = None,
        fanart: Optional[str] = None,
        video_info: Optional[Dict[str, Any]] = None,
        properties: Optional[Dict[str, Any]] = None,
        addContextMenuItems: bool = False,
        subtitles: Optional[List[str]] = None,
    ) -> None:
        super().__init__(name, label2, path)
        self.plugin = plugin
        if properties:
            self.setProperties(**properties)
        if video_info:
            self.setInfo("video", video_info)
            self.setResumeTime(video_info.get("time", 0))
        if poster:
            self.setArt({"poster": poster})
        if fanart:
            self.setArt({"fanart": fanart})
        if thumbnailImage:
            self.setArt({"thumb": thumbnailImage})
        if iconImage:
            self.setArt({"icon": iconImage})
        if subtitles:
            self.setSubtitles(subtitles)
        if addContextMenuItems:
            self.addPredefinedContextMenuItems()

    def _addWatchlistContextMenuItem(self, menu_items: List[Tuple[str, str]]) -> None:
        in_watchlist = self.getProperty("in_watchlist")
        if in_watchlist == "":
            return
        label = "Не буду смотреть" if int(in_watchlist) else "Буду смотреть"
        url = self.plugin.routing.build_url(
            "toggle_watchlist", self.getProperty("id"), added=int(not int(in_watchlist))
        )
        menu_items.append((label, f"Container.Update({url})"))

    def _addWatchedContextMenuItem(self, menu_items: List[Tuple[str, str]]) -> None:
        item_id = self.getProperty("id")
        season_number = self.getVideoInfoTag().getSeason()
        video_number = self.getVideoInfoTag().getEpisode()
        video_number = video_number if video_number != -1 else 1
        watched = int(self.getVideoInfoTag().getPlayCount()) > 0
        label = "Отметить как непросмотренное" if watched else "Отметить как просмотренное"
        if self.getVideoInfoTag().getMediaType() == "tvshow":
            return
        elif self.getVideoInfoTag().getMediaType() == "season":
            kwargs = {"season": season_number}
        elif self.getProperty("subtype") == "multi":
            kwargs = {}
        elif season_number != -1:
            kwargs = {"season": season_number, "video": video_number}
        else:
            kwargs = {"video": video_number}
        url = self.plugin.routing.build_url("toggle_watched", item_id, **kwargs)
        menu_items.append((label, f"Container.Update({url})"))

    def _addBookmarksContextMenuItem(self, menu_items: List[Tuple[str, str]]) -> None:
        if self.getVideoInfoTag().getMediaType() == "season":
            return
        item_id = self.getProperty("id")
        label = "Изменить закладки"
        url = self.plugin.routing.build_url("edit_bookmarks", item_id)
        menu_items.append((label, f"Container.Update({url})"))

    def _addCommentsContextMenuItem(self, menu_items: List[Tuple[str, str]]) -> None:
        item_id = self.getProperty("id")
        label = "Комментарии KinoPub"
        url = self.plugin.routing.build_url("comments", item_id)
        menu_items.append((label, f"Container.Update({url})"))

    def _addSimilarContextMenuItem(self, menu_items: List[Tuple[str, str]]) -> None:
        item_id = self.getProperty("id")
        title = self.getLabel()
        label = "Похожие фильмы"
        url = self.plugin.routing.build_url("similar", item_id, title=title)
        menu_items.append((label, f"Container.Update({url})"))

    def _addSeparatorContextMenuItem(self, menu_items: List[Tuple[str, str]]) -> None:
        # 21 is the maximum number of characters when the horizontal scrolling doesn't appear.
        menu_items.append(("─" * 21, ""))

    def addPredefinedContextMenuItems(self, items: Optional[List[str]] = None) -> None:
        items = items or ["watched", "watchlist", "bookmarks", "comments", "similar", "separator"]
        menu_items: List[str] = []
        for item in items:
            getattr(self, f"_add{item.capitalize()}ContextMenuItem")(menu_items)
        self.addContextMenuItems(menu_items)

    def setProperties(self, **properties) -> None:
        for prop, value in properties.items():
            self.setProperty(prop, str(value))

    def setResumeTime(self, resumetime: int, totaltime: float = 0.0) -> None:
        totaltime = float(totaltime or self.getVideoInfoTag().getDuration())
        if (
            resumetime > 0
            and totaltime > 0
            and 100 * resumetime / totaltime
            <= self.plugin.settings.advanced("video", "playcountminimumpercent")
            and resumetime > self.plugin.settings.advanced("video", "ignoresecondsatstart")
            or resumetime == 0
        ):
            self.setProperties(resumetime=resumetime, totaltime=totaltime)

    def markAdvert(self, has_advert: bool) -> None:
        if self.plugin.settings.mark_advert == "true" and has_advert:
            self.setLabel(f"{self.getLabel()} (!)")
