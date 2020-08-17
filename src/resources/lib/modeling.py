# -*- coding: utf-8 -*-
from collections import namedtuple

from resources.lib.utils import cached_property

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
        for i, item in enumerate(self.plugin.client("watching/movies").get()["items"]):
            movies.append(self.instantiate(item_id=item["id"], index=i))
        return movies

    @property
    def watching_tvshows(self):
        tvshows = []
        for item in self.plugin.client("watching/serials").get(data={"subscribed": 1})["items"]:
            tvshows.append(self.instantiate(item_id=item["id"], item=item))
        return tvshows

    def _get_item(self, item_id):
        return self.plugin.client("items/{}".format(item_id)).get()["item"]

    def instantiate(self, item_id=None, item=None, index=None):
        if item_id and not item:
            item = self._get_item(item_id)
        if item and item_id:
            item.update(self._get_item(item_id))
        if item["subtype"] == "multi":
            item_entity = Multi
        else:
            item_entity = self.content_type_map[item["type"]]
        return item_entity(self, item, index=index)


class ItemEntity(object):
    def __init__(self, parent, item, index=None):
        self.parent = parent
        self.item = item
        self.index = index
        self.item_id = self.item.get("id")
        self.title = self.item.get("title")
        self.number = self.item.get("number")
        self.poster = self.item.get("posters", {}).get("big")

    @property
    def plugin(self):
        return self.parent.plugin

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
            poster=self.item.get("posters", {}).get("big"),
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

    def __repr__(self):
        return "{!r}, item_id: {}, title: {}".format(
            type(self).__name__, self.item_id, self.title.encode("utf-8")
        )


class TVShow(ItemEntity):
    isdir = True
    mediatype = "tvshow"

    def __init__(self, *args, **kwargs):
        super(TVShow, self).__init__(*args, **kwargs)
        self.url = self.plugin.routing.build_url("seasons", self.item_id)
        self.new = self.item.get("new", "")

    @property
    def video_info(self):
        base_video_info = super(TVShow, self).video_info
        base_video_info.update({"trailer": self.trailer_url, "mediatype": self.mediatype})
        return base_video_info

    @property
    def seasons(self):
        return [Season(self, season) for season in self.item["seasons"]]


class Season(ItemEntity):
    isdir = True
    mediatype = "season"

    def __init__(self, *args, **kwargs):
        super(Season, self).__init__(*args, **kwargs)
        self.tvshow = self.parent
        self.title = "Сезон {}".format(self.number)
        self.item_id = self.tvshow.item_id
        self.url = self.plugin.routing.build_url("season_episodes", self.item_id, self.number)
        self.watching_info = self.tvshow.watching_info["seasons"][self.number - 1]
        self.watching_status = self.watching_info["status"]

    @property
    def episodes(self):
        return [SeasonEpisode(self, episode_item) for episode_item in self.item["episodes"]]

    @property
    def video_info(self):
        base_video_info = self.tvshow.video_info
        base_video_info.update(
            {"season": self.number, "playcount": self.watching_status, "mediatype": self.mediatype}
        )
        return base_video_info


class SeasonEpisode(ItemEntity):
    isdir = False
    mediatype = "episode"

    def __init__(self, *args, **kwargs):
        super(SeasonEpisode, self).__init__(*args, **kwargs)
        self.season = self.parent
        self.tvshow = self.season.tvshow
        self.item_id = self.tvshow.item_id
        self.url = self.plugin.routing.build_url("play", self.item_id, self.number)
        self.li_title = "s{:02d}e{:02d}".format(self.season.number, self.number)
        if self.title:
            self.li_title = u"{} | {}".format(self.li_title, self.title)
        try:
            # In a tvshow season could be a case when some episodes are not available, but episode
            # numbers in response payload are set correctly.
            self.watching_info = self.season.watching_info["episodes"][self.number - 1]
            self.watching_status = self.watching_info["status"]
        except IndexError:
            self.watching_info = self.watching_status = None

    @property
    def video_info(self):
        base_video_info = self.tvshow.video_info
        base_video_info.update(
            {
                "season": self.season.number,
                "episode": self.number,
                "tvshowtitle": self.tvshow.title,
                "time": self.watching_info["time"],
                "duration": self.watching_info["duration"],
                "playcount": self.watching_info["status"],
                "mediatype": self.mediatype,
            }
        )
        return base_video_info

    @property
    def list_item(self):
        li = super(SeasonEpisode, self).list_item
        li.setProperty("isPlayable", "true")
        return li


class Multi(ItemEntity):
    isdir = True

    def __init__(self, *args, **kwargs):
        super(Multi, self).__init__(*args, **kwargs)
        self.url = self.plugin.routing.build_url("episodes", self.item_id)

    @property
    def videos(self):
        return [Episode(self, episode_item) for episode_item in self.item["videos"]]

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


class Episode(ItemEntity):
    isdir = False
    mediatype = "episode"

    def __init__(self, *args, **kwargs):
        super(Episode, self).__init__(*args, **kwargs)
        self.item_id = self.parent.item_id
        self.url = self.plugin.routing.build_url("play", self.item_id, self.number)
        self.li_title = "e{:02d}".format(self.number)
        if self.title:
            self.li_title = u"{} | {}".format(self.li_title, self.title)

    @property
    def video_info(self):
        base_video_info = self.parent.video_info
        base_video_info.update(
            {
                "episode": self.number,
                "tvshowtitle": self.title,
                "time": self.watching_info["time"],
                "duration": self.watching_info["duration"],
                "playcount": self.item["watched"],
                "mediatype": self.mediatype,
            }
        )
        return base_video_info

    @property
    def list_item(self):
        li = super(Episode, self).list_item
        li.setProperty("isPlayable", "true")
        return li

    @property
    def watching_info(self):
        return self.parent.watching_info["videos"][self.number - 1]


class Movie(ItemEntity):
    isdir = False
    mediatype = "movie"

    def __init__(self, *args, **kwargs):
        super(Movie, self).__init__(*args, **kwargs)
        self.url = self.plugin.routing.build_url("play", self.item_id, self.index)

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
        li.setProperty("isPlayable", "true")
        li.setResumeTime(self.watching_info["time"], self.watching_info["duration"])
        return li

    @cached_property
    def watching_info(self):
        return self.plugin.client("watching").get(data={"id": self.item_id})["item"]["videos"][0]
