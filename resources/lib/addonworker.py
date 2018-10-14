# -*- coding: utf-8 -*-
import json

import xbmc
import xbmcgui
import xbmcplugin
import context_menu
from addonutils import (get_internal_link, get_mlink, nav_internal_link, notice, request, route,
                        ROUTES, trailer_link, video_info)
from authwindow import auth
from client import KinoPubClient
from data import __settings__, __plugin__


mediatype_map = {
    "serial": "tvshow",
    "docuserial": "tvshow",
    "tvshow": "tvshow",
    "concert": "musicvideo",
    "3d": "movie",
    "documovie": "movie",
    "movie": "movie",
    "4k": "movie"
}


def show_pagination(pagination, action, **kwargs):
    # Add "next page" button
    if (pagination and int(pagination["current"])) + 1 <= int(pagination["total"]):
        kwargs["page"] = int(pagination["current"]) + 1
        li = xbmcgui.ListItem("[COLOR FFFFF000]Вперёд[/COLOR]")
        link = get_internal_link(action, **kwargs)
        xbmcplugin.addDirectoryItem(request.handle, link, li, True)
    xbmcplugin.endOfDirectory(request.handle)


def show_items(items, add_indexes=False):
    xbmc.log("{} : show_items. Total items: {}".format(__plugin__, str(len(items))))
    xbmcplugin.setContent(request.handle, "movies")
    # Fill list with items
    for index, item in enumerate(items, 1):
        title = item["title"].encode("utf-8")
        li = xbmcgui.ListItem(title)
        if add_indexes:
            li.setLabel("{}. {}".format(index, li.getLabel()))
        li.setArt({"poster": item["posters"]["big"]})
        li.setProperty("id", str(item["id"]))
        if "in_watchlist" in item:
            li.setProperty("in_watchlist", str(int(item["in_watchlist"])))
        extra_info = {"trailer": trailer_link(item), "mediatype": mediatype_map[item["type"]]}
        # If not serials or multiseries movie, create playable item
        if item["type"] not in ["serial", "docuserial", "tvshow"] and not item["subtype"]:
            watched = KinoPubClient("watching").get(data={"id": item["id"]})["item"]
            extra_info.update({"playcount": watched["status"]})
            link = get_internal_link("play", id=item["id"], title=title)
            li.setProperty("isPlayable", "true")
            isdir = False
        elif item["subtype"] == "multi":
            link = get_internal_link("view_episodes", id=item["id"])
            isdir = True
        else:
            link = get_internal_link("view_seasons", id=item["id"])
            isdir = True
        li.setInfo("Video", video_info(item, extra_info))
        context_menu.add_items(li)
        xbmcplugin.addDirectoryItem(request.handle, link, li, isdir)


def add_default_headings(type=None, fmt="slp"):
    # fmt - show format
    # s - show search
    # l - show last
    # p - show popular
    # s - show alphabet sorting
    # g - show genres folder
    # h - show hot

    if "s" in fmt:
        li = xbmcgui.ListItem("[COLOR FFFFF000]Поиск[/COLOR]")
        link = get_internal_link("search", type=type)
        xbmcplugin.addDirectoryItem(request.handle, link, li, False)
    if "l" in fmt:
        li = xbmcgui.ListItem("[COLOR FFFFF000]Последние[/COLOR]")
        link = get_internal_link("items", type=type)
        xbmcplugin.addDirectoryItem(request.handle, link, li, True)
    if "p" in fmt:
        li = xbmcgui.ListItem("[COLOR FFFFF000]Популярные[/COLOR]")
        link = get_internal_link("items", type=type, shortcut="/popular")
        xbmcplugin.addDirectoryItem(request.handle, link, li, True)
    if "a" in fmt:
        li = xbmcgui.ListItem("[COLOR FFFFF000]По алфавиту[/COLOR]")
        link = get_internal_link("alphabet", type=type)
        xbmcplugin.addDirectoryItem(request.handle, link, li, True)
    if "g" in fmt:
        li = xbmcgui.ListItem("[COLOR FFFFF000]Жанры[/COLOR]")
        link = get_internal_link("genres", type=type)
        xbmcplugin.addDirectoryItem(request.handle, link, li, True)
    if "h" in fmt:
        li = xbmcgui.ListItem("[COLOR FFFFF000]Горячие[/COLOR]")
        link = get_internal_link("items", type=type, shortcut="/hot")
        xbmcplugin.addDirectoryItem(request.handle, link, li, True)


