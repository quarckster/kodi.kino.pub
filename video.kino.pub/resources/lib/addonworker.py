# -*- coding: utf-8 -*-
import authwindow as auth
import json
import sys
import time
import urllib
import urllib2
import urlparse
import xbmcplugin
import xbmcgui
import xbmc
import xbmcaddon
from addonutils import (dict_merge, get_internal_link, get_mlink, nav_internal_link, notice,
                        trailer_link, video_info)


__id__ = "video.kino.pub"
__addon__ = xbmcaddon.Addon(id=__id__)
__settings__ = xbmcaddon.Addon(id=__id__)
__skinsdir__ = "DefaultSkin"
__language__ = __addon__.getLocalizedString
__plugin__ = "plugin://{}".format(__id__)

DEFAULT_QUALITY = __settings__.getSetting("video_quality")
DEFAULT_STREAM_TYPE = __settings__.getSetting("stream_type")

_ADDON_PATH = xbmc.translatePath(__addon__.getAddonInfo("path"))
if sys.platform in ("win32", "win64"):
    _ADDON_PATH = _ADDON_PATH.decode("utf-8")

handle = int(sys.argv[1])
Auth = auth.Auth(__settings__)


class KinoPubClient(object):
    url = "http://api.service-kp.com/v1"

    def __init__(self, action):
        self.action = action

    def refresh_token(self):
        status, resp = Auth.get_token(refresh=True)
        if status != Auth.SUCCESS:
            xbmc.log("Refresh access token because it expired")
            xbmc.log(resp)
            if resp["status"] == 400:
                xbmc.log("Status is 400, we need to reauth")
                Auth.reauth()
                actionLogin({})
            else:
                notice("Повторите попытку позже.", "Ошибка", time=10000)

    def _make_request(self, request, timeout=600):
        if not Auth.is_token_valid:
            self.refresh_token()
        request.add_header("Authorization", "Bearer {}".format(Auth.access_token))
        try:
            response = urllib2.urlopen(request, timeout=timeout)
            data = json.loads(response.read())
            return data
        except urllib2.HTTPError as e:
            try:
                data = json.loads(e.read())
            except Exception:
                data = {"status": e.code, "error": "unknown server error"}
            return data
        except Exception as e:
            xbmc.log(e.message, level=xbmc.LOGERROR)
            return {
                "status": 105,
                "name": "Name Not Resolved",
                "message": "Name not resolved",
                "code": 0
            }

    def get(self, data=""):
        data = "?{}".format(urllib.urlencode(data)) if data else ""
        request = urllib2.Request("{}/{}{}".format(self.url, self.action, data))
        return self._make_request(request)

    def post(self, data=""):
        data = urllib.urlencode(data)
        request = urllib2.Request("{}/{}".format(self.url, self.action), data=data)
        return self._make_request(request)


def show_pagination(pagination, action, qp):
    # Add "next page" button
    if (pagination and int(pagination["current"])) + 1 <= int(pagination["total"]):
        qp["page"] = int(pagination["current"]) + 1
        li = xbmcgui.ListItem("[COLOR FFFFF000]Вперёд[/COLOR]")
        link = get_internal_link(action, qp)
        xbmcplugin.addDirectoryItem(handle, link, li, True)
    xbmcplugin.endOfDirectory(handle)


def show_items(items, add_indexes=False):
    xbmc.log("{} : show_items. Total items: {}".format(__plugin__, str(len(items))))
    xbmcplugin.setContent(handle, "movies")
    # Fill list with items
    for index, item in enumerate(items, 1):
        li = xbmcgui.ListItem(item["title"].encode("utf-8"))
        if add_indexes:
            li.setLabel("{}. {}".format(index, li.getLabel()))
        li.setInfo("Video", video_info(item, {"trailer": trailer_link(item)}))
        li.setArt({"poster": item["posters"]["big"]})
        # If not serials or multiseries movie, create playable item
        if item["type"] not in ["serial", "docuserial", "tvshow"] and not item["subtype"]:
            link = get_internal_link("play", {"id": item["id"], "video": 1})
            li.setProperty("IsPlayable", "true")
            isdir = False
        else:
            link = get_internal_link("view", {"id": item["id"]})
            isdir = True
        xbmcplugin.addDirectoryItem(handle, link, li, isdir)


