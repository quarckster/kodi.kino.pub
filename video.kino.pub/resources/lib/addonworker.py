# -*- coding: utf-8 -*-
import json
import sys
import urlparse
import xbmcplugin
import xbmcgui
import xbmc
from addonutils import (dict_merge, get_internal_link, get_mlink, nav_internal_link, notice,
                        trailer_link, video_info)
from authwindow import auth
from client import KinoPubClient
from data import __settings__, __plugin__


DEFAULT_QUALITY = __settings__.getSetting("video_quality")
DEFAULT_STREAM_TYPE = __settings__.getSetting("stream_type")

handle = int(sys.argv[1])


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
        title = item["title"].encode("utf-8")
        li = xbmcgui.ListItem(title)
        if add_indexes:
            li.setLabel("{}. {}".format(index, li.getLabel()))
        li.setInfo("Video", video_info(item, {"trailer": trailer_link(item)}))
        li.setArt({"poster": item["posters"]["big"]})
        # If not serials or multiseries movie, create playable item
        if item["type"] not in ["serial", "docuserial", "tvshow"] and not item["subtype"]:
            link = get_internal_link("play", {"id": item["id"], "title": title})
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
        xbmcplugin.addDirectoryItem(handle, get_internal_link(
            "items", dict_merge(qp, {"sort": "-rating"})), li, True)
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


# Actions
def actionLogin(qp):
    xbmc.log("{} : actionLogin. {}".format(__plugin__, str(qp)))
    # if no access token exists
    if not auth.access_token:
        auth.reauth()
    if auth.is_token_expired:
        # try to refresh token
        auth.get_token(refresh=True)
    actionIndex(qp)


def actionIndex(qp):
    """Main screen - show type list"""
    xbmc.log("{}: actionIndex. {}".format(__plugin__, str(qp)))
    xbmc.executebuiltin("Container.SetViewMode(0)")
    if "type" in qp:
        add_default_headings(qp, "slpga")
    else:
        response = KinoPubClient("types").get()
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
    for ch in response["channels"]:
        li = xbmcgui.ListItem(ch["title"].encode("utf-8"), iconImage=ch["logos"]["s"])
        xbmcplugin.addDirectoryItem(handle, ch["stream"], li, False)
    xbmcplugin.endOfDirectory(handle)


def actionGenres(qp):
    response = KinoPubClient("genres").get(data={"type": qp.get("type", "")})
    add_default_headings(qp, "")
    for genre in response["items"]:
        li = xbmcgui.ListItem(genre["title"].encode("utf-8"))
        link = get_internal_link("items", {"type": qp.get("type"), "genre": genre["id"]})
        xbmcplugin.addDirectoryItem(handle, link, li, True)
    xbmcplugin.endOfDirectory(handle)


def actionItems(qp):
    """List items with pagination

        Args:
            qp: dict, query parameters for item filtering
    """
    response = KinoPubClient("items").get(data=qp)
    pagination = response["pagination"]
    add_default_headings(qp, "s")
    show_items(response["items"])
    show_pagination(pagination, "items", qp)


