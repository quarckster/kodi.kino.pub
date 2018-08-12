# -*- coding: utf-8 -*-
import urllib
import xbmc


def dict_merge(old, new):
    n = old.copy()
    n.update(new)
    return n


def get_mlink(video, quality="480p", streamType="http"):
    """Get media link.

    Args:
        video: json dict from api call
        quality: video quality [480p, 720p, 1080p]

    """

    def normalize(qual):
        """Normalize quality param"""
        qual = str(qual)
        return int(qual.lower().replace("p", "").replace("3d", "1080"))

    def geturl(url, streamType="http"):
        return url[streamType] if isinstance(url, dict) else url

    url = ""
    files = video["files"]
    files = sorted(files, key=lambda x: normalize(x["quality"]), reverse=False)

    # check if auto quality
    if quality.lower() == "auto":
        return geturl(files[-1]["url"], streamType)

    # manual param quality
    for f in files:
        f["quality"] = normalize(f["quality"])
        if f["quality"] == quality:
            return geturl(f["url"], streamType)

    for f in reversed(files):
        if normalize(f["quality"]) <= normalize(quality):
            return geturl(f["url"], streamType)
        url = geturl(f["url"], streamType)
    return url


def video_info(item, extend=None):

    def get_plot():
        plot_1 = item["plot"]
        if item["kinopoisk_rating"]:
            plot_2 = u"Кинопоиск: {}".format(str(round(item["kinopoisk_rating"], 1)))
        else:
            plot_2 = u"Кинопоиск: нет"
        if item["imdb_rating"]:
            plot_3 = u"IMDB: {}".format(str(round(item["imdb_rating"], 1)))
        else:
            plot_3 = u"IMDB: нет"
        return "\n".join([plot_1, plot_2, plot_3])

    def get_status():
        if item["finished"] and item["type"] == "serial":
            return u"окончен"
        else:
            if item["type"] == "serial":
                return "в эфире"

    info = {
        "year": int(item["year"]),
        "genre": ",".join([x["title"] for x in item["genres"]]),
        "rating": float(item["rating"]),
        "cast": item["cast"].split(","),
        "director": item["director"],
        "plot": get_plot(),
        "title": item["title"],
        "duration": item.get("duration", {}).get("average"),
        "code": item["imdb"],
        "status": get_status(),
        "votes": item["rating_votes"]
    }
    if extend and isinstance(extend, dict):
        info.update(extend)
    return info


def get_internal_link(action, params=None):
    """Form internal link for plugin navigation"""
    params = "?{}".format(urllib.urlencode(params)) if params else ""
    return "plugin://video.kino.pub/{}{}".format(action, params)


def nav_internal_link(action, params):
    xbmc.executebuiltin("Container.Update({})".format(get_internal_link(action, params)))


def notice(message, heading="", time=4000):
    xbmc.executebuiltin('XBMC.Notification("{}", "{}", "{}")'.format(heading, message, time))


def trailer_link(item):
    if item.get("trailer"):
        trailer = item["trailer"]
        return get_internal_link("trailer", {"id": item["id"], "sid": trailer["id"]})
    return None