@route("/login")
def login():
    auth.reauth()


@route("/")
def index():
    """Main screen - show type list"""
    if not auth.access_token:
        li = xbmcgui.ListItem("Активировать устройство")
        xbmcplugin.addDirectoryItem(request.handle, get_internal_link("login"), li, False)
        xbmcplugin.endOfDirectory(request.handle)
    else:
        response = KinoPubClient("types").get()
        add_default_headings(fmt="slph")
        li = xbmcgui.ListItem("[COLOR FFFFF000]ТВ[/COLOR]")
        xbmcplugin.addDirectoryItem(request.handle, get_internal_link("tv"), li, True)
        li = xbmcgui.ListItem("[COLOR FFFFF000]Закладки[/COLOR]")
        xbmcplugin.addDirectoryItem(request.handle, get_internal_link("bookmarks"), li, True)
        li = xbmcgui.ListItem("[COLOR FFFFF000]Я смотрю[/COLOR]")
        xbmcplugin.addDirectoryItem(request.handle, get_internal_link("watching"), li, True)
        li = xbmcgui.ListItem("[COLOR FFFFF000]Подборки[/COLOR]")
        xbmcplugin.addDirectoryItem(request.handle, get_internal_link("collections"), li, True)
        for i in response["items"]:
            li = xbmcgui.ListItem(i["title"].encode("utf-8"))
            link = get_internal_link("item_index", type=i["id"])
            xbmcplugin.addDirectoryItem(request.handle, link, li, True)
        xbmcplugin.endOfDirectory(request.handle)


@route("/item_index")
def default_headings(type):
    add_default_headings(type, "slpgah")
    xbmcplugin.endOfDirectory(request.handle)


@route("/tv")
def tv():
    response = KinoPubClient("tv/index").get()
    for ch in response["channels"]:
        li = xbmcgui.ListItem(ch["title"].encode("utf-8"), iconImage=ch["logos"]["s"])
        xbmcplugin.addDirectoryItem(request.handle, ch["stream"], li, False)
    xbmcplugin.endOfDirectory(request.handle)


@route("/genres")
def genres(type):
    response = KinoPubClient("genres").get(data={"type": type})
    add_default_headings(type)
    for genre in response["items"]:
        li = xbmcgui.ListItem(genre["title"].encode("utf-8"))
        link = get_internal_link("items", type=type, genre=genre["id"])
        xbmcplugin.addDirectoryItem(request.handle, link, li, True)
    xbmcplugin.endOfDirectory(request.handle)


@route("/items")
def items(type, **kwargs):
    """List items with pagination"""
    kwargs["type"] = type
    shortcut = kwargs.pop("shortcut", "")
    response = KinoPubClient("items{}".format(shortcut)).get(data=kwargs)
    pagination = response["pagination"]
    add_default_headings(type, fmt="s")
    show_items(response["items"])
    show_pagination(pagination, "items", type=type)


@route("/view_seasons")
def seasons(id):
    response = KinoPubClient("items/{}".format(id)).get()
    item = response["item"]
    watching_info = KinoPubClient("watching").get(data={"id": item["id"]})["item"]
    selectedSeason = False
    xbmcplugin.setContent(request.handle, "tvshows")
    for season in item["seasons"]:
        season_title = "Сезон {}".format(season["number"])
        watching_season = watching_info["seasons"][season["number"] - 1]
        li = xbmcgui.ListItem(season_title)
        li.setInfo("Video", video_info(item, {"season": season["number"]}))
        li.setArt({"poster": item["posters"]["big"]})
        if watching_season["status"] < 1 and not selectedSeason:
            selectedSeason = True
            li.select(selectedSeason)
        qp = {"id": id, "season_number": season["number"]}
        link = get_internal_link("view_season_episodes", **qp)
        xbmcplugin.addDirectoryItem(request.handle, link, li, True)
    xbmcplugin.endOfDirectory(request.handle)


