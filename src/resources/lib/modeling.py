# -*- coding: utf-8 -*-
import re
import sys
from collections import namedtuple

import xbmcgui

from resources.lib.utils import cached_property
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

    def get(self, endpoint, data=None):
        resp = self.plugin.client(endpoint).get(data=data)
        items = [self.instantiate(item=item, index=i) for i, item in enumerate(resp["items"], 1)]
        return Response(items, resp.get("pagination"))

    @property
    def watching_movies(self):
        movies = []
        for i, small_item in enumerate(self.plugin.client("watching/movies").get()["items"]):
            item = self.get_api_item(small_item["id"])
            movies.append(self.instantiate(item=item))
        return movies

    @property
    def watching_tvshows(self):
        tvshows = []
        small_items = self.plugin.client("watching/serials").get(data={"subscribed": 1})["items"]
        for small_item in small_items:
            unwatched_episodes = small_item["new"]
            item = self.get_api_item(small_item["id"])
            tvhsow = self.instantiate(item=item)
            tvhsow.new = unwatched_episodes
            tvshows.append(tvhsow)
        return tvshows

    def get_api_item(self, item_id):
        return self.plugin.client("items/{}".format(item_id)).get()["item"]

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

    def get_playable(self, item=None, season_index=None, index=None):
        if isinstance(item, TVShow):
            return item.seasons[int(season_index) - 1].episodes[int(index) - 1]
        elif isinstance(item, Multi):
            return item.videos[int(index) - 1]
        else:
            return item


class ItemEntity(object):
    def __init__(self, parent, item, index=None):
        self.parent = parent
        self.item = item
        self.index = index
        self.item_id = self.item.get("id")
        self.title = self.item.get("title")
        self.poster = self.item.get("posters", {}).get("big")
        self._plugin = None

    @property
    def plugin(self):
        return self._plugin or self.parent.plugin

    @property
    def plot(self):
        final_plot = []
        if self.item["imdb_rating"]:
            final_plot.append("IMDB: {}".format(str(round(self.item["imdb_rating"], 1))))
        if self.item["kinopoisk_rating"]:
            final_plot.append(u"Кинопоиск: {}".format(str(round(self.item["kinopoisk_rating"], 1))))
        # a new line between the ratings and the plot
        if self.item["imdb_rating"] or self.item["kinopoisk_rating"]:
            final_plot.append("")
        final_plot.append(self.item["plot"])
        return "\n".join(final_plot)

    @property
    def status(self):
        if self.item["type"] == "serial" and self.item["finished"]:
            return u"окончен"
        elif self.item["type"] == "serial" and not self.item["finished"]:
            return u"в эфире"
        else:
            return

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
            "status": self.status,
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
            poster=self.poster,
            fanart=self.item.get("posters", {}).get("wide"),
            thumbnailImage=self.item.get("thumbnail", ""),
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
        return "<{!r}; item_id: {}; title: {}>".format(
            type(self).__name__, self.item_id, self.title.encode("utf-8")
        )


class PlayableItem(ItemEntity):
    isdir = False

    @property
    def media_url(self):
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
            "{}@{}".format(quality, stream): url
            for quality, urls in files.items()
            for stream, url in urls.items()
        }
        urls_list = natural_sort(flatten_urls_dict.keys())
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
                return files[natural_sort(files.keys())[-1]][stream_type]

    @property
    def list_item(self):
        li = super(PlayableItem, self).list_item
        li.setProperty("isPlayable", "true")
        return li

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
                    "inputstreamaddon": helper.inputstream_addon,
                    "inputstream.adaptive.manifest_type": "hls",
                }
        return {}

    @property
    def playable_list_item(self):
        properties = {
            "item_id": self.item_id,
            "play_duration": self.video_info["duration"],
            "play_resumetime": self.video_info["time"],
            "playcount": self.video_info["playcount"],
            "imdbnumber": self.video_info["imdbnumber"],
        }
        properties.update(self.hls_properties)
        return self.plugin.list_item(
            getattr(self, "li_title", self.title),
            path=self.media_url,
            properties=properties,
            poster=self.poster,
            subtitles=[subtitle["url"] for subtitle in self.video_data["subtitles"]],
        )


