# -*- coding: utf-8 -*-
from __future__ import absolute_import

from copy import copy
from datetime import date

try:
    import inputstreamhelper
except ImportError:
    inputstreamhelper = None
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

from resources.lib.settings import settings
from resources.lib.utils import (
    get_mlink,
    notice,
    trailer_link,
    video_info as extract_video_info,
    get_window_property,
    set_window_property,
    build_icon_path,
)
from resources.lib.routing import plugin
from resources.lib.client import KinoPubClient
from resources.lib.listitem import ExtendedListItem
from resources.lib.main_menu import main_menu_items
from resources.lib.player import Player


content_type_map = {
    "serial": "tvshow",
    "docuserial": "tvshow",
    "tvshow": "tvshow",
    "concert": "musicvideo",
    "3d": "movie",
    "documovie": "movie",
    "movie": "movie",
    "4k": "movie",
}


def show_pagination(pagination, action, **kwargs):
    # Add "next page" button
    if pagination and (int(pagination["current"]) + 1 <= int(pagination["total"])):
        kwargs["page"] = int(pagination["current"]) + 1
        # Use icons from lib for default headings
        img = build_icon_path("next_page")
        li = ExtendedListItem("[COLOR FFFFF000]Вперёд[/COLOR]", iconImage=img, thumbnailImage=img)
        link = plugin.build_url(action, **kwargs)
        xbmcplugin.addDirectoryItem(plugin.handle, link, li, True)
    xbmcplugin.endOfDirectory(plugin.handle, cacheToDisc=False)


def show_items(items, add_indexes=False):
    playback_data = {}
    # Fill list with items
    for index, item in enumerate(items, 1):
        title = item["title"]
        title = "{}. {}".format(index, title) if add_indexes else title
        li = ExtendedListItem(title, poster=item["posters"]["big"], properties={"id": item["id"]})
        if "in_watchlist" in item:
            li.setProperty("in_watchlist", str(int(item["in_watchlist"])))
        video_info = extract_video_info(
            item, {"trailer": trailer_link(item), "mediatype": content_type_map[item["type"]]}
        )
        # If not serials or multiseries movie, create playable item
        if item["type"] not in ["serial", "docuserial", "tvshow"] and not item["subtype"]:
            watching_info = KinoPubClient("watching").get(data={"id": item["id"]})["item"][
                "videos"
            ][0]
            video_info.update(
                {
                    "time": watching_info["time"],
                    "duration": watching_info["duration"],
                    "playcount": watching_info["status"],
                }
            )
            link = plugin.build_url("play", item["id"], index)
            li.setProperty("isPlayable", "true")
            li.setResumeTime(watching_info["time"], watching_info["duration"])
            isdir = False
            playback_data[index] = {
                "video_info": video_info,
                "poster": item["posters"]["big"],
                "title": title,
            }
            set_window_property(playback_data)
        elif item["subtype"] == "multi":
            watching_info = KinoPubClient("watching").get(data={"id": item["id"]})["item"]
            li.setProperty("subtype", "multi")
            video_info.update({"playcount": watching_info["status"]})
            link = plugin.build_url("episodes", item["id"])
            isdir = True
        else:
            link = plugin.build_url("seasons", item["id"])
            isdir = True
        li.setInfo("video", video_info)
        li.addPredefinedContextMenuItems()
        li.markAdvert(item["advert"])
        xbmcplugin.addDirectoryItem(plugin.handle, link, li, isdir)


