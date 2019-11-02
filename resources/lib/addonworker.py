# -*- coding: utf-8 -*-
from datetime import date

try:
    import inputstreamhelper
except ImportError:
    inputstreamhelper = None
from settings import settings
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
from utils import (
    get_internal_link,
    get_mlink,
    nav_internal_link,
    notice,
    request,
    route,
    ROUTES,
    trailer_link,
    video_info as extract_video_info,
    get_window_property,
    set_window_property,
    build_icon_path,
)
from auth import auth
from client import KinoPubClient
from listitem import ExtendedListItem
from main_menu import main_menu_items
from player import Player


mediatype_map = {
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
        link = get_internal_link(action, **kwargs)
        xbmcplugin.addDirectoryItem(request.handle, link, li, True)
    xbmcplugin.endOfDirectory(request.handle, cacheToDisc=False)


def show_items(items, add_indexes=False):
    playback_data = {}
    # Fill list with items
    for index, item in enumerate(items, 1):
        title = item["title"].encode("utf-8")
        title = "{}. {}".format(index, title) if add_indexes else title
        li = ExtendedListItem(title, poster=item["posters"]["big"], properties={"id": item["id"]})
        if "in_watchlist" in item:
            li.setProperty("in_watchlist", str(int(item["in_watchlist"])))
        video_info = extract_video_info(
            item, {"trailer": trailer_link(item), "mediatype": mediatype_map[item["type"]]}
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
            link = get_internal_link("play", id=item["id"], index=index)
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
            link = get_internal_link("view_episodes", id=item["id"])
            isdir = True
        else:
            link = get_internal_link("view_seasons", id=item["id"])
            isdir = True
        li.setInfo("video", video_info)
        li.addPredefinedContextMenuItems()
        li.markAdvert(item["advert"])
        xbmcplugin.addDirectoryItem(request.handle, link, li, isdir)


def add_default_headings(type=None, fmt="slp"):
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
        link = get_internal_link("search", type=type)
        xbmcplugin.addDirectoryItem(request.handle, link, li, False)
    if "l" in fmt:
        img = build_icon_path("new")
        li = ExtendedListItem("Последние", iconImage=img, thumbnailImage=img)
        link = get_internal_link("items", type=type)
        xbmcplugin.addDirectoryItem(request.handle, link, li, True)
    if "p" in fmt:
        img = build_icon_path("popular")
        li = ExtendedListItem("Популярные", iconImage=img, thumbnailImage=img)
        link = get_internal_link("items", type=type, shortcut="/popular")
        xbmcplugin.addDirectoryItem(request.handle, link, li, True)
    if "a" in fmt:
        img = build_icon_path("alphabet")
        li = ExtendedListItem("По алфавиту", iconImage=img, thumbnailImage=img)
        link = get_internal_link("alphabet", type=type)
        xbmcplugin.addDirectoryItem(request.handle, link, li, True)
    if "g" in fmt:
        img = build_icon_path("genres")
        li = ExtendedListItem("Жанры", iconImage=img, thumbnailImage=img)
        link = get_internal_link("genres", type=type)
        xbmcplugin.addDirectoryItem(request.handle, link, li, True)
    if "h" in fmt:
        img = build_icon_path("hot")
        li = ExtendedListItem("Горячие", iconImage=img, thumbnailImage=img)
        link = get_internal_link("items", type=type, shortcut="/hot")
        xbmcplugin.addDirectoryItem(request.handle, link, li, True)


@route("/login")
def login():
    auth.get_token()


@route("/reset_auth")
def reset_auth():
    settings.access_token = ""
    settings.access_token_expire = ""
    settings.refresh_token = ""


@route("/")
def index():
    """Main screen - show type list"""
    if not settings.access_token:
        # Use icons from lib for default headings
        li = ExtendedListItem("Активировать устройство", iconImage=build_icon_path("activate"))
        xbmcplugin.addDirectoryItem(request.handle, get_internal_link("login"), li, False)
    else:
        response = KinoPubClient("types").get()
        # Use icons from lib for default headings
        img = build_icon_path("profile")
        li = ExtendedListItem("Профиль", iconImage=img, thumbnailImage=img)
        xbmcplugin.addDirectoryItem(request.handle, get_internal_link("profile"), li, False)
        for menu_item in main_menu_items:
            if menu_item.is_displayed:
                li = ExtendedListItem(
                    menu_item.title, iconImage=menu_item.icon, thumbnailImage=menu_item.icon
                )
                xbmcplugin.addDirectoryItem(request.handle, menu_item.link, li, menu_item.is_dir)
        for i in response["items"]:
            if getattr(settings, "show_{}".format(i["id"])) != "false":
                img = build_icon_path(i["id"])
                li = ExtendedListItem(i["title"].encode("utf-8"))
                li = ExtendedListItem(i["title"].encode("utf-8"), iconImage=img, thumbnailImage=img)
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
        li = ExtendedListItem(ch["title"].encode("utf-8"), iconImage=ch["logos"]["s"])
        xbmcplugin.addDirectoryItem(request.handle, ch["stream"], li, False)
    xbmcplugin.endOfDirectory(request.handle)


@route("/genres")
def genres(type):
    response = KinoPubClient("genres").get(data={"type": type})
    add_default_headings(type)
    for genre in response["items"]:
        li = ExtendedListItem(genre["title"].encode("utf-8"))
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
    xbmcplugin.setContent(request.handle, "{}s".format(mediatype_map.get(type, "video")))
    show_items(response["items"])
    show_pagination(pagination, "items", **kwargs)


@route("/view_seasons")
def seasons(id):
    item = KinoPubClient("items/{}".format(id)).get()["item"]
    watching_info = KinoPubClient("watching").get(data={"id": item["id"]})["item"]
    selectedSeason = False
    xbmcplugin.setContent(request.handle, "tvshows")
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
        link = get_internal_link("view_season_episodes", id=id, season_number=season["number"])
        xbmcplugin.addDirectoryItem(request.handle, link, li, True)
    xbmcplugin.endOfDirectory(request.handle, cacheToDisc=False)


@route("/view_episodes")
def episodes(id):
    item = KinoPubClient("items/{}".format(id)).get()["item"]
    watching_info = KinoPubClient("watching").get(data={"id": id})["item"]
    xbmcplugin.setContent(request.handle, "episodes")
    playback_data = {}
    for video in item["videos"]:
        watching_episode = watching_info["videos"][video["number"] - 1]
        episode_title = "e{:02d}".format(video["number"])
        if video["title"]:
            episode_title = "{} | {}".format(episode_title, video["title"].encode("utf-8"))
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
        link = get_internal_link("play", id=item["id"], index=video["number"])
        playback_data[video["number"]] = {
            "video_data": video,
            "video_info": info,
            "poster": item["posters"]["big"],
            "title": episode_title,
        }
        xbmcplugin.addDirectoryItem(request.handle, link, li, False)
    set_window_property(playback_data)
    xbmcplugin.endOfDirectory(request.handle, cacheToDisc=False)


@route("/view_season_episodes")
def season_episodes(id, season_number):
    item = KinoPubClient("items/{}".format(id)).get()["item"]
    watching_info = KinoPubClient("watching").get(data={"id": id})["item"]
    season_number = int(season_number)
    season = item["seasons"][season_number - 1]
    watching_season = watching_info["seasons"][season_number - 1]
    selectedEpisode = False
    xbmcplugin.setContent(request.handle, "episodes")
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
            episode_title = "{} | {}".format(episode_title, episode["title"].encode("utf-8"))
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
        link = get_internal_link("play", id=item["id"], index=episode["number"])
        playback_data[episode["number"]] = {
            "video_data": episode,
            "video_info": info,
            "poster": item["posters"]["big"],
            "title": episode_title,
        }
        xbmcplugin.addDirectoryItem(request.handle, link, li, False)
    set_window_property(playback_data)
    xbmcplugin.endOfDirectory(request.handle, cacheToDisc=False)


@route("/play")
def play(id, index):
    properties = {}
    if (
        "hls" in settings.stream_type
        and settings.inputstream_adaptive_enabled == "true"
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
        response = KinoPubClient("items/{}".format(id)).get()
        video_data = response["item"]["videos"][0]
        video_info = extract_video_info(response["item"], video_info)
    if "files" not in video_data:
        notice("Видео обновляется и временно не доступно!", "Видео в обработке", time=8000)
        return
    url = get_mlink(
        video_data,
        quality=settings.video_quality,
        stream_type=settings.stream_type,
        ask_quality=settings.ask_quality,
    )
    properties.update(
        {
            "id": id,
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
    xbmcplugin.setResolvedUrl(request.handle, True, li)
    while player.is_playing:
        player.set_marktime()
        xbmc.sleep(1000)


@route("/trailer")
def trailer(id, sid=None):
    response = KinoPubClient("items/trailer").get(data={"id": id})
    trailer = response["trailer"]
    if "files" in trailer:
        url = get_mlink(trailer, quality=settings.video_quality, stream_type=settings.stream_type)
    elif sid is not None:
        url = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid={}"
        url = url.format(sid)
    li = ExtendedListItem("Трейлер", path=url)
    xbmcplugin.setResolvedUrl(request.handle, True, li)


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
        img = build_icon_path("create_bookmarks_folder")
        li = ExtendedListItem("Создать папку", iconImage=img, thumbnailImage=img)
        link = get_internal_link("create_bookmarks_folder")
        xbmcplugin.addDirectoryItem(request.handle, link, li, False)
        response = KinoPubClient("bookmarks").get()
        for folder in response["items"]:
            img = build_icon_path("bookmark")
            li = ExtendedListItem(
                folder["title"].encode("utf-8"),
                iconImage=img,
                thumbnailImage=img,
                properties={
                    "folder-id": str(folder["id"]).encode("utf-8"),
                    "views": str(folder["views"]).encode("utf-8"),
                },
            )
            remove_link = get_internal_link("remove_bookmarks_folder", folder_id=folder["id"])
            li.addContextMenuItems([("Удалить", "Container.Update({})".format(remove_link))])
            link = get_internal_link("bookmarks", folder_id=folder["id"])
            xbmcplugin.addDirectoryItem(request.handle, link, li, True)
        xbmcplugin.endOfDirectory(request.handle)
    else:
        # Show content of the folder
        response = KinoPubClient("bookmarks/{}".format(folder_id)).get(data={"page": page})
        xbmcplugin.setContent(request.handle, "videos")
        show_items(response["items"])
        show_pagination(response["pagination"], "bookmarks", folder_id=folder_id)


@route("/watching")
def watching():
    response = KinoPubClient("watching/serials").get(data={"subscribed": 1})
    xbmcplugin.setContent(request.handle, "tvshows")
    for item in response["items"]:
        title = "{} : [COLOR FFFFF000]+{}[/COLOR]".format(
            item["title"].encode("utf-8"), str(item["new"])
        )
        li = ExtendedListItem(
            title,
            str(item["new"]),
            poster=item["posters"]["big"],
            properties={"id": str(item["id"]), "in_watchlist": "1"},
            video_info={"mediatype": mediatype_map[item["type"]]},
            addContextMenuItems=True,
        )
        link = get_internal_link("view_seasons", id=item["id"])
        xbmcplugin.addDirectoryItem(request.handle, link, li, True)
    xbmcplugin.endOfDirectory(request.handle, cacheToDisc=False)


@route("/watching_movies")
def watching_movies():
    xbmcplugin.setContent(request.handle, "movies")
    playback_data = {}
    for i, item in enumerate(KinoPubClient("watching/movies").get()["items"]):
        li = ExtendedListItem(
            item["title"].encode("utf-8"),
            poster=item["posters"]["big"],
            properties={"id": item["id"]},
            video_info={"mediatype": mediatype_map[item["type"]]},
            addContextMenuItems=True,
        )
        if item["subtype"] == "multi":
            link = get_internal_link("view_episodes", id=item["id"])
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
            link = get_internal_link("play", id=item["id"], index=i)
            playback_data[i] = {
                "video_info": video_info,
                "poster": item["posters"]["big"],
                "title": item["title"].encode("utf-8"),
            }
            isdir = False
        xbmcplugin.addDirectoryItem(request.handle, link, li, isdir)
    set_window_property(playback_data)
    xbmcplugin.endOfDirectory(request.handle, cacheToDisc=False)


@route("/collections")
def collections(sort=None, page=None):
    response = KinoPubClient("collections/index").get(data={"sort": sort, "page": page})
    xbmcplugin.setContent(request.handle, "movies")

    img = build_icon_path("new")
    li = ExtendedListItem("Последние", iconImage=img, thumbnailImage=img)
    link = get_internal_link("collections", sort="-created")
    xbmcplugin.addDirectoryItem(request.handle, link, li, True)

    img = build_icon_path("hot")
    li = ExtendedListItem("Просматриваемые", iconImage=img, thumbnailImage=img)
    link = get_internal_link("collections", sort="-watchers")
    xbmcplugin.addDirectoryItem(request.handle, link, li, True)

    img = build_icon_path("popular")
    li = ExtendedListItem("Популярные", iconImage=img, thumbnailImage=img)
    link = get_internal_link("collections", sort="-views")
    xbmcplugin.addDirectoryItem(request.handle, link, li, True)
    for item in response["items"]:
        li = ExtendedListItem(
            item["title"].encode("utf-8"), thumbnailImage=item["posters"]["medium"]
        )
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
        "A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z",
    ]
    for al in alpha:
        letters = al.split(",")
        for letter in letters:
            li = ExtendedListItem(letter)
            link = get_internal_link("items", type=type, letter=letter)
            xbmcplugin.addDirectoryItem(request.handle, link, li, True)
    xbmcplugin.endOfDirectory(request.handle)


@route("/toggle_watched")
def toggle_watched(**data):
    KinoPubClient("watching/toggle").get(data=data)
    if "video" in data:
        data["time"] = 0
        KinoPubClient("watching/marktime").get(data=data)


@route("/toggle_watchlist")
def toggle_watchlist(**kwargs):
    added = int(kwargs.pop("added"))
    KinoPubClient("watching/togglewatchlist").get(data=kwargs)
    if added:
        notice('Сериал добавлен в список "Буду смотреть"')
    else:
        notice('Сериал удалён из списка "Буду смотреть"')


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
        KinoPubClient("bookmarks/add").post(data={"item": item_id, "folder": get_folder_id(folder)})
    for folder in folders_to_remove:
        KinoPubClient("bookmarks/remove-item").post(
            data={"item": item_id, "folder": get_folder_id(folder)}
        )
    notice("Закладки для видео изменены")


@route("/remove_bookmarks_folder")
def remove_bookmark_folder(folder_id):
    KinoPubClient("bookmarks/remove-folder").post(data={"folder": folder_id})


@route("/create_bookmarks_folder")
def create_bookmarks_folder():
    kbd = xbmc.Keyboard()
    kbd.setHeading("Имя папки закладок")
    kbd.doModal()
    if kbd.isConfirmed():
        title = kbd.getText()
        KinoPubClient("bookmarks/create").post(data={"title": title})


@route("/profile")
def profile():
    user_data = KinoPubClient("user").get()["user"]
    reg_date = date.fromtimestamp(user_data["reg_date"])
    dialog = xbmcgui.Dialog()
    dialog.ok(
        "Информация о профиле",
        "Имя пользователя: [B]{}[/B]".format(user_data["username"]),
        "Дата регистрации: [B]{0:%d} {0:%B} {0:%Y}[/B]".format(reg_date),
        "Остаток дней подписки: [B]{}[/B]".format(int(user_data["subscription"]["days"])),
    )


@route("/comments")
def comments(item_id=None):
    response = KinoPubClient("items/comments").get(data={"id": item_id})
    comments = response["comments"]
    title = response["item"]["title"].encode("utf-8")
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
    dialog.textviewer('Комментарии "{}"'.format(title), message)


@route("/similar")
def similar(item_id=None, title=""):
    response = KinoPubClient("items/similar").get(data={"id": item_id})
    if not response["items"]:
        dialog = xbmcgui.Dialog()
        dialog.ok("Похожие фильмы: {}".format(title), u"Пока тут пусто")
    else:
        show_items(response["items"])
        xbmcplugin.endOfDirectory(request.handle, cacheToDisc=False)


@route("/inputstream_helper_install")
def install_inputstream_helper():
    try:
        xbmcaddon.Addon("script.module.inputstreamhelper")
        notice("inputstream helper установлен")
    except RuntimeError:
        xbmc.executebuiltin("InstallAddon(script.module.inputstreamhelper)")


# Entry point
def init():
    ROUTES[request.path](**request.args)