def add_default_headings(qp, fmt="slp"):
    # qp - dict, query paramters
    # fmt - show format
    # s - show search
    # l - show last
    # p - show popular
    # s - show alphabet sorting
    # g - show genres folder
    if "s" in fmt:
        li = xbmcgui.ListItem("[COLOR FFFFF000]Поиск[/COLOR]")
        xbmcplugin.addDirectoryItem(handle, get_internal_link("search", qp), li, False)
    if "l" in fmt:
        li = xbmcgui.ListItem("[COLOR FFFFF000]Последние[/COLOR]")
        xbmcplugin.addDirectoryItem(handle, get_internal_link("items", qp), li, True)
    if "p" in fmt:
        li = xbmcgui.ListItem("[COLOR FFFFF000]Популярные[/COLOR]")
        xbmcplugin.addDirectoryItem(handle,
            get_internal_link("items", dict_merge(qp, {"sort": "-rating"})), li, True)
    if "a" in fmt:
        li = xbmcgui.ListItem("[COLOR FFFFF000]По алфавиту[/COLOR]")
        xbmcplugin.addDirectoryItem(handle, get_internal_link("alphabet", qp), li, True)
    if "g" in fmt:
        li = xbmcgui.ListItem("[COLOR FFFFF000]Жанры[/COLOR]")
        xbmcplugin.addDirectoryItem(handle, get_internal_link("genres", qp), li, True)


def route(fakeSys=None):
    if fakeSys:
        current = fakeSys.split("?")[0]
        qs = fakeSys.split("?")["?" in fakeSys]
    else:
        current = sys.argv[0]
        qs = sys.argv[2]
    action = current.replace(__plugin__, "").lstrip("/") or "login"
    actionFn = "action{}".format(action.title())
    qp = dict(urlparse.parse_qsl(qs.lstrip("?"))) if qs else {}
    xbmc.log("{} : route. {}".format(__plugin__, str(qp)))
    globals()[actionFn](qp)


# Entry point
def init():
    route()


def update_device_info(force=False):
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
        try:
            KinoPubClient("device/notify").post(data={
                "title": title,
                "hardware": hardware,
                "software": software
            })
            __settings__.setSetting("device_info_update", str(int(float(time.time()))))
        except Exception:
            pass


def showActivationWindow():
    xbmc.log("{}: actionLogin - No acess_token. Show modal auth".format(__plugin__))
    wn = auth.AuthWindow(
        "auth.xml",
        _ADDON_PATH,
        __skinsdir__,
        settings=__settings__,
        afterAuth=update_device_info
    )
    wn.doModal()
    xbmc.log("{}: actionLogin - Close modal auth".format(__plugin__))


# Actions
def actionLogin(qp):
    xbmc.log("{} : actionLogin. {}".format(__plugin__, str(qp)))

    # if no access token exists
    if not Auth.access_token:
        showActivationWindow()
        actionLogin(qp)
        return
    else:
        if Auth.access_token_expire - int(time.time()) <= 15 * 60:
            # try to refresh token
            Auth.get_token(refresh=True)

        # test API call
        response = KinoPubClient("types").get()
        if response["status"] == 401:
            status, __ = Auth.get_token(refresh=True)
            if status != Auth.SUCCESS:
                # reset access_token
                Auth.reauth()
                actionLogin(qp)
        elif response["status"] == 200:
            update_device_info()
            actionIndex(qp)
        else:
            notice("Повторите попытку позже ({}).".format(response["status"], "Ошибка", time=10000))


def actionIndex(qp):
    """Main screen - show type list"""
    xbmc.log("{}: actionIndex. {}".format( __plugin__, str(qp)))
    xbmc.executebuiltin("Container.SetViewMode(0)")
    if "type" in qp:
        add_default_headings(qp, "slpga")
    else:
        response = KinoPubClient("types").get()
        if response["status"] == 200:
            add_default_headings(qp)
            li = xbmcgui.ListItem("[COLOR FFFFF000]ТВ[/COLOR]")
            xbmcplugin.addDirectoryItem(handle, get_internal_link("tv"), li, True)
            li = xbmcgui.ListItem("[COLOR FFFFF000]Закладки[/COLOR]")
            xbmcplugin.addDirectoryItem(handle, get_internal_link("bookmarks"), li, True)
            li = xbmcgui.ListItem("[COLOR FFFFF000]Я смотрю[/COLOR]")
            xbmcplugin.addDirectoryItem(handle, get_internal_link("watching"), li, True)
            li = xbmcgui.ListItem("[COLOR FFFFF000]Подборки[/COLOR]")
            xbmcplugin.addDirectoryItem(handle, get_internal_link("collections"), li, True)
            for i in response["items"]:
                li = xbmcgui.ListItem(i["title"].encode("utf-8"))
                link = get_internal_link("index", {"type": i["id"]})
                xbmcplugin.addDirectoryItem(handle, link, li, True)
    xbmcplugin.endOfDirectory(handle)