@route("/view_episodes")
def episodes(id):
    response = KinoPubClient("items/{}".format(id)).get()
    item = response["item"]
    xbmcplugin.setContent(request.handle, "episodes")
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
            "episode": video_number,
            "playcount": video["watched"],
            "mediatype": "episode"
        }))
        li.setArt({"poster": item["posters"]["big"]})
        li.setProperty("id", str(item["id"]))
        li.setProperty("isPlayable", "true")
        qp = {
            "id": item["id"],
            "title": episode_title,
            "episode_number": video_number,
            "video_data": json.dumps(video)
        }
        link = get_internal_link("play", **qp)
        context_menu.add_items(li)
        xbmcplugin.addDirectoryItem(request.handle, link, li, False)
    xbmcplugin.endOfDirectory(request.handle)


@route("/view_season_episodes")
def season_episodes(id, season_number):
    response = KinoPubClient("items/{}".format(id)).get()
    item = response["item"]
    watching_info = KinoPubClient("watching").get(data={"id": item["id"]})["item"]
    season_number = int(season_number)
    season = item["seasons"][season_number - 1]
    watching_season = watching_info["seasons"][season_number - 1]
    selectedEpisode = False
    xbmcplugin.setContent(request.handle, "episodes")
    for episode in season["episodes"]:
        episode_title = "s{:02d}e{:02d}".format(season_number, episode["number"])
        if episode["title"]:
            episode_title = "{} | {}".format(episode_title, episode["title"].encode("utf-8"))
        li = xbmcgui.ListItem(
            episode_title,
            iconImage=episode["thumbnail"],
            thumbnailImage=episode["thumbnail"]
        )
        li.setInfo("Video", video_info(item, {
            "season": season_number,
            "episode": episode["number"],
            "duration": episode["duration"],
            "playcount": episode["watched"],
            "mediatype": "episode"
        }))
        li.setArt({"poster": item["posters"]["big"]})
        li.setProperty("id", str(item["id"]))
        li.setProperty("isPlayable", "true")
        status = watching_season["episodes"][episode["number"] - 1]["status"]
        if status < 1 and not selectedEpisode:
            selectedEpisode = True
            li.select(selectedEpisode)
        qp = {
            "id": item["id"],
            "title": episode_title,
            "season_number": season["number"],
            "episode_number": episode["number"],
            "video_data": json.dumps(episode)
        }
        link = get_internal_link("play", **qp)
        context_menu.add_items(li)
        xbmcplugin.addDirectoryItem(request.handle, link, li, False)
    xbmcplugin.endOfDirectory(request.handle)


@route("/play")
def play(id, title, season_number=None, episode_number=None, video_data=None):
    if not video_data:
        response = KinoPubClient("items/{}".format(id)).get()
        video_data = response["item"]["videos"][0]
    else:
        video_data = json.loads(video_data)
    if "files" not in video_data:
        notice("Видео обновляется и временно не доступно!", "Видео в обработке", time=8000)
        return
    li = xbmcgui.ListItem(title)
    subtitles = [subtitle["url"] for subtitle in video_data["subtitles"]]
    if subtitles:
        li.setSubtitles(subtitles)
    url = get_mlink(
        video_data,
        quality=__settings__.getSetting("video_quality"),
        stream_type=__settings__.getSetting("stream_type"),
        ask_quality=__settings__.getSetting("ask_quality")
    )
    KinoPubClient("watching/marktime").get(data={
        "id": id,
        "video": video_data["number"],
        "time": video_data.get("duration"),
        "season": season_number
    })
    li.setPath(url)
    xbmcplugin.setResolvedUrl(request.handle, True, li)