def actionView(qp):
    """Show items

    If item type is movie with more than 1 episodes - show those episodes. If item type is serial,
    docuserial, tvshow - show seasons. If parameter season is set - show episodes. Otherwise play
    content.
    """
    response = KinoPubClient("items/{}".format(qp["id"])).get()
    item = response["item"]
    watching_info = KinoPubClient("watching").get(data={"id": item["id"]})["item"]
    # If serial instance or multiseries film show navigation, else start play
    if item["type"] in ["serial", "docuserial", "tvshow"]:
        if "season" in qp:
            for season in item["seasons"]:
                season_number = int(season["number"])
                if season_number == int(qp["season"]):
                    watching_season = watching_info["seasons"][season["number"] - 1]
                    selectedEpisode = False
                    xbmcplugin.setContent(handle, "episodes")
                    for episode_number, episode in enumerate(season["episodes"], 1):
                        episode_title = "s{:02d}e{:02d}".format(
                            season["number"], episode_number)
                        if episode["title"]:
                            episode_title = "{} | {}".format(
                                episode_title, episode["title"].encode("utf-8"))
                        li = xbmcgui.ListItem(
                            episode_title,
                            iconImage=episode["thumbnail"],
                            thumbnailImage=episode["thumbnail"]
                        )
                        li.setInfo("Video", video_info(item, {
                            "season": season_number,
                            "episode": episode_number,
                            "duration": episode["duration"],
                        }))
                        li.setInfo("Video", {"playcount": episode["watched"]})
                        li.setArt({"poster": item["posters"]["big"]})
                        li.setProperty("IsPlayable", "true")
                        status = watching_season["episodes"][episode_number - 1]["status"]
                        if status < 1 and not selectedEpisode:
                            selectedEpisode = True
                            li.select(selectedEpisode)
                        qp = {
                            "id": item["id"],
                            "title": episode_title,
                            "season": season["number"],
                            "number": episode_number,
                            "video": json.dumps(episode)
                        }
                        link = get_internal_link("play", qp)
                        xbmcplugin.addDirectoryItem(handle, link, li, False)
                    break
        else:
            selectedSeason = False
            xbmcplugin.setContent(handle, "tvshows")
            for season in item["seasons"]:
                season_title = "Сезон {}".format(season["number"])
                watching_season = watching_info["seasons"][season["number"] - 1]
                li = xbmcgui.ListItem(season_title)
                li.setInfo("Video", video_info(item, {"season": season["number"]}))
                li.setArt({"poster": item["posters"]["big"]})
                if watching_season["status"] < 1 and not selectedSeason:
                    selectedSeason = True
                    li.select(selectedSeason)
                link = get_internal_link("view", {"id": qp["id"], "season": season["number"]})
                xbmcplugin.addDirectoryItem(handle, link, li, True)
    elif "videos" in item and len(item["videos"]) > 1:
        xbmcplugin.setContent(handle, "episodes")
        for video_number, video in enumerate(item["videos"], 1):
            episode_title = "e{:02d}".format(video_number)
            if video["title"]:
                episode_title = "{} | {}".format(episode_title, video["title"].encode("utf-8"))
            li = xbmcgui.ListItem(
                episode_title,
                iconImage=video["thumbnail"],
                thumbnailImage=video["thumbnail"]
            )
            li.setInfo("Video", video_info(item, {
                "season": 1,
                "episode": video_number
            }))
            li.setInfo("Video", {"playcount": video["watched"]})
            li.setArt({"poster": item["posters"]["big"]})
            li.setProperty("IsPlayable", "true")
            qp = {
                "id": item["id"],
                "title": episode_title,
                "number": video_number,
                "video": json.dumps(video)
            }
            link = get_internal_link("play", qp)
            xbmcplugin.addDirectoryItem(handle, link, li, False)
    xbmcplugin.endOfDirectory(handle)


def actionPlay(qp):
    if not qp.get("video"):
        response = KinoPubClient("items/{}".format(qp["id"])).get()
        videoObject = response["item"]["videos"][0]
    else:
        videoObject = json.loads(qp["video"])
    liObject = xbmcgui.ListItem(qp["title"])
    subtitles = [subtitle["url"] for subtitle in videoObject["subtitles"]]
    if subtitles:
        liObject.setSubtitles(subtitles)
    if "files" not in videoObject:
        notice("Видео обновляется и временно не доступно!", "Видео в обработке", time=8000)
        return
    url = get_mlink(
        videoObject,
        quality=qp.get("quality", DEFAULT_QUALITY),
        streamType=qp.get("stream_type", DEFAULT_STREAM_TYPE)
    )
    KinoPubClient("watching/marktime").get(data={
        "id": qp["id"],
        "video": videoObject["number"],
        "time": videoObject.get("duration"),
        "season": qp.get("season")
    })
    liObject.setPath(url)
    xbmcplugin.setResolvedUrl(handle, True, liObject)


def actionTrailer(qp):
    response = KinoPubClient("items/trailer").get(data={"id": qp["id"]})
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
        show_items(response["items"])
        show_pagination(response["pagination"], "bookmarks", qp)
        xbmcplugin.endOfDirectory(handle)


def actionWatching(qp):
    response = KinoPubClient("watching/serials").get(data={"subscribed": 1})
    xbmcplugin.setContent(handle, "tvshows")
    for item in response["items"]:
        li = xbmcgui.ListItem("{} : [COLOR FFFFF000]+{}[/COLOR]".format(
            item["title"].encode("utf-8"), str(item["new"])))
        li.setLabel2(str(item["new"]))
        li.setArt({"poster": item["posters"]["big"]})
        link = get_internal_link("view", {"id": item["id"]})
        xbmcplugin.addDirectoryItem(handle, link, li, True)
    xbmcplugin.endOfDirectory(handle)


def actionCollections(qp):
    if "id" not in qp:
        response = KinoPubClient("collections/index").get(data=qp)
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
        response = KinoPubClient("collections/view").get(data=qp)
        show_items(response["items"], add_indexes=True)
        xbmcplugin.endOfDirectory(handle)


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