def actionTv(qp):
    response = KinoPubClient("tv/index").get()
    if response["status"] == 200:
        for ch in response["channels"]:
            li = xbmcgui.ListItem(ch["title"].encode("utf-8"), iconImage=ch["logos"]["s"])
            xbmcplugin.addDirectoryItem(handle, ch["stream"], li, False)
    xbmcplugin.endOfDirectory(handle)


def actionGenres(qp):
    response = KinoPubClient("genres").get(data={"type": qp.get("type", "")})
    if response["status"] == 200:
        add_default_headings(qp, "")
        for genre in response["items"]:
            li = xbmcgui.ListItem(genre["title"].encode("utf-8"))
            link = get_internal_link("items", {"type": qp.get("type"), "genre": genre["id"]})
            xbmcplugin.addDirectoryItem(handle, link, li, True)
        xbmcplugin.endOfDirectory(handle)
    else:
        notice(response["message"], response["name"])


def actionItems(qp):
    """List items with pagination

        Args:
            qp: dict, query parameters for item filtering
    """
    response = KinoPubClient("items").get(data=qp)
    if response["status"] == 200:
        pagination = response["pagination"]
        add_default_headings(qp, "s")
        show_items(response["items"])
        show_pagination(pagination, "items", qp)
    else:
        notice(response["message"], response["name"])


def actionView(qp):
    """Show items

    If item type is movie with more than 1 episodes - show those episodes. If item type is serial,
    docuserial, tvshow - show seasons. If parameter season is set - show episodes. Otherwise play
    content.
    """
    response = KinoPubClient("items/{}".format(qp["id"])).get()
    if response["status"] == 200:
        item = response["item"]
        watching_info = KinoPubClient("watching").get(data={"id": item["id"]})["item"]
        # If serial instance or multiseries film show navigation, else start play
        if item["type"] in ["serial", "docuserial", "tvshow"]:
            if "season" in qp:
                for season in item["seasons"]:
                    if int(season["number"]) == int(qp["season"]):
                        watching_season = watching_info["seasons"][season["number"] - 1]
                        selectedEpisode = False
                        xbmcplugin.setContent(handle, "episodes")
                        for episode_number, episode in enumerate(season["episodes"], 1):
                            episode_title = "s{:02d}e{:02d}".format(
                                season["number"], episode_number)
                            if episode["title"]:
                                episode_title = "{} | {}".format(episode_title, episode["title"])
                            li = xbmcgui.ListItem(
                                episode_title,
                                iconImage=episode["thumbnail"],
                                thumbnailImage=episode["thumbnail"]
                            )
                            li.setInfo("Video", video_info(item, {
                                "season": int(season["number"]),
                                "episode": episode_number,
                                "duration": int(episode["duration"]),
                            }))
                            li.setInfo("Video", {"playcount": int(episode["watched"])})
                            li.setArt({"poster": item["posters"]["big"]})
                            li.setProperty("IsPlayable", "true")
                            status = watching_season["episodes"][episode_number - 1]["status"]
                            if status < 1 and not selectedEpisode:
                                selectedEpisode = True
                                li.select(selectedEpisode)
                            link = get_internal_link("play", {
                                "id": item["id"],
                                "season": int(season["number"]),
                                "episode": episode_number
                            })
                            xbmcplugin.addDirectoryItem(handle, link, li, False)
                        break
                xbmcplugin.endOfDirectory(handle)
            else:
                selectedSeason = False
                xbmcplugin.setContent(handle, "tvshows")
                for season in item["seasons"]:
                    season_title = "Сезон {}".format(season["number"])
                    watching_season = watching_info["seasons"][season["number"] - 1]
                    li = xbmcgui.ListItem(season_title)
                    li.setInfo("Video", video_info(item, {
                        "season": int(season["number"]),
                    }))
                    li.setArt({"poster": item["posters"]["big"]})
                    if watching_season["status"] < 1 and not selectedSeason:
                        selectedSeason = True
                        li.select(selectedSeason)
                    link = get_internal_link("view", {"id": qp["id"], "season": season["number"]})
                    xbmcplugin.addDirectoryItem(handle, link, li, True)
                xbmcplugin.endOfDirectory(handle)
        elif "videos" in item and len(item["videos"]) > 1:
            xbmcplugin.setContent(handle, "episodes")
            for video_number, video in enumerate(item["videos"], 1):
                episode_title = "e{:02d}".format(video_number)
                if video["title"]:
                    episode_title = "{} | {}".format(episode_title, video["title"])
                li = xbmcgui.ListItem(
                    episode_title,
                    iconImage=video["thumbnail"],
                    thumbnailImage=video["thumbnail"]
                )
                li.setInfo("Video", video_info(item, {
                    "season": 1,
                    "episode": video_number
                }))
                li.setInfo("Video", {"playcount": int(video["watched"])})
                li.setArt({"poster": item["posters"]["big"]})
                li.setProperty("IsPlayable", "true")
                link = get_internal_link("play", {"id": item["id"], "video": video_number})
                xbmcplugin.addDirectoryItem(handle, link, li, False)
            xbmcplugin.endOfDirectory(handle)