def add_default_headings(content_type=None, fmt="slp"):
    # fmt - show format
    # s - show search
    # l - show last
    # p - show popular
    # s - show alphabet sorting
    # g - show genres folder
    # h - show hot
    # Use icons from lib for default headings
    if "s" in fmt:
        img = build_icon_path("search")
        li = ExtendedListItem("Поиск", iconImage=img, thumbnailImage=img)
        url = plugin.build_url("search", content_type=content_type)
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, False)
    if "l" in fmt:
        img = build_icon_path("new")
        li = ExtendedListItem("Последние", iconImage=img, thumbnailImage=img)
        url = plugin.build_url("items", content_type=content_type)
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)
    if "p" in fmt:
        img = build_icon_path("popular")
        li = ExtendedListItem("Популярные", iconImage=img, thumbnailImage=img)
        url = plugin.build_url("items", content_type=content_type, shortcut="/popular")
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)
    if "a" in fmt:
        img = build_icon_path("alphabet")
        li = ExtendedListItem("По алфавиту", iconImage=img, thumbnailImage=img)
        url = plugin.build_url("alphabet", content_type)
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)
    if "g" in fmt:
        img = build_icon_path("genres")
        li = ExtendedListItem("Жанры", iconImage=img, thumbnailImage=img)
        url = plugin.build_url("genres", content_type)
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)
    if "h" in fmt:
        img = build_icon_path("hot")
        li = ExtendedListItem("Горячие", iconImage=img, thumbnailImage=img)
        url = plugin.build_url("items", content_type=content_type, shortcut="/hot")
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)


@plugin.route("/login")
def login():
    plugin.auth.get_token()


@plugin.route("/reset_auth")
def reset_auth():
    plugin.settings.access_token = ""
    plugin.settings.access_token_expire = ""
    plugin.settings.refresh_token = ""
    xbmc.executebuiltin("Container.Refresh")


@plugin.route("/")
def index():
    """Main screen - show type list"""
    if not settings.access_token:
        # Use icons from lib for default headings
        li = ExtendedListItem("Активировать устройство", iconImage=build_icon_path("activate"))
        xbmcplugin.addDirectoryItem(plugin.handle, plugin.build_url("login"), li, False)
    else:
        response = KinoPubClient("types").get()
        # Use icons from lib for default headings
        img = build_icon_path("profile")
        li = ExtendedListItem("Профиль", iconImage=img, thumbnailImage=img)
        xbmcplugin.addDirectoryItem(plugin.handle, plugin.build_url("profile"), li, False)
        for menu_item in main_menu_items:
            if menu_item.is_displayed:
                li = ExtendedListItem(
                    menu_item.title, iconImage=menu_item.icon, thumbnailImage=menu_item.icon
                )
                xbmcplugin.addDirectoryItem(plugin.handle, menu_item.url, li, menu_item.is_dir)
        for i in response["items"]:
            if getattr(settings, "show_{}".format(i["id"])) != "false":
                img = build_icon_path(i["id"])
                li = ExtendedListItem(i["title"], iconImage=img, thumbnailImage=img)
                url = plugin.build_url("item_index", i["id"])
                xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/item_index/<content_type>")
def default_headings(content_type):
    add_default_headings(content_type, "slpgah")
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/tv")
def tv():
    response = KinoPubClient("tv/index").get()
    for ch in response["channels"]:
        li = ExtendedListItem(ch["title"], iconImage=ch["logos"]["s"])
        xbmcplugin.addDirectoryItem(plugin.handle, ch["stream"], li, False)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/genres/<content_type>")
def genres(content_type):
    response = KinoPubClient("genres").get(data={"type": content_type})
    add_default_headings(content_type)
    for genre in response["items"]:
        li = ExtendedListItem(genre["title"])
        url = plugin.build_url("items", content_type=content_type, genre=genre["id"])
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/items")
def items():
    """List items with pagination"""
    data = copy(plugin.kwargs)
    data["type"] = data.pop("content_type", None)
    shortcut = data.pop("shortcut", "")
    response = KinoPubClient("items{}".format(shortcut)).get(data=data)
    pagination = response["pagination"]
    xbmcplugin.setContent(
        plugin.handle,
        "{}s".format(content_type_map.get(plugin.kwargs.get("content_type"), "video")),
    )
    show_items(response["items"])
    show_pagination(pagination, "items", **plugin.kwargs)