@route("/trailer")
def trailer(id, sid=None):
    response = KinoPubClient("items/trailer").get(data={"id": id})
    trailer = None
    trailer = response["trailer"]
    if "files" in trailer:
        url = get_mlink(
            trailer,
            quality=__settings__.getSetting("video_quality"),
            streamType=__settings__.getSetting("stream_type")
        )
    elif sid is not None:
        url = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid={}"
        url = url.format(sid)
    liObject = xbmcgui.ListItem("Трейлер")
    liObject.setPath(url)
    xbmcplugin.setResolvedUrl(request.handle, True, liObject)


@route("/search")
def search(type=None):
    kbd = xbmc.Keyboard()
    kbd.setHeading("Поиск")
    kbd.doModal()
    if kbd.isConfirmed():
        title = kbd.getText()
        if len(title.decode("utf-8")) >= 3:
            nav_internal_link("items", title=title, type=type)
        else:
            notice("Введите больше символов для поиска", "Поиск")


@route("/bookmarks")
def bookmarks(folder_id=None, page=None):
    if folder_id is None:
        li = xbmcgui.ListItem("[COLOR FFFFF000]Создать папку[/COLOR]")
        link = get_internal_link("create_bookmarks_folder")
        xbmcplugin.addDirectoryItem(request.handle, link, li, False)
        response = KinoPubClient("bookmarks").get()
        for folder in response["items"]:
            li = xbmcgui.ListItem(folder["title"].encode("utf-8"))
            li.setProperty("folder-id", str(folder["id"]).encode("utf-8"))
            li.setProperty("views", str(folder["views"]).encode("utf-8"))
            context_menu.add_bookmarks_items(li, folder["id"])
            link = get_internal_link("bookmarks", folder_id=folder["id"])
            xbmcplugin.addDirectoryItem(request.handle, link, li, True)
        xbmcplugin.endOfDirectory(request.handle)
    else:
        # Show content of the folder
        response = KinoPubClient("bookmarks/{}".format(folder_id)).get(data={"page": page})
        show_items(response["items"])
        show_pagination(response["pagination"], "bookmarks", folder_id=folder_id)


@route("/watching")
def watching():
    response = KinoPubClient("watching/serials").get(data={"subscribed": 1})
    xbmcplugin.setContent(request.handle, "tvshows")
    for item in response["items"]:
        li = xbmcgui.ListItem("{} : [COLOR FFFFF000]+{}[/COLOR]".format(
            item["title"].encode("utf-8"), str(item["new"])))
        li.setLabel2(str(item["new"]))
        li.setArt({"poster": item["posters"]["big"]})
        li.setProperty("id", str(item["id"]))
        li.setProperty("in_watchlist", "1")
        li.setInfo("Video", {"mediatype": mediatype_map[item["type"]]})
        link = get_internal_link("view_seasons", id=item["id"])
        context_menu.add_items(li)
        xbmcplugin.addDirectoryItem(request.handle, link, li, True)
    xbmcplugin.endOfDirectory(request.handle)


@route("/collections")
def collections(sort=None, page=None):
    response = KinoPubClient("collections/index").get(data={"sort": sort, "page": page})
    xbmcplugin.setContent(request.handle, "movies")
    li = xbmcgui.ListItem("[COLOR FFFFF000]Последние[/COLOR]")
    link = get_internal_link("collections", sort="-created")
    xbmcplugin.addDirectoryItem(request.handle, link, li, True)
    li = xbmcgui.ListItem("[COLOR FFFFF000]Просматриваемые[/COLOR]")
    link = get_internal_link("collections", sort="-watchers")
    xbmcplugin.addDirectoryItem(request.handle, link, li, True)
    li = xbmcgui.ListItem("[COLOR FFFFF000]Популярные[/COLOR]")
    link = get_internal_link("collections", sort="-views")
    xbmcplugin.addDirectoryItem(request.handle, link, li, True)
    for item in response["items"]:
        li = xbmcgui.ListItem(item["title"].encode("utf-8"))
        li.setThumbnailImage(item["posters"]["medium"])
        link = get_internal_link("collection_view", id=item["id"])
        xbmcplugin.addDirectoryItem(request.handle, link, li, True)
    show_pagination(response["pagination"], "collections", sort=sort)


