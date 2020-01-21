# -*- coding: utf-8 -*-
from datetime import date

try:
    import inputstreamhelper
except ImportError:
    inputstreamhelper = None
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

from resources.lib.utils import (
    get_mlink,
    notice,
    trailer_link,
    video_info as extract_video_info,
    get_window_property,
    set_window_property,
)
from resources.lib.player import Player
from resources.lib.plugin import Plugin


content_type_map = {
    "all": "video",
    "serial": "tvshow",
    "docuserial": "tvshow",
    "tvshow": "tvshow",
    "concert": "musicvideo",
    "3d": "movie",
    "documovie": "movie",
    "movie": "movie",
}


plugin = Plugin()


def show_pagination(pagination):
    """Add "next page" button"""
    if pagination and (int(pagination["current"]) + 1 <= int(pagination["total"])):
        page = int(pagination["current"]) + 1
        img = plugin.routing.build_icon_path("next_page")
        li = plugin.list_item("[COLOR FFFFF000]Вперёд[/COLOR]", iconImage=img, thumbnailImage=img)
        url = plugin.routing.add_kwargs_to_url(page=page)
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)
    xbmcplugin.endOfDirectory(plugin.handle, cacheToDisc=False)


def show_items(items, content_type, add_indexes=False):
    xbmcplugin.setContent(plugin.handle, content_type_map[content_type.rstrip("s")])
    playback_data = {}
    # Fill list with items
    for index, item in enumerate(items, 1):
        title = item["title"]
        title = "{}. {}".format(index, title) if add_indexes else title
        li = plugin.list_item(
            title,
            poster=item["posters"]["big"],
            fanart=item["posters"]["wide"],
            properties={"id": item["id"]},
        )
        if "in_watchlist" in item:
            li.setProperty("in_watchlist", str(int(item["in_watchlist"])))
        video_info = extract_video_info(
            item, {"trailer": trailer_link(item), "mediatype": content_type_map[item["type"]]}
        )
        # If not serials or multiseries movie, create a playable item
        if item["type"] not in ["serial", "docuserial", "tvshow"] and not item["subtype"]:
            watching_info = plugin.client("watching").get(data={"id": item["id"]})["item"][
                "videos"
            ][0]
            video_info.update(
                {
                    "time": watching_info["time"],
                    "duration": watching_info["duration"],
                    "playcount": watching_info["status"],
                }
            )
            link = plugin.routing.build_url("play", item["id"], index)
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
            watching_info = plugin.client("watching").get(data={"id": item["id"]})["item"]
            li.setProperty("subtype", "multi")
            video_info.update({"playcount": watching_info["status"]})
            link = plugin.routing.build_url("episodes", item["id"])
            isdir = True
        else:
            link = plugin.routing.build_url("seasons", item["id"])
            isdir = True
        li.setInfo("video", video_info)
        li.addPredefinedContextMenuItems()
        li.markAdvert(item["advert"])
        xbmcplugin.addDirectoryItem(plugin.handle, link, li, isdir)


@plugin.routing.route("/login")
def login():
    plugin.auth.get_token()


@plugin.routing.route("/reset_auth")
def reset_auth():
    plugin.settings.access_token = ""
    plugin.settings.access_token_expire = ""
    plugin.settings.refresh_token = ""
    xbmc.executebuiltin("Container.Refresh")


@plugin.routing.route("/")
def index():
    """Main screen - show type list"""
    if not plugin.settings.access_token:
        li = plugin.list_item(
            "Активировать устройство", iconImage=plugin.routing.build_icon_path("activate")
        )
        xbmcplugin.addDirectoryItem(plugin.handle, plugin.routing.build_url("login"), li, False)
    else:
        for menu_item in plugin.main_menu_items:
            if menu_item.is_displayed:
                li = plugin.list_item(
                    menu_item.title, iconImage=menu_item.icon, thumbnailImage=menu_item.icon
                )
                xbmcplugin.addDirectoryItem(plugin.handle, menu_item.url, li, menu_item.is_dir)
    xbmcplugin.endOfDirectory(plugin.handle)


