# -*- coding: utf-8 -*-
import re
import sys
import urllib
from collections import namedtuple
from functools import cached_property

import xbmcgui

from resources.lib.utils import fix_m3u8
from resources.lib.utils import notice

try:
    import inputstreamhelper
except ImportError:
    inputstreamhelper = None

Response = namedtuple("Response", ["items", "pagination"])


class ItemsCollection(object):
    @property
    def content_type_map(self):
        return {
            "serial": TVShow,
            "docuserial": TVShow,
            "tvshow": TVShow,
            "concert": Movie,
            "3d": Movie,
            "documovie": Movie,
            "movie": Movie,
        }

    def __init__(self, plugin):
        self.plugin = plugin

    def get(self, endpoint, data=None, exclude_anime=False):
        if exclude_anime:
            resp = self._get_anime_exluded(endpoint, data=data)
        else:
            resp = self.plugin.client(endpoint).get(data=data)
        items = [self.instantiate(item=item, index=i) for i, item in enumerate(resp["items"], 1)]
        return Response(items, resp.get("pagination"))

    @property
    def watching_movies(self):
        movies = []
        for item in self.plugin.client("watching/movies").get()["items"]:
            item = self.get_api_item(item["id"])
            movies.append(self.instantiate(item=item))
        return movies

    @property
    def watching_tvshows(self):
        tvshows = []
        for item in self.plugin.client("watching/serials").get(data={"subscribed": 1})["items"]:
            tvshow = self.instantiate(item=item)
            tvshow.new = item["new"]
            tvshow._video_info = {"mediatype": tvshow.mediatype}
            tvshows.append(tvshow)
        return tvshows

    def get_api_item(self, item_id):
        return self.plugin.client(f"items/{item_id}").get()["item"]

    def _get_item_entity(self, item_id=None, item=None):
        if item_id and not item:
            item = self.get_api_item(item_id)
        if item.get("subtype") == "multi":
            return item, Multi
        else:
            return item, self.content_type_map[item["type"]]

    def instantiate(self, item_id=None, item=None, index=None):
        item, item_entity = self._get_item_entity(item_id, item)
        return item_entity(self, item, index=index)

    def get_playable(self, item, season_index=None, index=None):
        if isinstance(item, TVShow):
            return item.seasons[int(season_index) - 1].episodes[int(index) - 1]
        elif isinstance(item, Multi):
            return item.videos[int(index) - 1]
        else:
            return item

    def _get_anime_exluded(self, endpoint, data=None, collection=None):
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
            [x for x in new_items[start_from:] if all(i["id"] != 25 for i in x["genres"])]
        )

        # if not enough items continue with next API page
        if len(non_anime_items) + len(collection["items"]) < page_size:
            collection["items"].extend(non_anime_items)

            if int(pagination["current"]) + 1 < int(pagination["total"]):
                data.update({"page": pagination["current"] + 1, "start_from": 0})
                collection = self._get_anime_exluded(endpoint, data, collection)
        else:
            # exlude extra items from filtered items
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


class ItemEntity(object):
    def __init__(self, parent, item, index=None):
        self.parent = parent
        self.item = item
        self.index = index
        self.item_id = self.item.get("id")
        self.title = self.item.get("title")
        self._plugin = None

    @property
    def plugin(self):
        return self._plugin or self.parent.plugin

    @property
    def plot(self):
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
    def video_info(self):
        rating = self.item.get("imdb_rating") or self.item.get("kinopoisk_rating") or 0.0
        return {
            "year": int(self.item["year"]),
            "genre": ", ".join([genre["title"] for genre in self.item["genres"]]),
            "rating": float(rating),
            "cast": [cast.strip() for cast in self.item["cast"].split(",")],
            "director": self.item["director"],
            "plot": self.plot,
            "title": self.title,
            "duration": self.item.get("duration", {}).get("average"),
            "imdbnumber": self.item["imdb"],
            "votes": self.item["rating_votes"],
            "country": ", ".join([country["title"] for country in self.item["countries"]]),
        }

    @property
    def trailer_url(self):
        if "trailer" in self.item:
            return self.plugin.routing.build_url("trailer", self.item_id)
        return None

    @cached_property
    def watching_info(self):
        return self.plugin.client("watching").get(data={"id": self.item_id})["item"]

    @property
    def list_item(self):
        li = self.plugin.list_item(
            getattr(self, "li_title", self.title),
            poster=self.item.get("posters", {}).get("big"),
            fanart=self.item.get("posters", {}).get("wide"),
            thumbnailImage=self.item.get(
                "thumbnail", self.item.get("posters", {}).get("small", "")
            ),
            properties={"id": self.item_id},
            video_info=self.video_info,
            addContextMenuItems=True,
        )
        if self.item.get("in_watchlist") is not None:
            li.setProperty("in_watchlist", str(int(self.item["in_watchlist"])))
        li.markAdvert(self.item.get("advert"))
        return li

    def __getstate__(self):
        odict = self.__dict__.copy()
        if "parent" in odict:
            del odict["parent"]
        if "_plugin" in odict:
            del odict["_plugin"]
        return odict

    def __repr__(self):
        return f"{type(self).__name__}(item_id: {self.item_id}; title: {self.title})"