@plugin.route("/seasons/<item_id>")
def seasons(item_id):
    item = KinoPubClient("items/{}".format(item_id)).get()["item"]
    watching_info = KinoPubClient("watching").get(data={"id": item["id"]})["item"]
    selectedSeason = False
    xbmcplugin.setContent(plugin.handle, "tvshows")
    for season in item["seasons"]:
        season_title = "Сезон {}".format(season["number"])
        watching_season = watching_info["seasons"][season["number"] - 1]
        li = ExtendedListItem(
            season_title,
            video_info=extract_video_info(
                item,
                {
                    "season": season["number"],
                    "playcount": watching_season["status"],
                    "mediatype": "season",
                },
            ),
            poster=item["posters"]["big"],
            properties={"id": item["id"]},
            addContextMenuItems=True,
        )
        if watching_season["status"] < 1 and not selectedSeason:
            selectedSeason = True
            li.select(selectedSeason)
        url = plugin.build_url("season_episodes", item_id, season["number"])
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)
    xbmcplugin.endOfDirectory(plugin.handle, cacheToDisc=False)


@plugin.route("/episodes/<item_id>")
def episodes(item_id):
    item = KinoPubClient("items/{}".format(item_id)).get()["item"]
    watching_info = KinoPubClient("watching").get(data={"id": item_id})["item"]
    xbmcplugin.setContent(plugin.handle, "episodes")
    playback_data = {}
    for video in item["videos"]:
        watching_episode = watching_info["videos"][video["number"] - 1]
        episode_title = "e{:02d}".format(video["number"])
        if video["title"]:
            episode_title = "{} | {}".format(episode_title, video["title"])
        info = extract_video_info(
            item,
            {
                "episode": video["number"],
                "tvshowtitle": video["title"],
                "time": watching_episode["time"],
                "duration": watching_episode["duration"],
                "playcount": video["watched"],
                "mediatype": "episode",
            },
        )
        li = ExtendedListItem(
            episode_title,
            thumbnailImage=video["thumbnail"],
            video_info=info,
            poster=item["posters"]["big"],
            properties={"id": item["id"], "isPlayable": "true"},
            addContextMenuItems=True,
        )
        url = plugin.build_url("play", item["id"], video["number"])
        playback_data[video["number"]] = {
            "video_data": video,
            "video_info": info,
            "poster": item["posters"]["big"],
            "title": episode_title,
        }
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, False)
    set_window_property(playback_data)
    xbmcplugin.endOfDirectory(plugin.handle, cacheToDisc=False)


@plugin.route("/season_episodes/<item_id>/<season_number>")
def season_episodes(item_id, season_number):
    item = KinoPubClient("items/{}".format(item_id)).get()["item"]
    watching_info = KinoPubClient("watching").get(data={"id": item_id})["item"]
    season_number = int(season_number)
    season = item["seasons"][season_number - 1]
    watching_season = watching_info["seasons"][season_number - 1]
    selectedEpisode = False
    xbmcplugin.setContent(plugin.handle, "episodes")
    playback_data = {}
    for episode in season["episodes"]:
        # In tvshow season could be a case when some episodes are not available, but episode numbers
        # in response payload are set correctly.
        try:
            watching_episode = watching_season["episodes"][episode["number"] - 1]
        except IndexError:
            continue
        episode_title = "s{:02d}e{:02d}".format(season_number, episode["number"])
        if episode["title"]:
            episode_title = u"{} | {}".format(episode_title, episode["title"])
        info = extract_video_info(
            item,
            {
                "season": season_number,
                "episode": episode["number"],
                "tvshowtitle": episode["title"],
                "time": watching_episode["time"],
                "duration": watching_episode["duration"],
                "playcount": watching_episode["status"],
                "mediatype": "episode",
            },
        )
        li = ExtendedListItem(
            episode_title,
            thumbnailImage=episode["thumbnail"],
            poster=item["posters"]["big"],
            video_info=info,
            properties={"id": item["id"], "isPlayable": "true"},
            addContextMenuItems=True,
        )
        if watching_episode["status"] < 1 and not selectedEpisode:
            selectedEpisode = True
            li.select(selectedEpisode)
        url = plugin.build_url("play", item["id"], episode["number"])
        playback_data[episode["number"]] = {
            "video_data": episode,
            "video_info": info,
            "poster": item["posters"]["big"],
            "title": episode_title,
        }
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, False)
    set_window_property(playback_data)
    xbmcplugin.endOfDirectory(plugin.handle, cacheToDisc=False)