class TVShow(ItemEntity):
    isdir = True
    mediatype = "tvshow"

    def __init__(self, *args, **kwargs):
        super(TVShow, self).__init__(*args, **kwargs)
        self.url = self.plugin.routing.build_url("seasons", "{}/".format(self.item_id))
        self.new = None

    @property
    def video_info(self):
        base_video_info = super(TVShow, self).video_info
        base_video_info.update({"trailer": self.trailer_url, "mediatype": self.mediatype})
        return base_video_info

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
        self.title = "Сезон {}".format(self.index)
        self.item_id = self.tvshow.item_id
        self.url = self.plugin.routing.build_url(
            "season_episodes", self.item_id, "{}/".format(self.index)
        )
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
        base_video_info = self.tvshow.video_info
        base_video_info.update(
            {"season": self.index, "playcount": self.watching_status, "mediatype": self.mediatype}
        )
        return base_video_info


class SeasonEpisode(PlayableItem):
    mediatype = "episode"

    def __init__(self, *args, **kwargs):
        super(SeasonEpisode, self).__init__(*args, **kwargs)
        self.season = self.parent
        self.tvshow = self.season.tvshow
        self.item_id = self.tvshow.item_id
        self.video_data = self.item
        self.url = self.plugin.routing.build_url(
            "play", self.item_id, "seasons", self.season.index, "episodes", self.index
        )
        self.li_title = "s{:02d}e{:02d}".format(self.season.index, self.index)
        if self.title:
            self.li_title = u"{} | {}".format(self.li_title, self.title)
        try:
            # In a tvshow season could be a case when some episodes are not available, but episode
            # numbers in response payload are set correctly.
            self.watching_info = self.season.watching_info["episodes"][int(self.index) - 1]
            self.watching_status = self.watching_info["status"]
        except IndexError:
            self.watching_info = self.watching_status = None

    @property
    def video_info(self):
        base_video_info = self.tvshow.video_info
        base_video_info.update(
            {
                "season": self.season.index,
                "episode": self.index,
                "tvshowtitle": self.tvshow.title,
                "time": self.watching_info["time"],
                "duration": self.watching_info["duration"],
                "playcount": self.watching_info["status"],
                "mediatype": self.mediatype,
            }
        )
        return base_video_info

    @property
    def playable_list_item(self):
        li = super(SeasonEpisode, self).playable_list_item
        li.setProperties(video_number=self.index, season_number=self.season.index)
        return li


class Multi(ItemEntity):
    isdir = True

    def __init__(self, *args, **kwargs):
        super(Multi, self).__init__(*args, **kwargs)
        self.url = self.plugin.routing.build_url("episodes", "{}/".format(self.item_id))

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
        base_video_info = super(Multi, self).video_info
        base_video_info.update({"playcount": self.watching_info["status"]})
        return base_video_info


class Episode(PlayableItem):
    mediatype = "episode"

    def __init__(self, *args, **kwargs):
        super(Episode, self).__init__(*args, **kwargs)
        self.item_id = self.parent.item_id
        self.video_data = self.item
        self.url = self.plugin.routing.build_url(
            "play", self.item_id, "seasons", 1, "episodes", self.index
        )
        self.li_title = "e{:02d}".format(self.index)
        if self.title:
            self.li_title = u"{} | {}".format(self.li_title, self.title)

    @property
    def video_info(self):
        base_video_info = self.parent.video_info
        base_video_info.update(
            {
                "episode": self.index,
                "tvshowtitle": self.title,
                "time": self.watching_info["time"],
                "duration": self.watching_info["duration"],
                "playcount": self.item["watched"],
                "mediatype": self.mediatype,
            }
        )
        return base_video_info

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
        self.url = self.plugin.routing.build_url(
            "play", self.item_id, "seasons", 1, "episodes", self.index
        )

    @property
    def video_data(self):
        if "videos" in self.item:
            return self.item["videos"][0]
        return self.plugin.items.get_api_item(self.item_id)["videos"][0]

    @property
    def video_info(self):
        base_video_info = super(Movie, self).video_info
        base_video_info.update(
            {
                "time": self.watching_info["time"],
                "duration": self.watching_info["duration"],
                "playcount": self.watching_info["status"],
                "trailer": self.trailer_url,
                "mediatype": self.mediatype,
            }
        )
        return base_video_info

    @property
    def list_item(self):
        li = super(Movie, self).list_item
        li.setResumeTime(self.watching_info["time"], self.watching_info["duration"])
        return li

    @cached_property
    def watching_info(self):
        return self.plugin.client("watching").get(data={"id": self.item_id})["item"]["videos"][0]

    @property
    def playable_list_item(self):
        li = super(Movie, self).playable_list_item
        li.setProperties(video_number=1)
        return li