class PlayableItem(ItemEntity):
    isdir = False

    def get_media_url(self):
        quality = self.plugin.settings.video_quality
        stream_type = self.plugin.settings.stream_type
        ask_quality = self.plugin.settings.ask_quality

        def natural_sort(line):
            def convert(text):
                return int(text) if text.isdigit() else text.lower()

            def alphanum_key(key):
                return [convert(c) for c in re.split("([0-9]+)", key)]

            return sorted(line, key=alphanum_key)

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
                return flatten_urls_dict[urls_list[result]]
        else:
            try:
                return files[quality][stream_type]
            except KeyError:
                # if there is no such quality then return a link with the highest available quality
                return files[natural_sort(list(files.keys()))[-1]][stream_type]

    @property
    def media_url(self):
        url = self.get_media_url()
        if urllib.parse.urlsplit(url).path.endswith("m3u8"):
            return fix_m3u8(url, self.plugin.logger)
        return url

    @property
    def list_item(self):
        li = super(PlayableItem, self).list_item
        li.setProperty("isPlayable", "true")
        li.setResumeTime(self.resume_time, self.watching_info["duration"])
        return li

    @property
    def resume_time(self):
        if self.watching_info["time"] == self.watching_info["duration"]:
            return 0
        return self.watching_info["time"]

    @property
    def hls_properties(self):
        if (
            "hls" in self.plugin.settings.stream_type
            and self.plugin.settings.inputstream_adaptive_enabled == "true"
            and inputstreamhelper
        ):
            helper = inputstreamhelper.Helper("hls")
            if not helper.check_inputstream():
                notice("HLS поток не поддерживается")
                return {}
            else:
                return {
                    "inputstream": helper.inputstream_addon,
                    "inputstream.adaptive.manifest_type": "hls",
                }
        return {}

    @property
    def playable_list_item(self):
        properties = {
            "item_id": self.item_id,
            "play_duration": self.video_info["duration"],
            "play_resumetime": self.resume_time,
            "playcount": self.video_info["playcount"],
            "imdbnumber": self.video_info["imdbnumber"],
            **self.hls_properties,
        }
        return self.plugin.list_item(
            getattr(self, "li_title", self.title),
            path=self.media_url,
            properties=properties,
            iconImage=self.item.get("posters", {}).get("small", ""),
            thumbnailImage=self.item.get("posters", {}).get("small", ""),
            poster=self.item.get("posters", {}).get("big"),
            subtitles=[subtitle["url"] for subtitle in self.video_data["subtitles"]],
        )


class TVShow(ItemEntity):
    isdir = True
    mediatype = "tvshow"

    def __init__(self, *args, **kwargs):
        super(TVShow, self).__init__(*args, **kwargs)
        self.url = self.plugin.routing.build_url("seasons", f"{self.item_id}/")
        self.new = None
        self._video_info = None

    @property
    def video_info(self):
        if self._video_info:
            return self._video_info
        return {
            **super(TVShow, self).video_info,
            "trailer": self.trailer_url,
            "mediatype": self.mediatype,
            "status": "окончен" if self.item["finished"] else "в эфире",
        }

    @property
    def seasons(self):
        return [
            Season(self, item=season, index=i) for i, season in enumerate(self.item["seasons"], 1)
        ]


class Season(ItemEntity):
    isdir = True
    mediatype = "season"

    def __init__(self, *args, **kwargs):
        super(Season, self).__init__(*args, **kwargs)
        self.tvshow = self.parent
        self.title = f"Сезон {self.index}"
        self.item_id = self.tvshow.item_id
        self.url = self.plugin.routing.build_url("season_episodes", self.item_id, f"{self.index}/")
        self.watching_info = self.tvshow.watching_info["seasons"][int(self.index) - 1]
        self.watching_status = self.watching_info["status"]

    @property
    def episodes(self):
        return [
            SeasonEpisode(self, item=episode_item, index=i)
            for i, episode_item in enumerate(self.item["episodes"], 1)
        ]

    @property
    def video_info(self):
        return {
            **self.tvshow.video_info.copy(),
            "season": self.index,
            "playcount": self.watching_status,
            "mediatype": self.mediatype,
        }