@plugin.route("/play/<item_id>/<index>")
def play(item_id, index):
    properties = {}
    if (
        "hls" in plugin.settings.stream_type
        and plugin.settings.inputstream_adaptive_enabled == "true"
        and inputstreamhelper
    ):
        helper = inputstreamhelper.Helper("hls")
        if not helper.check_inputstream():
            return
        else:
            properties.update(
                {
                    "inputstreamaddon": helper.inputstream_addon,
                    "inputstream.adaptive.manifest_type": "hls",
                }
            )
    playback_data = get_window_property(index)
    video_data = playback_data.get("video_data")
    video_info = playback_data["video_info"]
    if not video_data:
        response = KinoPubClient("items/{}".format(item_id)).get()
        video_data = response["item"]["videos"][0]
        video_info = extract_video_info(response["item"], video_info)
    if "files" not in video_data:
        notice("Видео обновляется и временно не доступно!", "Видео в обработке", time=8000)
        return
    url = get_mlink(
        video_data,
        quality=plugin.settings.video_quality,
        stream_type=plugin.settings.stream_type,
        ask_quality=plugin.settings.ask_quality,
    )
    properties.update(
        {
            "id": item_id,
            "play_duration": video_info["duration"],
            "play_resumetime": video_info["time"],
            "video_number": video_info.get("episode", 1),
            "season_number": video_info.get("season", ""),
            "playcount": video_info["playcount"],
            "imdbnumber": video_info["imdbnumber"],
        }
    )
    li = ExtendedListItem(
        playback_data["title"],
        path=url,
        properties=properties,
        poster=playback_data["poster"],
        subtitles=[subtitle["url"] for subtitle in video_data["subtitles"]],
    )
    player = Player(list_item=li)
    xbmcplugin.setResolvedUrl(plugin.handle, True, li)
    while player.is_playing:
        player.set_marktime()
        xbmc.sleep(1000)


@plugin.route("/trailer/<item_id>")
def trailer(item_id):
    response = KinoPubClient("items/trailer").get(data={"id": item_id})
    trailer = response["trailer"]
    url = get_mlink(
        trailer, quality=plugin.settings.video_quality, stream_type=plugin.settings.stream_type
    )
    li = ExtendedListItem("Трейлер", path=url)
    xbmcplugin.setResolvedUrl(plugin.handle, True, li)


@plugin.route("/search")
def search():
    kbd = xbmc.Keyboard()
    kbd.setHeading("Поиск")
    kbd.doModal()
    if kbd.isConfirmed():
        title = kbd.getText()
        if len(title.decode("utf-8")) >= 3:
            url = plugin.build_url("items", content_type=plugin.kwargs["content_type"], title=title)
            plugin.redirect(url)
        else:
            notice("Введите больше символов для поиска", "Поиск")


@plugin.route("/bookmarks")
def bookmarks():
    img = build_icon_path("create_bookmarks_folder")
    li = ExtendedListItem("Создать папку", iconImage=img, thumbnailImage=img)
    url = plugin.build_url("create_bookmarks_folder")
    xbmcplugin.addDirectoryItem(plugin.handle, url, li, False)
    response = KinoPubClient("bookmarks").get()
    for folder in response["items"]:
        img = build_icon_path("bookmark")
        li = ExtendedListItem(
            folder["title"],
            iconImage=img,
            thumbnailImage=img,
            properties={"folder-id": str(folder["id"]), "views": str(folder["views"])},
        )
        url = plugin.build_url("remove_bookmarks_folder", folder["id"])
        li.addContextMenuItems([("Удалить", "Container.Update({})".format(url))])
        url = plugin.build_url("bookmarks", folder["id"])
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/bookmarks/<folder_id>")
def show_bookmark_folder(folder_id=None):
    response = KinoPubClient("bookmarks/{}".format(folder_id)).get()
    xbmcplugin.setContent(plugin.handle, "videos")
    show_items(response["items"])
    show_pagination(response["pagination"], "bookmarks", folder_id=folder_id)