def actionPlay(qp):
    response = KinoPubClient("items/{}".format(qp["id"])).get()
    if response["status"] == 200:
        item = response["item"]
        season_number = 0
        if "season" in qp:
            # process episode
            for season in item["seasons"]:
                if int(qp["season"]) == int(season["number"]):
                    season_number = season["number"]
                    for episode_number, episode in enumerate(season["episodes"], 1):
                        if episode_number == int(qp["episode"]):
                            videoObject = episode
                            episode_title = "s{:02d}e{:02d}".format(
                                season["number"], episode_number)
                            if episode["title"]:
                                episode_title = "{} | {}".format(episode_title, episode["title"])
                            liObject = xbmcgui.ListItem(episode_title)
                            liObject.setInfo("video", {
                                "season": season["number"],
                                "episode": episode_number,
                                "duration": videoObject.get("duration")
                            })
                    break
        elif "video" in qp:
            # process video
            for video_number, video in enumerate(item["videos"], 1):
                if video_number == int(qp["video"]):
                    videoObject = video
                    if len(item["videos"]) > 1:
                        episode_title = "e{:02d}".format(video_number)
                        if video["title"]:
                            episode_title = "{} | {}".format(episode_title, video["title"])
                        liObject = xbmcgui.ListItem(episode_title)
                        liObject.setInfo("video", {
                            "season": 1,
                            "episode": video_number
                        })
                    else:
                        liObject = xbmcgui.ListItem(item["title"])
        subtitles = [subtitle["url"] for subtitle in videoObject["subtitles"]]
        if subtitles:
            liObject.setSubtitles(subtitles)
        if "files" not in videoObject:
            notice("Видео обновляется и временно не доступно!", "Видео в обработке", time=8000)
            return
        url = get_mlink(
            videoObject,
            quality=DEFAULT_QUALITY,
            streamType=DEFAULT_STREAM_TYPE
        )
        KinoPubClient("watching/marktime").get(data={
            "id": qp["id"],
            "video": videoObject["number"],
            "time": videoObject["duration"],
            "season": season_number
        })
        liObject.setPath(url)
        xbmcplugin.setResolvedUrl(handle, True, liObject)


def actionTrailer(qp):
    response = KinoPubClient("items/trailer").get(data={"id": qp["id"]})
    if response["status"] == 200:
        trailer = None
        trailer = response["trailer"]
        if "files" in trailer:
            url = get_mlink(
                trailer,
                quality=DEFAULT_QUALITY,
                streamType=DEFAULT_STREAM_TYPE
            )
        elif "sid" in qp:
            url = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid={}"
            url = url.format(qp["sid"])
        liObject = xbmcgui.ListItem("Трейлер")
        liObject.setPath(url)
        xbmcplugin.setResolvedUrl(handle, True, liObject)


def actionSearch(qp):
    kbd = xbmc.Keyboard()
    kbd.setDefault("")
    kbd.setHeading("Поиск")
    kbd.doModal()
    out = ""
    if kbd.isConfirmed():
        out = kbd.getText()
        if len(out.decode("utf-8")) >= 3:
            if "page" in qp:
                qp["page"] = 1
            qp["title"] = out
            nav_internal_link("items", qp)
        else:
            notice("Введите больше символов для поиска", "Поиск")
            nav_internal_link("index", qp)
    else:
        nav_internal_link("index", qp)