class SeasonEpisode(PlayableItem):
    mediatype = "episode"

    def __init__(self, *args, **kwargs):
        super(SeasonEpisode, self).__init__(*args, **kwargs)
        self.season = self.parent
        self.tvshow = self.season.tvshow
        self.item_id = self.tvshow.item_id
        self.video_data = self.item
        self.url = self.plugin.routing.build_url(
            "play", self.item_id, season_index=self.season.index, index=self.index
        )
        self.li_title = f"s{self.season.index:02d}e{self.index:02d}"
        if self.title:
            self.li_title = f"{self.li_title} | {self.title}"
        try:
            # In a tvshow season could be a case when some episodes are not available, but episode
            # numbers in response payload are set correctly.
            self.watching_info = self.season.watching_info["episodes"][int(self.index) - 1]
            self.watching_status = self.watching_info["status"]
        except IndexError:
            self.watching_info = self.watching_status = None

    @property
    def video_info(self):
        return {
            **self.tvshow.video_info.copy(),
            "season": self.season.index,
            "episode": self.index,
            "tvshowtitle": self.tvshow.title,
            "time": self.resume_time,
            "duration": self.watching_info["duration"],
            "playcount": self.watching_info["status"],
            "mediatype": self.mediatype,
        }

    @property
    def playable_list_item(self):
        li = super(SeasonEpisode, self).playable_list_item
        li.setProperties(video_number=self.index, season_number=self.season.index)
        return li


class Multi(ItemEntity):
    isdir = True

    def __init__(self, *args, **kwargs):
        super(Multi, self).__init__(*args, **kwargs)
        self.url = self.plugin.routing.build_url("episodes", f"{self.item_id}/")

    @property
    def videos(self):
        return [
            Episode(self, item=episode_item, index=i)
            for i, episode_item in enumerate(self.item["videos"], 1)
        ]

    @property
    def list_item(self):
        li = super(Multi, self).list_item
        li.setProperty("subtype", "multi")
        return li

    @property
    def video_info(self):
        return {**super(Multi, self).video_info, "playcount": self.watching_info["status"]}


class Episode(PlayableItem):
    mediatype = "episode"

    def __init__(self, *args, **kwargs):
        super(Episode, self).__init__(*args, **kwargs)
        self.item_id = self.parent.item_id
        self.video_data = self.item
        self.url = self.plugin.routing.build_url("play", self.item_id, index=self.index)
        self.li_title = f"e{self.index:02d}"
        if self.title:
            self.li_title = f"{self.li_title} | {self.title}"
        self.watching_status = self.watching_info["status"]

    @property
    def video_info(self):
        return {
            **self.parent.video_info.copy(),
            "episode": self.index,
            "tvshowtitle": self.title,
            "time": self.resume_time,
            "duration": self.watching_info["duration"],
            "playcount": self.item["watched"],
            "mediatype": self.mediatype,
        }

    @property
    def watching_info(self):
        return self.parent.watching_info["videos"][int(self.index) - 1]

    @property
    def playable_list_item(self):
        li = super(Episode, self).playable_list_item
        li.setProperties(video_number=self.index)
        return li


class Movie(PlayableItem):
    mediatype = "movie"

    def __init__(self, *args, **kwargs):
        super(Movie, self).__init__(*args, **kwargs)
        self.url = self.plugin.routing.build_url("play", self.item_id)

    @cached_property
    def video_data(self):
        if "videos" in self.item:
            return self.item["videos"][0]
        return self.plugin.items.get_api_item(self.item_id)["videos"][0]

    @property
    def video_info(self):
        return {
            **super(Movie, self).video_info,
            "time": self.resume_time,
            "duration": self.watching_info["duration"],
            "playcount": self.watching_info["status"],
            "trailer": self.trailer_url,
            "mediatype": self.mediatype,
        }

    @cached_property
    def watching_info(self):
        return self.plugin.client("watching").get(data={"id": self.item_id})["item"]["videos"][0]

    @property
    def playable_list_item(self):
        li = super(Movie, self).playable_list_item
        li.setProperties(video_number=1)
        return li