def render_heading(name, localized_name, content_type, is_dir):
    img = plugin.routing.build_icon_path(name)
    li = plugin.list_item(localized_name, iconImage=img, thumbnailImage=img)
    url = plugin.routing.build_url("items", content_type, name)
    xbmcplugin.addDirectoryItem(plugin.handle, url, li, is_dir)


@plugin.routing.route("/items/<content_type>")
def headings(content_type):
    render_heading("search", "Поиск", content_type, False)
    render_heading("fresh", "Последние", content_type, True)
    render_heading("hot", "Горячие", content_type, True)
    render_heading("popular", "Популярные", content_type, True)
    render_heading("alphabet", "По алфавиту", content_type, True)
    render_heading("genres", "Жанры", content_type, True)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.routing.route("/items/<content_type>/<heading>")
def items(content_type, heading):
    if heading == "alphabet":
        alphabet(content_type)
    elif heading == "genres":
        genres(content_type)
    elif heading == "search":
        search(content_type)
    else:
        data = {"type": None if content_type == "all" else content_type.rstrip("s")}
        data.update(plugin.kwargs)
        response = plugin.client("items/{}".format(heading)).get(data=data)
        show_items(response["items"], content_type)
        show_pagination(response["pagination"])


@plugin.routing.route("/tv")
def tv():
    response = plugin.client("tv/index").get()
    for ch in response["channels"]:
        li = plugin.list_item(ch["title"], iconImage=ch["logos"]["s"])
        xbmcplugin.addDirectoryItem(plugin.handle, ch["stream"], li, False)
    xbmcplugin.endOfDirectory(plugin.handle)


def genres(content_type):
    response = plugin.client("genres").get(data={"type": content_type.rstrip("s")})
    for genre in response["items"]:
        li = plugin.list_item(genre["title"])
        url = plugin.routing.build_url("items", content_type, "genres", genre["id"])
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.routing.route("/items/<content_type>/genres/<genre>")
def genre_items(content_type, genre):
    content_type = content_type.rstrip("s")
    data = {"type": content_type, "genre": genre}
    data.update(plugin.kwargs)
    response = plugin.client("items").get(data=data)
    show_items(response["items"], content_type)
    show_pagination(response["pagination"])


def alphabet(content_type):
    # fmt: off
    letters = [
        "А", "Б", "В", "Г", "Д", "Е", "Ё", "Ж", "З", "И", "Й", "К", "Л", "М", "Н",
        "О", "П", "Р", "С", "Т", "У", "Ф", "Х", "Ц", "Ч", "Ш", "Щ", "Ы", "Э", "Ю",
        "Я", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N",
        "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",
    ]
    # fmt: on
    for letter in letters:
        li = plugin.list_item(letter)
        url = plugin.routing.build_url("items", content_type, "alphabet", letter, sort="title")
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.routing.route("/items/<content_type>/alphabet/<letter>")
def alphabet_items(content_type, letter):
    content_type = content_type.rstrip("s")
    data = {"type": content_type, "letter": letter}
    data.update(plugin.kwargs)
    response = plugin.client("items").get(data=data)
    show_items(response["items"], content_type)
    show_pagination(response["pagination"])


@plugin.routing.route("/search/<content_type>")
def search(content_type):
    kbd = xbmc.Keyboard()
    kbd.setHeading("Поиск")
    kbd.doModal()
    if kbd.isConfirmed():
        title = kbd.getText()
        plugin.logger.notice(title)
        url = plugin.routing.build_url("search", content_type, "results", title=title)
        plugin.routing.redirect(url)


@plugin.routing.route("/search/<content_type>/results")
def search_results(content_type):
    data = {
        "type": None if content_type == "all" else content_type.rstrip("s"),
        "title": plugin.kwargs["title"],
    }
    data.update(plugin.kwargs)
    response = plugin.client("items").get(data=data)
    show_items(response["items"], content_type)
    show_pagination(response["pagination"])


