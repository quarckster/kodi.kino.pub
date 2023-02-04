import re
import sys
import typing
import urllib
from collections import namedtuple
from typing import Any
from typing import cast
from typing import ClassVar
from typing import Dict
from typing import List
from typing import Optional
from typing import TYPE_CHECKING
from typing import Union

import xbmcgui

from resources.lib.listitem import ExtendedListItem

if TYPE_CHECKING:
    from resources.lib.plugin import Plugin
from resources.lib.utils import cached_property
from resources.lib.utils import popup_warning


try:
    import inputstreamhelper
except ImportError:
    inputstreamhelper = None


Response = namedtuple("Response", ["items", "pagination"])


class ItemsCollection:
    def __init__(self, plugin: "Plugin"):
        self.plugin = plugin

    def get(self, endpoint: str, data=None, exclude_anime: bool = False) -> Response:
        if exclude_anime:
            resp = self._get_anime_excluded(endpoint, data=data)
        else:
            resp = self.plugin.client(endpoint).get(data=data)
        items = [
            self.instantiate_from_item_data(item_data, index=i)
            for i, item_data in enumerate(resp["items"], 1)
        ]
        return Response(items, resp.get("pagination"))

    @property
    def watching_movies(self) -> List["Movie"]:
        movies = []
        for item_data in self.plugin.client("watching/movies").get()["items"]:
            movie = cast(Movie, self.instantiate_from_item_id(item_data["id"]))
            movies.append(movie)
        return movies

    @property
    def watching_tvshows(self) -> List["TVShow"]:
        tvshows = []
        items_data = self.plugin.client("watching/serials").get(data={"subscribed": 1})["items"]
        for item_data in items_data:
            # This needs in order to add context menu items in "Я смотрю"
            item_data["from_watching"] = True
            tvshow = cast(TVShow, self.instantiate_from_item_data(item_data=item_data))
            tvshows.append(tvshow)
        return tvshows

    def get_api_item(self, item_id: str) -> Dict:
        return self.plugin.client(f"items/{item_id}").get()["item"]

    def instantiate_from_item_id(
        self, item_id: str, index: Optional[int] = None
    ) -> Union["TVShow", "Multi", "Movie"]:
        item = self.plugin.get_window_property(item_id)
        if item:
            return item
        item_data = self.get_api_item(item_id)
        return self.instantiate_from_item_data(item_data, index)

    def instantiate_from_item_data(
        self, item_data: Dict, index: Optional[int] = None
    ) -> Union["TVShow", "Multi", "Movie"]:
        cls = Multi if item_data.get("subtype") == "multi" else CONTENT_TYPE_MAP[item_data["type"]]
        return cast(
            Union["TVShow", "Multi", "Movie"], cls(parent=self, item_data=item_data, index=index)
        )

    def get_playable(
        self,
        item: Union["TVShow", "Multi", "Movie"],
        season_index: Optional[str] = None,
        index: Optional[str] = None,
    ) -> Union["SeasonEpisode", "Episode", "Movie"]:
        if isinstance(item, TVShow) and season_index and index:
            return item.seasons[int(season_index) - 1].episodes[int(index) - 1]
        elif isinstance(item, Multi) and index:
            return item.videos[int(index) - 1]
        else:
            return cast(Movie, item)

    @typing.no_type_check
    def _get_anime_excluded(
        self, endpoint: str, data: Dict, collection: Optional[Dict[str, List[Dict]]] = None
    ) -> Dict[str, List[Dict]]:
        # init items collection
        collection = collection or {"items": []}

        # exclude start_from from request data
        start_from = int(data.pop("start_from", 0))

        resp = self.plugin.client(endpoint).get(data=data)

        new_items = resp["items"]
        pagination = resp["pagination"]
        page_size = int(pagination["perpage"])
        collection["pagination"] = pagination

        # filter items list from anime items
        non_anime_items = list(
            x for x in new_items[start_from:] if all(i["id"] != 25 for i in x["genres"])
        )

        # if not enough items continue with next API page
        if len(non_anime_items) + len(collection["items"]) < page_size:
            collection["items"].extend(non_anime_items)

            if int(pagination["current"]) + 1 < int(pagination["total"]):
                data.update({"page": pagination["current"] + 1, "start_from": 0})
                collection = self._get_anime_excluded(endpoint, data, collection)
        else:
            # exclude extra items from filtered items
            count_items_to_extend = page_size - len(collection["items"])
            items = non_anime_items[:count_items_to_extend]
            last_item_id = items[-1]["id"]
            last_item_index = next(
                (index for (index, d) in enumerate(new_items) if d["id"] == last_item_id), None
            )
            collection["items"].extend(items)
            collection["pagination"]["current"] = (
                pagination["current"] - 1
            )  # start from current API page
            collection["pagination"]["start_from"] = (
                last_item_index + 1
            )  # do not include last item to next page

        return collection