def actionBookmarks(qp):
    xbmc.log("{} : actionBookmarks. {}".format(__plugin__, str(qp)))
    if "folder-id" not in qp:
        response = KinoPubClient("bookmarks").get()
        if response["status"] == 200:
            for folder in response["items"]:
                li = xbmcgui.ListItem(folder["title"].encode("utf-8"))
                li.setProperty("folder-id", str(folder["id"]).encode("utf-8"))
                li.setProperty("views", str(folder["views"]).encode("utf-8"))
                link = get_internal_link("bookmarks", {"folder-id": folder["id"]})
                xbmcplugin.addDirectoryItem(handle, link, li, True)
            xbmcplugin.endOfDirectory(handle)
    else:
        # Show content of the folder
        response = KinoPubClient("bookmarks/{}".format(qp["folder-id"])).get(data=qp)
        if response["status"] == 200:
            show_items(response["items"])
            show_pagination(response["pagination"], "bookmarks", qp)
            xbmcplugin.endOfDirectory(handle)


def actionWatching(qp):
    response = KinoPubClient("watching/serials").get(data={"subscribed": 1})
    if response["status"] == 200:
        xbmcplugin.setContent(handle, "tvshows")
        for item in response["items"]:
            li = xbmcgui.ListItem("{} : [COLOR FFFFF000]+{}[/COLOR]".format(
                item["title"].encode("utf-8"), str(item["new"])))
            li.setLabel2(str(item["new"]))
            li.setArt({"poster": item["posters"]["big"]})
            link = get_internal_link("view", {"id": item["id"]})
            xbmcplugin.addDirectoryItem(handle, link, li, True)
        xbmcplugin.endOfDirectory(handle)
    else:
        notice("При загрузке сериалов произошла ошибка. Попробуйте позже.", "Я смотрю")


def actionCollections(qp):
    if "id" not in qp:
        response = KinoPubClient("collections/index").get(data=qp)
        if response["status"] == 200:
            xbmcplugin.setContent(handle, "movies")
            li = xbmcgui.ListItem("[COLOR FFFFF000]Последние[/COLOR]")
            qp["sort"] = "-created"
            xbmcplugin.addDirectoryItem(handle, get_internal_link("collections", qp), li, True)
            li = xbmcgui.ListItem("[COLOR FFFFF000]Просматриваемые[/COLOR]")
            qp["sort"] = "-watchers"
            xbmcplugin.addDirectoryItem(handle, get_internal_link("collections", qp), li, True)
            li = xbmcgui.ListItem("[COLOR FFFFF000]Популярные[/COLOR]")
            qp["sort"] = "-views"
            xbmcplugin.addDirectoryItem(handle, get_internal_link("collections", qp), li, True)
            for item in response["items"]:
                li = xbmcgui.ListItem(item["title"].encode("utf-8"))
                li.setThumbnailImage(item["posters"]["medium"])
                link = get_internal_link("collections", {"id": item["id"]})
                xbmcplugin.addDirectoryItem(handle, link, li, True)
            show_pagination(response["pagination"], "collections", qp)
            xbmcplugin.endOfDirectory(handle)
        else:
            notice("При загрузке подборок произошла ошибка. Попробуйте позже.", "Подборки")
    else:
        response = KinoPubClient("collections/view").get(data=qp)
        if response["status"] == 200:
            show_items(response["items"], add_indexes=True)
            #show_pagination(response["pagination"], "collections", qp)
            xbmcplugin.endOfDirectory(handle)
        else:
            notice("При загрузке произошла ошибка. Попробуйте позже.", "Подборки / Просмотр")


def actionAlphabet(qp):
    alpha = [
        "А,Б,В,Г,Д,Е,Ё,Ж,З,И,Й,К,Л,М,Н,О,П,Р,С,Т,У,Ф,Х,Ц,Ч,Ш,Щ,Ы,Э,Ю,Я",
        "A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z"
    ]
    for al in alpha:
        letters = al.split(",")
        for letter in letters:
            li = xbmcgui.ListItem(letter)
            link = get_internal_link("items", dict_merge(qp, {"letter": letter}))
            xbmcplugin.addDirectoryItem(handle, link, li, True)
    xbmcplugin.endOfDirectory(handle)