@plugin.routing.route("/seasons/<item_id>")
def seasons(item_id):
    item = plugin.client("items/{}".format(item_id)).get()["item"]
    watching_info = plugin.client("watching").get(data={"id": item["id"]})["item"]
    selectedSeason = False
    xbmcplugin.setContent(plugin.handle, "tvshows")
    for season in item["seasons"]:
        season_title = "Сезон {}".format(season["number"])
        watching_season = watching_info["seasons"][season["number"] - 1]
        li = plugin.list_item(
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
            fanart=item["posters"]["wide"],
            properties={"id": item["id"]},
            addContextMenuItems=True,
        )
        if watching_season["status"] < 1 and not selectedSeason:
            selectedSeason = True
            li.select(selectedSeason)
        url = plugin.routing.build_url("season_episodes", item_id, season["number"])
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)
    xbmcplugin.endOfDirectory(plugin.handle, cacheToDisc=False)


@plugin.routing.route("/episodes/<item_id>")
def episodes(item_id):
    item = plugin.client("items/{}".format(item_id)).get()["item"]
    watching_info = plugin.client("watching").get(data={"id": item_id})["item"]
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
        li = plugin.list_item(
            episode_title,
            thumbnailImage=video["thumbnail"],
            video_info=info,
            poster=item["posters"]["big"],
            fanart=item["posters"]["wide"],
            properties={"id": item["id"], "isPlayable": "true"},
            addContextMenuItems=True,
        )
        url = plugin.routing.build_url("play", item["id"], video["number"])
        playback_data[video["number"]] = {
            "video_data": video,
            "video_info": info,
            "poster": item["posters"]["big"],
            "title": episode_title,
        }
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, False)
    set_window_property(playback_data)
    xbmcplugin.endOfDirectory(plugin.handle, cacheToDisc=False)


@plugin.routing.route("/season_episodes/<item_id>/<season_number>")
def season_episodes(item_id, season_number):
    item = plugin.client("items/{}".format(item_id)).get()["item"]
    watching_info = plugin.client("watching").get(data={"id": item_id})["item"]
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
            episode_title = "{} | {}".format(episode_title, episode["title"])
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
        li = plugin.list_item(
            episode_title,
            thumbnailImage=episode["thumbnail"],
            poster=item["posters"]["big"],
            fanart=item["posters"]["wide"],
            video_info=info,
            properties={"id": item["id"], "isPlayable": "true"},
            addContextMenuItems=True,
        )
        if watching_episode["status"] < 1 and not selectedEpisode:
            selectedEpisode = True
            li.select(selectedEpisode)
        url = plugin.routing.build_url("play", item["id"], episode["number"])
        playback_data[episode["number"]] = {
            "video_data": episode,
            "video_info": info,
            "poster": item["posters"]["big"],
            "title": episode_title,
        }
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, False)
    set_window_property(playback_data)
    xbmcplugin.endOfDirectory(plugin.handle, cacheToDisc=False)