class ItemEntity:
    isdir: ClassVar[bool]

    def __init__(self, *, parent, item_data: Dict) -> None:
        self.parent = parent
        self.item = item_data
        self.item_id = self.item["id"]
        self.title = self.item.get("title", "")
        self._plugin: Optional["Plugin"] = None
        self.url: Optional[str] = None

    @property
    def plugin(self) -> "Plugin":
        return self._plugin or self.parent.plugin

    @property
    def plot(self) -> str:
        final_plot = []
        if self.item["imdb_rating"]:
            final_plot.append(f"IMDB: {str(round(self.item['imdb_rating'], 1))}")
        if self.item["kinopoisk_rating"]:
            final_plot.append(f"Кинопоиск: {str(round(self.item['kinopoisk_rating'], 1))}")
        # a new line between the ratings and the plot
        if self.item["imdb_rating"] or self.item["kinopoisk_rating"]:
            final_plot.append("")
        final_plot.append(self.item["plot"])
        return "\n".join(final_plot)

    @property
    def video_info(self) -> Dict[str, Any]:
        rating = self.item.get("imdb_rating") or self.item.get("kinopoisk_rating") or 0.0
        return {
            "year": int(self.item["year"]),
            "genre": ", ".join([genre["title"] for genre in self.item["genres"]]),
            "rating": float(rating),
            "cast": [cast.strip() for cast in self.item["cast"].split(",")],
            "director": self.item["director"],
            "plot": self.plot,
            "title": self.title,
            "imdbnumber": self.item["imdb"],
            "votes": self.item["rating_votes"],
            "country": ", ".join([country["title"] for country in self.item["countries"]]),
        }

    @property
    def trailer_url(self) -> Optional[str]:
        if "trailer" in self.item:
            return self.plugin.routing.build_url("trailer", self.item_id)
        return None

    @cached_property
    def watching_info(self) -> Dict:
        return self.plugin.client("watching").get(data={"id": self.item_id})["item"]

    @property
    def list_item(self) -> ExtendedListItem:
        li = self.plugin.list_item(
            name=getattr(self, "li_title", self.title),
            poster=self.item.get("posters", {}).get("big"),
            fanart=self.item.get("posters", {}).get("wide"),
            thumbnailImage=self.item.get(
                "thumbnail", self.item.get("posters", {}).get("small", "")
            ),
            properties={"id": self.item_id, "is_subscribed": getattr(self, "is_subscribed", "")},
            video_info=self.video_info,
            addContextMenuItems=True,
        )
        li.markAdvert(self.item.get("advert", False))
        return li

    def __getstate__(self) -> Dict:
        odict = self.__dict__.copy()
        if "parent" in odict:
            del odict["parent"]
        if "_plugin" in odict:
            del odict["_plugin"]
        return odict

    def __repr__(self) -> str:
        return f"{type(self).__name__}(item_id: {self.item_id}; title: {self.title})"