@plugin.route("/watching")
def watching():
    response = KinoPubClient("watching/serials").get(data={"subscribed": 1})
    xbmcplugin.setContent(plugin.handle, "tvshows")
    for item in response["items"]:
        title = u"{} : [COLOR FFFFF000]+{}[/COLOR]".format(item["title"], item["new"])
        li = ExtendedListItem(
            title,
            str(item["new"]),
            poster=item["posters"]["big"],
            properties={"id": str(item["id"]), "in_watchlist": "1"},
            video_info={"mediatype": content_type_map[item["type"]]},
            addContextMenuItems=True,
        )
        url = plugin.build_url("seasons", item["id"])
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)
    xbmcplugin.endOfDirectory(plugin.handle, cacheToDisc=False)


@plugin.route("/watching_movies")
def watching_movies():
    xbmcplugin.setContent(plugin.handle, "movies")
    playback_data = {}
    for i, item in enumerate(KinoPubClient("watching/movies").get()["items"]):
        li = ExtendedListItem(
            item["title"],
            poster=item["posters"]["big"],
            properties={"id": item["id"]},
            video_info={"mediatype": content_type_map[item["type"]]},
            addContextMenuItems=True,
        )
        if item["subtype"] == "multi":
            url = plugin.build_url("episodes", item["id"])
            isdir = True
        else:
            response = KinoPubClient("items/{}".format(item["id"])).get()
            watching_info = KinoPubClient("watching").get(data={"id": item["id"]})["item"]["videos"]
            watching_info = watching_info[0]
            video_info = extract_video_info(
                response["item"],
                {
                    "time": watching_info["time"],
                    "duration": watching_info["duration"],
                    "playcount": watching_info["status"],
                },
            )
            li.setInfo("video", video_info)
            li.setProperty("isPlayable", "true")
            li.setResumeTime(watching_info["time"])
            url = plugin.build_url("play", item["id"], i)
            playback_data[i] = {
                "video_info": video_info,
                "poster": item["posters"]["big"],
                "title": item["title"],
            }
            isdir = False
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, isdir)
    set_window_property(playback_data)
    xbmcplugin.endOfDirectory(plugin.handle, cacheToDisc=False)


@plugin.route("/collections")
def collections():
    response = KinoPubClient("collections/index").get(data=plugin.kwargs)
    xbmcplugin.setContent(plugin.handle, "movies")

    img = build_icon_path("new")
    li = ExtendedListItem("Последние", iconImage=img, thumbnailImage=img)
    url = plugin.build_url("collections", sort="-created")
    xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)

    img = build_icon_path("hot")
    li = ExtendedListItem("Просматриваемые", iconImage=img, thumbnailImage=img)
    url = plugin.build_url("collections", sort="-watchers")
    xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)

    img = build_icon_path("popular")
    li = ExtendedListItem("Популярные", iconImage=img, thumbnailImage=img)
    url = plugin.build_url("collections", sort="-views")
    xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)
    for item in response["items"]:
        li = ExtendedListItem(item["title"], thumbnailImage=item["posters"]["medium"])
        url = plugin.build_url("collection_view", item["id"])
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)
    show_pagination(response["pagination"], "collections", **plugin.kwargs)


@plugin.route("/collection_view/<item_id>")
def collection_view(item_id):
    response = KinoPubClient("collections/view").get(data={"id": item_id})
    show_items(response["items"], add_indexes=True)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/alphabet/<content_type>")