@plugin.routing.route("/play/<item_id>/<index>")
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
        response = plugin.client("items/{}".format(item_id)).get()
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
            "item_id": item_id,
            "play_duration": video_info["duration"],
            "play_resumetime": video_info["time"],
            "video_number": video_info.get("episode", 1),
            "season_number": video_info.get("season", ""),
            "playcount": video_info["playcount"],
            "imdbnumber": video_info["imdbnumber"],
        }
    )
    li = plugin.list_item(
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


@plugin.routing.route("/trailer/<item_id>")
def trailer(item_id):
    response = plugin.client("items/trailer").get(data={"id": item_id})
    url = response["trailer"][0]["url"]
    li = plugin.list_item("Трейлер", path=url)
    xbmcplugin.setResolvedUrl(plugin.handle, True, li)


@plugin.routing.route("/bookmarks")
def bookmarks():
    img = plugin.routing.build_icon_path("create_bookmarks_folder")
    li = plugin.list_item("Создать папку", iconImage=img, thumbnailImage=img)
    url = plugin.routing.build_url("create_bookmarks_folder")
    xbmcplugin.addDirectoryItem(plugin.handle, url, li, False)
    response = plugin.client("bookmarks").get()
    for folder in response["items"]:
        img = plugin.routing.build_icon_path("bookmark")
        li = plugin.list_item(
            folder["title"],
            iconImage=img,
            thumbnailImage=img,
            properties={"folder-id": str(folder["id"]), "views": str(folder["views"])},
        )
        url = plugin.routing.build_url("remove_bookmarks_folder", folder["id"])
        li.addContextMenuItems([("Удалить", "Container.Update({})".format(url))])
        url = plugin.routing.build_url("bookmarks", folder["id"])
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.routing.route("/bookmarks/<folder_id>")
def show_bookmark_folder(folder_id):
    response = plugin.client("bookmarks/{}".format(folder_id)).get(data=plugin.kwargs)
    show_items(response["items"], content_type="all")
    show_pagination(response["pagination"])


@plugin.routing.route("/watching")
def watching():
    response = plugin.client("watching/serials").get(data={"subscribed": 1})
    xbmcplugin.setContent(plugin.handle, "tvshows")
    for item in response["items"]:
        title = "{} : [COLOR FFFFF000]+{}[/COLOR]".format(item["title"], item["new"])
        li = plugin.list_item(
            title,
            str(item["new"]),
            poster=item["posters"]["big"],
            properties={"id": str(item["id"]), "in_watchlist": "1"},
            video_info={"mediatype": content_type_map[item["type"]]},
            addContextMenuItems=True,
        )
        url = plugin.routing.build_url("seasons", item["id"])
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)
    xbmcplugin.endOfDirectory(plugin.handle, cacheToDisc=False)


@plugin.routing.route("/watching_movies")
def watching_movies():
    xbmcplugin.setContent(plugin.handle, "movies")
    playback_data = {}
    for i, item in enumerate(plugin.client("watching/movies").get()["items"]):
        li = plugin.list_item(
            item["title"],
            poster=item["posters"]["big"],
            properties={"id": item["id"]},
            video_info={"mediatype": content_type_map[item["type"]]},
            addContextMenuItems=True,
        )
        if item["subtype"] == "multi":
            url = plugin.routing.build_url("episodes", item["id"])
            isdir = True
        else:
            response = plugin.client("items/{}".format(item["id"])).get()
            watching_info = plugin.client("watching").get(data={"id": item["id"]})["item"]["videos"]
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
            url = plugin.routing.build_url("play", item["id"], i)
            playback_data[i] = {
                "video_info": video_info,
                "poster": item["posters"]["big"],
                "title": item["title"],
            }
            isdir = False
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, isdir)
    set_window_property(playback_data)
    xbmcplugin.endOfDirectory(plugin.handle, cacheToDisc=False)


@plugin.routing.route("/collections")
def collections():
    img = plugin.routing.build_icon_path("fresh")
    li = plugin.list_item("Последние", iconImage=img, thumbnailImage=img)
    url = plugin.routing.build_url("collections", "created")
    xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)

    img = plugin.routing.build_icon_path("hot")
    li = plugin.list_item("Просматриваемые", iconImage=img, thumbnailImage=img)
    url = plugin.routing.build_url("collections", "watchers")
    xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)

    img = plugin.routing.build_icon_path("popular")
    li = plugin.list_item("Популярные", iconImage=img, thumbnailImage=img)
    url = plugin.routing.build_url("collections", "views")
    xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)

    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.routing.route("/collections/<sorting>")
def sorted_collections(sorting):
    data = {"sort": "-{}".format(sorting)}
    data.update(plugin.kwargs)
    response = plugin.client("collections/index").get(data=data)
    xbmcplugin.setContent(plugin.handle, "movies")
    for item in response["items"]:
        li = plugin.list_item(item["title"], thumbnailImage=item["posters"]["medium"])
        url = plugin.routing.build_url("collection", item["id"])
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)
    show_pagination(response["pagination"])