class PlayableItem(ItemEntity):
    isdir: ClassVar[bool] = False

    @property
    def video_data(self):
        return self.item

    def _choose_cdn_loc(self, url) -> str:
        parsed = urllib.parse.urlparse(url)
        return urllib.parse.urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                f"loc={self.plugin.settings.loc}",
                parsed.fragment,
            )
        )

    @property
    def media_url(self) -> str:
        quality = self.plugin.settings.video_quality
        stream_type = self.plugin.settings.stream_type
        ask_quality = self.plugin.settings.ask_quality

        def natural_sort(lines: List[str]) -> List[str]:
            def convert(text: str) -> Union[str, int]:
                return int(text) if text.isdigit() else text.lower()

            def alphanum_key(key: str) -> List[Union[str, int]]:
                return [convert(c) for c in re.split("([0-9]+)", key)]

            return sorted(lines, key=alphanum_key)

        files = {f["quality"]: f["url"] for f in self.video_data["files"]}
        flatten_urls_dict = {
            f"{quality}@{stream}": url
            for quality, urls in files.items()
            for stream, url in urls.items()
        }
        urls_list = natural_sort(list(flatten_urls_dict.keys()))
        if ask_quality == "true":
            dialog = xbmcgui.Dialog()
            result = dialog.select("Выберите качество видео", urls_list)
            if result == -1:
                sys.exit()
            else:
                return self._choose_cdn_loc(flatten_urls_dict[urls_list[result]])
        else:
            try:
                return self._choose_cdn_loc(files[quality][stream_type])
            except KeyError:
                # if there is no such quality then return a link with the highest available quality
                return self._choose_cdn_loc(
                    files[natural_sort(list(files.keys()))[-1]][stream_type]
                )

    @property
    def list_item(self) -> ExtendedListItem:
        li = super().list_item
        li.setProperty("isPlayable", "true")
        li.setResumeTime(self.resume_time, self.watching_info["duration"])
        return li

    @property
    def resume_time(self) -> int:
        if self.watching_info["time"] == self.watching_info["duration"]:
            return 0
        return self.watching_info["time"]

    @property
    def hls_properties(self) -> Dict[str, str]:
        if self.plugin.is_hls_enabled:
            helper = inputstreamhelper.Helper("hls")
            if not helper.check_inputstream():
                popup_warning("HLS поток не поддерживается")
                return {}
            else:
                return {
                    "inputstream": helper.inputstream_addon,
                    "inputstream.adaptive.manifest_type": "hls",
                }
        return {}

    @property
    def playable_list_item(self) -> ExtendedListItem:
        properties = {
            "item_id": self.item_id,
            "play_duration": self.video_info["duration"],
            "play_resumetime": self.resume_time,
            "playcount": self.video_info["playcount"],
            "imdbnumber": self.video_info["imdbnumber"],
            **self.hls_properties,
        }
        return self.plugin.list_item(
            name=getattr(self, "li_title", self.title),
            path=self.media_url,
            properties=properties,
            iconImage=self.item.get("posters", {}).get("small", ""),
            thumbnailImage=self.item.get("posters", {}).get("small", ""),
            poster=self.item.get("posters", {}).get("big"),
            subtitles=[subtitle.get("url") for subtitle in self.video_data["subtitles"]],
        )


class TVShow(ItemEntity):
    isdir: ClassVar[bool] = True
    mediatype: ClassVar[str] = "tvshow"

    def __init__(self, *, parent=ItemsCollection, item_data=Dict, **kwargs) -> None:
        super().__init__(parent=parent, item_data=item_data)
        self.url = self.plugin.routing.build_url("seasons", f"{self.item_id}/")
        self.is_in_watchlist = self.item.get("from_watching") is True
        if self.is_in_watchlist:
            self.li_title = f"{self.title} : [COLOR FFFFF000]+{self.item['new']}[/COLOR]"
        self.is_subscribed = self.is_in_watchlist or self.item.get("subscribed")

    @property
    def video_info(self) -> Dict:
        if self.is_in_watchlist:
            return {"mediatype": self.mediatype}
        return {
            **super().video_info,
            "trailer": self.trailer_url,
            "mediatype": self.mediatype,
            "status": "окончен" if self.item["finished"] else "в эфире",
        }

    @property
    def seasons(self) -> List["Season"]:
        return [
            Season(parent=self, item_data=season, index=i)
            for i, season in enumerate(self.item["seasons"], 1)
        ]


class Season(ItemEntity):
    isdir: ClassVar[bool] = True
    mediatype: ClassVar[str] = "season"

    def __init__(self, *, index: int, parent: TVShow, item_data: Dict) -> None:
        super().__init__(parent=parent, item_data=item_data)
        self.index = index
        self.tvshow = self.parent
        self.title = f"Сезон {self.index}"
        self.item_id = self.tvshow.item_id
        self.url = self.plugin.routing.build_url("season_episodes", self.item_id, f"{self.index}/")
        self.watching_info = self.tvshow.watching_info["seasons"][self.index - 1]
        self.watching_status = self.watching_info["status"]

    @property
    def episodes(self) -> List["SeasonEpisode"]:
        return [
            SeasonEpisode(parent=self, item_data=episode_item, index=i)
            for i, episode_item in enumerate(self.item["episodes"], 1)
        ]

    @property
    def video_info(self) -> Dict:
        return {
            **self.tvshow.video_info.copy(),
            "season": self.index,
            "playcount": self.watching_status,
            "mediatype": self.mediatype,
        }


