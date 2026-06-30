import sys
import urllib
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
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
from resources.lib.utils import cached_property, natural_sort
from resources.lib.utils import localize
from resources.lib.utils import popup_warning

try:
    import inputstreamhelper
except ImportError:
    inputstreamhelper = None


Response = namedtuple("Response", ["items", "pagination"])

# kino.pub genre id for anime, filtered out when the user enables "exclude anime".
ANIME_GENRE_ID = 25


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
        # watching/movies returns only ids + minimal metadata, so each movie needs
        # its own full items/{id} response. Fetch them concurrently rather than in
        # a blocking loop (executor.map preserves order). KinoPubClient is
        # thread-safe and the proxy/addon settings are warmed by the call below.
        response = self.plugin.client("watching/movies").get()
        item_ids = [item_data["id"] for item_data in response["items"]]
        if not item_ids:
            return []
        workers = min(self.plugin.settings.concurrent_requests, len(item_ids))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            movies = list(executor.map(self.instantiate_from_item_id, item_ids))
        return cast(List["Movie"], movies)

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

    @staticmethod
    def _is_anime(item: Dict[str, Any]) -> bool:
        return any(genre["id"] == ANIME_GENRE_ID for genre in item["genres"])

    def _get_anime_excluded(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch one screen's worth of items with anime removed.

        Dropping anime from an API page leaves fewer than ``perpage`` items, so
        keep pulling subsequent API pages until a full screen is collected (or the
        pages run out). When a page overshoots, the surplus is carried to the next
        screen by rewinding the pagination cursor -- ``current`` back one and
        ``start_from`` past the last item shown -- which render_pagination replays
        on the next request.
        """
        data = dict(data)  # don't mutate the caller's query params
        start_from = int(data.pop("start_from", 0))
        items: List[Dict[str, Any]] = []
        pagination: Dict[str, Any] = {}

        while True:
            response = self.plugin.client(endpoint).get(data=data)
            api_items = response["items"]
            pagination = response["pagination"]
            page_size = int(pagination["perpage"])
            non_anime = [item for item in api_items[start_from:] if not self._is_anime(item)]

            # Enough to fill the screen: keep only what's needed and rewind the
            # cursor so the leftovers show up on the next screen.
            if len(items) + len(non_anime) >= page_size:
                needed = page_size - len(items)
                items.extend(non_anime[:needed])
                last_item_id = non_anime[needed - 1]["id"]
                last_index = next(
                    index for index, item in enumerate(api_items) if item["id"] == last_item_id
                )
                pagination["current"] = int(pagination["current"]) - 1
                pagination["start_from"] = last_index + 1
                break

            # Not enough yet: take everything and advance to the next API page,
            # if there is one.
            items.extend(non_anime)
            if int(pagination["current"]) + 1 >= int(pagination["total"]):
                break
            data["page"] = int(pagination["current"]) + 1
            start_from = 0

        return {"items": items, "pagination": pagination}


class ItemEntity:
    isdir: ClassVar[bool]

    def __init__(self, *, parent, item_data: Dict) -> None:
        self.parent = parent
        self.item = item_data
        self.item_id = self.item["id"]
        self.title = self.item.get("title", "")
        self._plugin: Optional["Plugin"] = None
        self.url: Optional[str] = None
        self.properties: Dict[str, Union[str, float, bool]] = {}

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
            properties={"id": self.item_id, **self.properties},
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

    def _choose_cdn_loc(self, url: str) -> str:
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

    def _get_media_url_from_dialog(self) -> str:
        urls = {}
        for file_ in self.video_data["files"]:
            for stream_type, url in file_["url"].items():
                if stream_type != "hls":
                    continue
                quality = file_["quality"]
                urls[quality] = url
        qualities = natural_sort(list(urls.keys()))
        dialog = xbmcgui.Dialog()
        # Choose video quality
        result = dialog.select(localize(32043), qualities)
        if result == -1:
            sys.exit()
        return self._choose_cdn_loc(urls[qualities[result]])

    @property
    def media_url(self) -> str:
        desired_quality = self.plugin.settings.video_quality
        desired_stream_type = self.plugin.settings.stream_type
        ask_quality = self.plugin.settings.ask_quality
        if ask_quality == "true" and desired_stream_type == "hls":
            return self._get_media_url_from_dialog()
        files = {file_["quality"]: file_["url"] for file_ in self.video_data["files"]}
        try:
            return self._choose_cdn_loc(files[desired_quality][desired_stream_type])
        except KeyError:
            # if there is no such quality then return a link with the highest available quality
            return self._choose_cdn_loc(
                files[natural_sort(list(files.keys()))[-1]][desired_stream_type]
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
                # HLS stream is not supported
                popup_warning(localize(32044))
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
            **self.properties,
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
        self.properties = {
            "is_subscribed": self.is_in_watchlist or self.item.get("subscribed", False)
        }

    @property
    def video_info(self) -> Dict:
        if self.is_in_watchlist:
            return {"mediatype": self.mediatype}
        return {
            **super().video_info,
            "trailer": self.trailer_url,
            "mediatype": self.mediatype,
            # ended, on air
            "status": localize(32045) if self.item["finished"] else localize(32046),
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
        self.properties = {"video_number": self.index, "season_number": self.season.index}

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


class Multi(ItemEntity):
    isdir: ClassVar[bool] = True

    def __init__(self, *, parent: ItemsCollection, item_data: Dict, **kwargs) -> None:
        super().__init__(parent=parent, item_data=item_data)
        self.url = self.plugin.routing.build_url("episodes", f"{self.item_id}/")
        self.properties = {"subtype": "multi"}

    @property
    def videos(self) -> List["Episode"]:
        return [
            Episode(parent=self, item_data=episode_item, index=i)
            for i, episode_item in enumerate(self.item["videos"], 1)
        ]

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
        self.properties = {"video_number": self.index}

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


class Movie(PlayableItem):
    mediatype: ClassVar[str] = "movie"

    def __init__(self, *, parent: ItemsCollection, item_data: Dict, **kwargs) -> None:
        super().__init__(parent=parent, item_data=item_data)
        self.url = self.plugin.routing.build_url("play", self.item_id)
        self.properties = {"video_number": "1"}

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
        # A full items/{id} response embeds the per-user watch state in its video
        # entry, so reuse it instead of an extra "watching" request (the
        # "I'm watching" screen already fetched items/{id} per movie). List
        # endpoints omit it, so fall back to the API call when it's absent.
        videos = self.item.get("videos")
        if videos and "watching" in videos[0]:
            video = videos[0]
            return {
                "time": video["watching"]["time"],
                "status": video["watching"]["status"],
                "duration": video["duration"],
            }
        return self.plugin.client("watching").get(data={"id": self.item_id})["item"]["videos"][0]


CONTENT_TYPE_MAP = {
    "serial": TVShow,
    "docuserial": TVShow,
    "tvshow": TVShow,
    "concert": Movie,
    "3d": Movie,
    "documovie": Movie,
    "movie": Movie,
}