@plugin.routing.route("/collection/<item_id>")
def collection(item_id):
    response = plugin.client("collections/view").get(data={"id": item_id})
    show_items(response["items"], content_type="movie", add_indexes=True)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.routing.route("/toggle_watched/<item_id>")
def toggle_watched(item_id):
    data = {"id": item_id}
    data.update(plugin.kwargs)
    plugin.client("watching/toggle").get(data=data)
    if "video" in data:
        data["time"] = 0
        plugin.client("watching/marktime").get(data=data)


@plugin.routing.route("/toggle_watchlist/<item_id>")
def toggle_watchlist(item_id):
    added = int(plugin.kwargs["added"])
    plugin.client("watching/togglewatchlist").get(data={"id": item_id})
    if added:
        notice('Сериал добавлен в список "Буду смотреть"')
    else:
        notice('Сериал удалён из списка "Буду смотреть"')


@plugin.routing.route("/edit_bookmarks/<item_id>")
def edit_bookmarks(item_id):
    item_folders_resp = plugin.client("bookmarks/get-item-folders").get(data={"item": item_id})
    all_folders_resp = plugin.client("bookmarks").get()
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
        plugin.client("bookmarks/add").post(data={"item": item_id, "folder": get_folder_id(folder)})
    for folder in folders_to_remove:
        plugin.client("bookmarks/remove-item").post(
            data={"item": item_id, "folder": get_folder_id(folder)}
        )
    notice("Закладки для видео изменены")


@plugin.routing.route("/remove_bookmarks_folder/<folder_id>")
def remove_bookmarks_folder(folder_id):
    plugin.client("bookmarks/remove-folder").post(data={"folder": folder_id})


@plugin.routing.route("/create_bookmarks_folder")
def create_bookmarks_folder():
    kbd = xbmc.Keyboard()
    kbd.setHeading("Имя папки закладок")
    kbd.doModal()
    if kbd.isConfirmed():
        title = kbd.getText()
        plugin.client("bookmarks/create").post(data={"title": title})


@plugin.routing.route("/profile")
def profile():
    user_data = plugin.client("user").get()["user"]
    reg_date = date.fromtimestamp(user_data["reg_date"])
    dialog = xbmcgui.Dialog()
    dialog.ok(
        "Информация о профиле",
        "Имя пользователя: [B]{}[/B]".format(user_data["username"]),
        "Дата регистрации: [B]{0:%d}.{0:%m}.{0:%Y}[/B]".format(reg_date),
        "Остаток дней подписки: [B]{}[/B]".format(int(user_data["subscription"]["days"])),
    )


@plugin.routing.route("/comments/<item_id>")
def comments(item_id):
    response = plugin.client("items/comments").get(data={"id": item_id})
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
        message = "{}[COLOR FFFFF000]{}[/COLOR]{}: {}\n\n".format(
            message, i["user"]["name"], rating, i["message"].replace("\n", " ")
        )
    dialog = xbmcgui.Dialog()
    dialog.textviewer('Комментарии "{}"'.format(title), message)


@plugin.routing.route("/similar/<item_id>")
def similar(item_id):
    response = plugin.client("items/similar").get(data={"id": item_id})
    if not response["items"]:
        dialog = xbmcgui.Dialog()
        dialog.ok("Похожие фильмы: {}".format(plugin.kwargs["title"]), "Пока тут пусто")
    else:
        show_items(response["items"], "movie")
        xbmcplugin.endOfDirectory(plugin.handle, cacheToDisc=False)


@plugin.routing.route("/inputstream_helper_install")
def install_inputstream_helper():
    try:
        xbmcaddon.Addon("script.module.inputstreamhelper")
        notice("inputstream helper установлен")
    except RuntimeError:
        xbmc.executebuiltin("InstallAddon(script.module.inputstreamhelper)")