@route("/collection_view")
def collection_view(id):
    response = KinoPubClient("collections/view").get(data={"id": id})
    show_items(response["items"], add_indexes=True)
    xbmcplugin.endOfDirectory(request.handle)


@route("/alphabet")
def alphabet(type):
    alpha = [
        "А,Б,В,Г,Д,Е,Ё,Ж,З,И,Й,К,Л,М,Н,О,П,Р,С,Т,У,Ф,Х,Ц,Ч,Ш,Щ,Ы,Э,Ю,Я",
        "A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z"
    ]
    for al in alpha:
        letters = al.split(",")
        for letter in letters:
            li = xbmcgui.ListItem(letter)
            link = get_internal_link("items", type=type, letter=letter)
            xbmcplugin.addDirectoryItem(request.handle, link, li, True)
    xbmcplugin.endOfDirectory(request.handle)


@route("/toggle_watched")
def toggle_watched(**kwargs):
    KinoPubClient("watching/toggle").get(data=kwargs)
    xbmc.executebuiltin("Container.Refresh")


@route("/toggle_watchlist")
def toggle_watchlist(**kwargs):
    added = bool(kwargs.pop("added"))
    KinoPubClient("watching/togglewatchlist").get(data=kwargs)
    if added:
        notice('Сериал добавлен в список "Буду смотреть"')
    else:
        notice('Сериал удалён из списка "Буду смотреть"')
    xbmc.executebuiltin("Container.Refresh")


@route("/edit_bookmarks")
def edit_bookmarks(item_id=None):
    item_folders_resp = KinoPubClient("bookmarks/get-item-folders").get(data={"item": item_id})
    all_folders_resp = KinoPubClient("bookmarks").get()
    all_folders = [f["title"] for f in all_folders_resp["items"]]
    item_folders = [f["title"] for f in item_folders_resp["folders"]]
    preselect = [all_folders.index(f) for f in item_folders]
    dialog = xbmcgui.Dialog()
    indexes = dialog.multiselect("Папки закладок", all_folders, preselect=preselect)
    # Cancel button was pressed
    if indexes is None:
        return
    chosen_folders = [all_folders[i] for i in indexes]
    folders_to_add = list(set(chosen_folders) - set(item_folders))
    folders_to_remove = list(set(item_folders) - set(chosen_folders))
    # Ok button was pressed but nothing changed
    if not folders_to_add and not folders_to_remove:
        return

    def get_folder_id(title):
        for folder in all_folders_resp["items"]:
            if folder["title"] == title:
                return folder["id"]

    for folder in folders_to_add:
        KinoPubClient("bookmarks/add").post(data={
            "item": item_id,
            "folder": get_folder_id(folder)
        })
    for folder in folders_to_remove:
        KinoPubClient("bookmarks/remove-item").post(data={
            "item": item_id,
            "folder": get_folder_id(folder)
        })
    notice("Закладки для видео изменены")
    xbmc.executebuiltin("Container.Refresh")


@route("/remove_bookmarks_folder")
def remove_bookmark_folder(folder_id):
    KinoPubClient("bookmarks/remove-folder").post(data={"folder": folder_id})
    xbmc.executebuiltin("Container.Refresh")


@route("/create_bookmarks_folder")
def create_bookmarks_folder():
    kbd = xbmc.Keyboard()
    kbd.setHeading("Имя папки закладок")
    kbd.doModal()
    if kbd.isConfirmed():
        title = kbd.getText()
        KinoPubClient("bookmarks/create").post(data={"title": title})
        xbmc.executebuiltin("Container.Refresh")


# Entry point
def init():
    ROUTES[request.path](**request.args)