def alphabet(content_type):
    # fmt: off
    letters = [
        "А", "Б", "В", "Г", "Д", "Е", "Ё", "Ж", "З", "И", "Й", "К", "Л", "М", "Н", "О", "П", "Р",
        "С", "Т", "У", "Ф", "Х", "Ц", "Ч", "Ш", "Щ", "Ы", "Э", "Ю", "Я", "A", "B", "C", "D", "E",
        "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W",
        "X", "Y", "Z",
    ]
    # fmt: on
    for letter in letters:
        li = ExtendedListItem(letter)
        url = plugin.build_url("items", content_type=content_type, letter=letter, sort="title")
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/toggle_watched/<item_id>")
def toggle_watched(item_id):
    data = copy(plugin.kwargs)
    data["id"] = item_id
    KinoPubClient("watching/toggle").get(data=data)
    if "video" in data:
        data["time"] = 0
        KinoPubClient("watching/marktime").get(data=data)


@plugin.route("/toggle_watchlist/<item_id>")
def toggle_watchlist(item_id):
    added = int(plugin.kwargs["added"])
    KinoPubClient("watching/togglewatchlist").get(data={"id": item_id})
    if added:
        notice('Сериал добавлен в список "Буду смотреть"')
    else:
        notice('Сериал удалён из списка "Буду смотреть"')


@plugin.route("/edit_bookmarks/<item_id>")
def edit_bookmarks(item_id):
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
        KinoPubClient("bookmarks/add").post(data={"item": item_id, "folder": get_folder_id(folder)})
    for folder in folders_to_remove:
        KinoPubClient("bookmarks/remove-item").post(
            data={"item": item_id, "folder": get_folder_id(folder)}
        )
    notice("Закладки для видео изменены")


@plugin.route("/remove_bookmarks_folder/<folder_id>")
def remove_bookmarks_folder(folder_id):
    KinoPubClient("bookmarks/remove-folder").post(data={"folder": folder_id})


@plugin.route("/create_bookmarks_folder")
def create_bookmarks_folder():
    kbd = xbmc.Keyboard()
    kbd.setHeading("Имя папки закладок")
    kbd.doModal()
    if kbd.isConfirmed():
        title = kbd.getText()
        KinoPubClient("bookmarks/create").post(data={"title": title})


@plugin.route("/profile")
def profile():
    user_data = KinoPubClient("user").get()["user"]
    reg_date = date.fromtimestamp(user_data["reg_date"])
    dialog = xbmcgui.Dialog()
    dialog.ok(
        "Информация о профиле",
        "Имя пользователя: [B]{}[/B]".format(user_data["username"]),
        "Дата регистрации: [B]{0:%d}.{0:%m}.{0:%Y}[/B]".format(reg_date),
        "Остаток дней подписки: [B]{}[/B]".format(int(user_data["subscription"]["days"])),
    )


@plugin.route("/comments/<item_id>")
def comments(item_id):
    response = KinoPubClient("items/comments").get(data={"id": item_id})
    comments = response["comments"]
    title = response["item"]["title"]
    message = "" if comments else "Пока тут пусто"
    for i in comments:
        if int(i["rating"]) > 0:
            rating = " [COLOR FF00B159](+{})[/COLOR]".format(i["rating"])
        elif int(i["rating"]) < 0:
            rating = " [COLOR FFD11141]({})[/COLOR]".format(i["rating"])
        else:
            rating = ""
        message = u"{}[COLOR FFFFF000]{}[/COLOR]{}: {}\n\n".format(
            message, i["user"]["name"], rating, i["message"].replace("\n", " ")
        )
    dialog = xbmcgui.Dialog()
    dialog.textviewer(u'Комментарии "{}"'.format(title), message)


@plugin.route("/similar/<item_id>")
def similar(item_id):
    response = KinoPubClient("items/similar").get(data={"id": item_id})
    if not response["items"]:
        dialog = xbmcgui.Dialog()
        dialog.ok("Похожие фильмы: {}".format(plugin.kwargs["title"]), "Пока тут пусто")
    else:
        show_items(response["items"])
        xbmcplugin.endOfDirectory(plugin.handle, cacheToDisc=False)


@plugin.route("/inputstream_helper_install")
def install_inputstream_helper():
    try:
        xbmcaddon.Addon("script.module.inputstreamhelper")
        notice("inputstream helper установлен")
    except RuntimeError:
        xbmc.executebuiltin("InstallAddon(script.module.inputstreamhelper)")
