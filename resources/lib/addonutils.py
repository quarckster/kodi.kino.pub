# -*- coding: utf-8 -*-
import json
import re
import sys
import time
import urllib
import urlparse
from functools import wraps

import xbmc
import xbmcgui

from data import __id__, __settings__, __plugin__


def dict_merge(old, new):
    n = old.copy()
    n.update(new)
    return n


def get_mlink(video, stream_type=None, quality=None, ask_quality="false"):
    """Get media link.

    Args:
        video: a dict from api call
        quality: video quality (480p, 720p, 1080p)
        stream_type: hls, hls2, hls4, http
        ask_quality: "false" or "true"
    """

    def natural_sort(l):
        def convert(text):
            return int(text) if text.isdigit() else text.lower()

        def alphanum_key(key):
            return [convert(c) for c in re.split('([0-9]+)', key)]

        return sorted(l, key=alphanum_key)

    files = {f["quality"]: f["url"] for f in video["files"]}
    flatten_urls_dict = {"{}@{}".format(quality, stream): url for quality, urls in files.items()
                         for stream, url in urls.items()}
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
                return u"в эфире"

    info = {
        "year": int(item["year"]),
        "genre": ", ".join([x["title"] for x in item["genres"]]),
        "rating": float(item["rating"]),
        "cast": [x.strip() for x in item["cast"].split(",")],
        "director": item["director"],
        "plot": get_plot(),
        "title": item["title"],
        "duration": item.get("duration", {}).get("average"),
        "code": item["imdb"],
        "status": get_status(),
        "votes": item["rating_votes"],
        "country": ", ".join([x["title"] for x in item["countries"]])
    }
    if extend and isinstance(extend, dict):
        info.update(extend)
    return info


def get_internal_link(path, **params):
    """Form internal link for plugin navigation"""
    return urlparse.urlunsplit(("plugin", __id__, path, urllib.urlencode(params), ""))


def nav_internal_link(action, **params):
    xbmc.executebuiltin("Container.Update({})".format(get_internal_link(action, **params)))


def notice(message, heading="", time=4000):
    xbmc.executebuiltin('XBMC.Notification("{}", "{}", "{}")'.format(heading, message, time))


def trailer_link(item):
    if item.get("trailer"):
        trailer = item["trailer"]
        return get_internal_link("trailer", id=item["id"], sid=trailer["id"])
    return None


def update_device_info(force=False):
    from client import KinoPubClient
    # Update device info
    deviceInfoUpdate = __settings__.getSetting("device_info_update")
    if force or not deviceInfoUpdate or int(deviceInfoUpdate) + 1800 < int(time.time()):
        infoLabels = [
            '"System.BuildVersion"',
            '"System.FriendlyName"',
            '"System.KernelVersion"'
        ]
        result = "Busy"
        payload = {
            "jsonrpc": "2.0",
            "method": "XBMC.GetInfoLabels",
            "id": 1,
            "params": {"labels": [",".join(infoLabels)]}
        }
        while "Busy" in result:
            result = xbmc.executeJSONRPC(json.dumps(payload))
        result = json.loads(result)["result"]
        title = result.get("System.FriendlyName")
        hardware = result.get("System.KernelVersion")
        software = "Kodi/{}".format(result.get("System.BuildVersion"))
        KinoPubClient("device/notify").post(data={
            "title": title,
            "hardware": hardware,
            "software": software
        })
        __settings__.setSetting("device_info_update", str(int(float(time.time()))))


class Request(object):

    @property
    def handle(self):
        return int(sys.argv[1])

    @property
    def path(self):
        return sys.argv[0].replace(__plugin__, "")

    @property
    def args(self):
        return dict(urlparse.parse_qsl(sys.argv[2].lstrip("?")))


request = Request()

ROUTES = dict()


def route(path):
    def decorator_route(f):
        ROUTES[path] = f

        @wraps(f)
        def wrapper_route(*args, **kwargs):
            xbmc.log("{} : {}. {}".format(__plugin__, f.__name__, str(request.args)))
            return f(*args, **kwargs)
        return wrapper_route
    return decorator_route
