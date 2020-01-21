# -*- coding: utf-8 -*-
import json
import re
import sys

import xbmc
import xbmcgui


def set_window_property(value):
    xbmcgui.Window(10000).clearProperty("video.kino.pub-playback_data")
    if not isinstance(value, str):
        value = json.dumps(value)
    xbmcgui.Window(10000).setProperty("video.kino.pub-playback_data", value)


def get_window_property(index):
    data = json.loads(xbmcgui.Window(10000).getProperty("video.kino.pub-playback_data"))[index]
    xbmcgui.Window(10000).clearProperty("video.kino.pub-playback_data")
    return data


def get_mlink(video, stream_type=None, quality=None, ask_quality="false"):
    """Get media link.

    Args:
        video: a dict from api call
        quality: video quality (480p, 720p, 1080p, 2160p)
        stream_type: hls, hls2, hls4, http
        ask_quality: "false" or "true"
    """

    def natural_sort(l):
        def convert(text):
            return int(text) if text.isdigit() else text.lower()

        def alphanum_key(key):
            return [convert(c) for c in re.split("([0-9]+)", key)]

        return sorted(l, key=alphanum_key)

    files = {f["quality"]: f["url"] for f in video["files"]}
    flatten_urls_dict = {
        "{}@{}".format(quality, stream): url
        for quality, urls in list(files.items())
        for stream, url in list(urls.items())
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


def build_plot(item):
    final_plot = []
    if item["imdb_rating"]:
        final_plot.append("IMDB: {}".format(str(round(item["imdb_rating"], 1))))
    if item["kinopoisk_rating"]:
        final_plot.append("Кинопоиск: {}".format(str(round(item["kinopoisk_rating"], 1))))
    # a new line between the ratings and the plot
    if item["imdb_rating"] or item["kinopoisk_rating"]:
        final_plot.append("")
    final_plot.append(item["plot"])
    return "\n".join(final_plot)


def get_status(item):
    if item["type"] == "serial" and item["finished"]:
        return "окончен"
    elif item["type"] == "serial" and not item["finished"]:
        return "в эфире"
    else:
        return


def video_info(item, extend=None):
    info = {
        "year": int(item["year"]),
        "genre": ", ".join([x["title"] for x in item["genres"]]),
        "rating": float(item["rating"]),
        "cast": [x.strip() for x in item["cast"].split(",")],
        "director": item["director"],
        "plot": build_plot(item),
        "title": item["title"],
        "duration": item.get("duration", {}).get("average"),
        "imdbnumber": item["imdb"],
        "status": get_status(item),
        "votes": item["rating_votes"],
        "country": ", ".join([x["title"] for x in item["countries"]]),
    }
    if extend and isinstance(extend, dict):
        info.update(extend)
    return info


def notice(message, heading="", time=4000):
    xbmc.executebuiltin('XBMC.Notification("{}", "{}", "{}")'.format(heading, message, time))


def trailer_link(item):
    from resources.lib.main import plugin

    if "trailer" in item:
        return plugin.routing.build_url("trailer", item["id"])
    return None