class SeasonEpisode(PlayableItem):
    mediatype: ClassVar[str] = "episode"

    def __init__(self, *, index: int, parent: Season, item_data: Dict) -> None:
        super().__init__(parent=parent, item_data=item_data)
        self.index = index
        self.season = self.parent
        self.tvshow = self.season.tvshow
        self.item_id = self.tvshow.item_id
        self.url = self.plugin.routing.build_url(
            "play", self.item_id, season_index=self.season.index, index=self.index
        )
        self.li_title = f"s{self.season.index:02d}e{self.index:02d}"
        if self.title:
            self.li_title = f"{self.li_title} | {self.title}"
        try:
            # In a tvshow season could be a case when some episodes are not available, but episode
            # numbers in response payload are set correctly.
            self.watching_info = self.season.watching_info["episodes"][self.index - 1]
            self.watching_status = self.watching_info["status"]
        except IndexError:
            self.watching_info = self.watching_status = None

    @property
    def video_info(self) -> Dict:
        return {
            **self.tvshow.video_info.copy(),
            "season": self.season.index,
            "episode": self.index,
            "title": self.title,
            "tvshowtitle": self.tvshow.title,
            "time": self.resume_time,
            "duration": self.watching_info["duration"],
            "playcount": self.watching_info["status"],
            "mediatype": self.mediatype,
        }

    @property
    def playable_list_item(self) -> ExtendedListItem:
        li = super().playable_list_item
        li.setProperties(video_number=self.index, season_number=self.season.index)
        return li


class Multi(ItemEntity):
    isdir: ClassVar[bool] = True

    def __init__(self, *, parent: ItemsCollection, item_data: Dict, **kwargs) -> None:
        super().__init__(parent=parent, item_data=item_data)
        self.url = self.plugin.routing.build_url("episodes", f"{self.item_id}/")

    @property
    def videos(self) -> List["Episode"]:
        return [
            Episode(parent=self, item_data=episode_item, index=i)
            for i, episode_item in enumerate(self.item["videos"], 1)
        ]

    @property
    def list_item(self) -> ExtendedListItem:
        li = super().list_item
        li.setProperty("subtype", "multi")
        return li

    @property
    def video_info(self) -> Dict:
        return {**super().video_info, "playcount": self.watching_info["status"]}


class Episode(PlayableItem):
    mediatype: ClassVar[str] = "episode"

    def __init__(self, *, index: int, parent: Multi, item_data: Dict) -> None:
        super().__init__(parent=parent, item_data=item_data)
        self.index = index
        self.item_id = self.parent.item_id
        self.url = self.plugin.routing.build_url("play", self.item_id, index=self.index)
        self.li_title = f"e{self.index:02d}"
        if self.title:
            self.li_title = f"{self.li_title} | {self.title}"
        self.watching_status = self.watching_info["status"]

    @property
    def video_info(self) -> Dict:
        return {
            **self.parent.video_info.copy(),
            "episode": self.index,
            "title": self.title,
            "tvshowtitle": self.title,
            "time": self.resume_time,
            "duration": self.watching_info["duration"],
            "playcount": self.item["watched"],
            "mediatype": self.mediatype,
        }

    @cached_property
    def watching_info(self) -> Dict:
        return self.parent.watching_info["videos"][int(self.index) - 1]

    @property
    def playable_list_item(self) -> ExtendedListItem:
        li = super().playable_list_item
        li.setProperties(video_number=self.index)
        return li


class Movie(PlayableItem):
    mediatype: ClassVar[str] = "movie"

    def __init__(self, *, parent: ItemsCollection, item_data: Dict, **kwargs) -> None:
        super().__init__(parent=parent, item_data=item_data)
        self.url = self.plugin.routing.build_url("play", self.item_id)

    @cached_property
    def video_data(self) -> Dict:
        if "videos" in self.item:
            return self.item["videos"][0]
        return self.plugin.items.get_api_item(self.item_id)["videos"][0]

    @property
    def video_info(self) -> Dict:
        return {
            **super().video_info,
            "time": self.resume_time,
            "duration": self.watching_info["duration"],
            "playcount": self.watching_info["status"],
            "trailer": self.trailer_url,
            "mediatype": self.mediatype,
        }

    @cached_property
    def watching_info(self) -> Dict:
        return self.plugin.client("watching").get(data={"id": self.item_id})["item"]["videos"][0]

    @property
    def playable_list_item(self) -> ExtendedListItem:
        li = super().playable_list_item
        li.setProperties(video_number=1)
        return li


CONTENT_TYPE_MAP = {
    "serial": TVShow,
    "docuserial": TVShow,
    "tvshow": TVShow,
    "concert": Movie,
    "3d": Movie,
    "documovie": Movie,
    "movie": Movie,
}
