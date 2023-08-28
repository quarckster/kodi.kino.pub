from datetime import date
from typing import Any
from typing import cast
from typing import Dict
from typing import List
from typing import Optional

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

from resources.lib.modeling import ItemEntity
from resources.lib.modeling import Multi
from resources.lib.modeling import TVShow
from resources.lib.player import Player
from resources.lib.plugin import Plugin
from resources.lib.utils import localize
from resources.lib.utils import popup_info


content_type_map = {
    "all": "tvshow",
    "serial": "tvshow",
    "docuserial": "tvshow",
    "tvshow": "tvshow",
    "concert": "musicvideo",
    "3d": "movie",
    "documovie": "movie",
    "movie": "movie",
}


plugin = Plugin()


def render_pagination(pagination: Optional[Dict[str, Any]]) -> None:
    """Add "next page" and "home" buttons"""
    if pagination and (int(pagination["current"]) + 1 <= int(pagination["total"])):
        kwargs = {"page": int(pagination["current"]) + 1}
        if plugin.settings.exclude_anime == "true" and "start_from" in pagination:
            kwargs["start_from"] = pagination["start_from"]
        img = plugin.routing.build_icon_path("next_page")
        # Next
        li = plugin.list_item(
            name=f"[COLOR FFFFF000]{localize(32016)}[/COLOR]", iconImage=img, thumbnailImage=img
        )
        url = plugin.routing.add_kwargs_to_url(**kwargs)
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)
        img = plugin.routing.build_icon_path("home")
        home_url = plugin.routing.build_url("/")
        # Home
        li = plugin.list_item(
            name=f"[COLOR FFFFF000]{localize(32017)}[/COLOR]", iconImage=img, thumbnailImage=img
        )
        xbmcplugin.addDirectoryItem(plugin.handle, home_url, li, True)
    xbmcplugin.endOfDirectory(plugin.handle)


def render_items(items: List[ItemEntity], content_type: str) -> None:
    """
    Available content strings

    ======= ======== ========= ============
    files   songs    artists   albums
    movies  tvshows  episodes  musicvideos
    videos  images   games
    ======= ======== ========= ============
    """
    container_content_type = f"{content_type_map[content_type.rstrip('s')]}s"
    xbmcplugin.setContent(plugin.handle, container_content_type)
    playback_data = {}
    for item in items:
        if not item.isdir:
            playback_data[item.item_id] = item
        xbmcplugin.addDirectoryItem(plugin.handle, item.url, item.list_item, item.isdir)
    plugin.set_window_property(playback_data)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_VIDEO_RATING)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL)


@plugin.routing.route("/login/")
def login() -> None:
    plugin.auth.get_token()


@plugin.routing.route("/reset_auth/")
def reset_auth() -> None:
    plugin.settings.access_token = ""
    plugin.settings.access_token_expire = ""
    plugin.settings.refresh_token = ""
    xbmc.executebuiltin("Container.Refresh")


@plugin.routing.route("/")
def index() -> None:
    """Main screen - show type list"""
    if not plugin.settings.access_token:
        # Activate device
        li = plugin.list_item(
            name=localize(32018), iconImage=plugin.routing.build_icon_path("activate")
        )
        xbmcplugin.addDirectoryItem(plugin.handle, plugin.routing.build_url("login/"), li, False)
    else:
        for menu_item in plugin.main_menu_items:
            if menu_item.is_displayed:
                li = plugin.list_item(
                    name=menu_item.title, iconImage=menu_item.icon, thumbnailImage=menu_item.icon
                )
                xbmcplugin.addDirectoryItem(plugin.handle, menu_item.url, li, menu_item.is_dir)
    xbmcplugin.endOfDirectory(plugin.handle)


def render_heading(name: str, localized_name: str, content_type: str, is_dir: bool) -> None:
    img = plugin.routing.build_icon_path(name)
    li = plugin.list_item(name=localized_name, iconImage=img, thumbnailImage=img)
    url = plugin.routing.build_url("items", content_type, f"{name}/")
    xbmcplugin.addDirectoryItem(plugin.handle, url, li, is_dir)


@plugin.routing.route("/items/<content_type>/")
def headings(content_type: str) -> None:
    render_heading("search", localize(32019), content_type, True)
    render_heading("fresh", localize(32020), content_type, True)
    render_heading("hot", localize(32021), content_type, True)
    render_heading("popular", localize(32022), content_type, True)
    render_heading("alphabet", localize(32023), content_type, True)
    render_heading("genres", localize(32024), content_type, True)
    render_heading("sort", plugin.sorting_title, content_type, True)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.routing.route("/items/<content_type>/<heading>/")
def items(content_type: str, heading: str) -> None:
    if heading == "alphabet":
        alphabet(content_type)
    elif heading == "genres":
        genres(content_type)
    elif heading == "search":
        search(content_type)
    else:
        data = {"type": None if content_type == "all" else content_type.rstrip("s")}
        data.update(plugin.kwargs)
        exclude_anime = plugin.settings.exclude_anime == "true"
        if heading == "sort":
            data.update(plugin.sorting_params)
            response = plugin.items.get("items", data=data, exclude_anime=exclude_anime)
        else:
            response = plugin.items.get(f"items/{heading}", data=data, exclude_anime=exclude_anime)
        render_items(response.items, content_type)
        render_pagination(response.pagination)


@plugin.routing.route("/tv/")
def tv() -> None:
    response = plugin.client("tv/index").get()
    for ch in response["channels"]:
        li = plugin.list_item(name=ch["title"], iconImage=ch["logos"]["s"])
        xbmcplugin.addDirectoryItem(plugin.handle, ch["stream"], li, False)
    xbmcplugin.endOfDirectory(plugin.handle)


def genres(content_type: str) -> None:
    response = plugin.client("genres").get(data={"type": content_type.rstrip("s")})
    for genre in response["items"]:
        li = plugin.list_item(name=genre["title"])
        url = plugin.routing.build_url("items", content_type, "genres", f"{genre['id']}/")
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.routing.route("/items/<content_type>/genres/<genre>/")
def genre_items(content_type: str, genre: str) -> None:
    content_type = content_type.rstrip("s")
    data = {"type": content_type, "genre": genre, **plugin.kwargs, **plugin.sorting_params}
    response = plugin.items.get("items", data)
    render_items(response.items, content_type)
    render_pagination(response.pagination)


def alphabet(content_type: str) -> None:
    # fmt: off
    letters = [
        "А", "Б", "В", "Г", "Д", "Е", "Ё", "Ж", "З", "И", "Й", "К", "Л", "М", "Н",
        "О", "П", "Р", "С", "Т", "У", "Ф", "Х", "Ц", "Ч", "Ш", "Щ", "Ы", "Э", "Ю",
        "Я", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N",
        "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",
    ]
    # fmt: on
    for letter in letters:
        li = plugin.list_item(name=letter)
        url = plugin.routing.build_url(
            "items", content_type, "alphabet", f"{letter}/", sort="title"
        )
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.routing.route("/items/<content_type>/alphabet/<letter>/")
def alphabet_items(content_type: str, letter: str) -> None:
    content_type = content_type.rstrip("s")
    data = {"type": content_type, "letter": letter, **plugin.kwargs, **plugin.sorting_params}
    response = plugin.items.get("items", data)
    render_items(response.items, content_type)
    render_pagination(response.pagination)


@plugin.routing.route("/new_search/<content_type>/")
def new_search(content_type: str) -> None:
    kbd = xbmc.Keyboard()
    # Search
    kbd.setHeading(localize(32019))
    kbd.doModal()
    if kbd.isConfirmed():
        title = kbd.getText()
        plugin.search_history.save(title)
        url = plugin.routing.build_url("search", content_type, "results/", title=title)
        plugin.routing.redirect(url)


@plugin.routing.route("/search/<content_type>/")
def search(content_type: str) -> None:
    img = plugin.routing.build_icon_path("search")
    # New search
    li = plugin.list_item(name=localize(32025), iconImage=img, thumbnailImage=img)
    url = plugin.routing.build_url("new_search", f"{content_type}/")
    xbmcplugin.addDirectoryItem(plugin.handle, url, li, False)

    for history_item in plugin.search_history.recent:
        img = plugin.routing.build_icon_path("search_history")
        li = plugin.list_item(name=history_item, iconImage=img, thumbnailImage=img)
        url = plugin.routing.build_url("search", content_type, "results/", title=history_item)
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.routing.route("/search/<content_type>/results/")
def search_results(content_type: str) -> None:
    data = {
        "type": None if content_type == "all" else content_type.rstrip("s"),
        **plugin.kwargs,
        **plugin.sorting_params,
    }
    response = plugin.items.get("items", data)
    render_items(response.items, content_type)
    render_pagination(response.pagination)


@plugin.routing.route("/clean_search_history/")
def clean_search_history() -> None:
    # Clean search history?
    confirm = xbmcgui.Dialog().yesno("kino.pub", localize(32026))
    if confirm:
        plugin.search_history.clean()
        xbmc.executebuiltin("Container.Refresh")


@plugin.routing.route("/seasons/<item_id>/")
def seasons(item_id: str) -> None:
    tvshow = cast(TVShow, plugin.items.instantiate_from_item_id(item_id))
    xbmcplugin.setContent(plugin.handle, "tvshows")
    for season in tvshow.seasons:
        xbmcplugin.addDirectoryItem(plugin.handle, season.url, season.list_item, True)
    plugin.set_window_property({tvshow.item_id: tvshow})
    xbmcplugin.endOfDirectory(plugin.handle, cacheToDisc=False)


@plugin.routing.route("/episodes/<item_id>/")
def episodes(item_id: str) -> None:
    collection = cast(Multi, plugin.items.instantiate_from_item_id(item_id))
    xbmcplugin.setContent(plugin.handle, "episodes")
    for video in collection.videos:
        xbmcplugin.addDirectoryItem(plugin.handle, video.url, video.list_item, False)
    plugin.set_window_property({collection.item_id: collection})
    xbmcplugin.endOfDirectory(plugin.handle, cacheToDisc=False)


@plugin.routing.route("/season_episodes/<item_id>/<season_number>/")
def season_episodes(item_id: str, season_number: str) -> None:
    tvshow = cast(TVShow, plugin.items.instantiate_from_item_id(item_id))
    xbmcplugin.setContent(plugin.handle, "episodes")
    for episode in tvshow.seasons[int(season_number) - 1].episodes:
        xbmcplugin.addDirectoryItem(plugin.handle, episode.url, episode.list_item, False)
    plugin.set_window_property({tvshow.item_id: tvshow})
    xbmcplugin.endOfDirectory(plugin.handle, cacheToDisc=False)


@plugin.routing.route("/play/<item_id>")
def play(item_id: str) -> None:
    item = plugin.items.instantiate_from_item_id(item_id)
    si = plugin.kwargs.get("season_index")
    i = plugin.kwargs.get("index")
    playable_li = plugin.items.get_playable(item, season_index=si, index=i).playable_list_item
    player = Player(list_item=playable_li)
    xbmcplugin.setResolvedUrl(plugin.handle, True, playable_li)
    while player.is_playing:
        player.set_marktime()
        xbmc.sleep(1000)


@plugin.routing.route("/trailer/<item_id>")
def trailer(item_id: str) -> None:
    response = plugin.client("items/trailer").get(data={"id": item_id})
    url = response["trailer"][0]["url"]
    # Trailer
    li = plugin.list_item(name=localize(32027), path=url)
    xbmcplugin.setResolvedUrl(plugin.handle, True, li)


@plugin.routing.route("/bookmarks/")
def bookmarks() -> None:
    img = plugin.routing.build_icon_path("create_bookmarks_folder")
    # Make a folder
    li = plugin.list_item(name=localize(32028), iconImage=img, thumbnailImage=img)
    url = plugin.routing.build_url("create_bookmarks_folder")
    xbmcplugin.addDirectoryItem(plugin.handle, url, li, False)
    response = plugin.client("bookmarks").get()
    for folder in response["items"]:
        img = plugin.routing.build_icon_path("bookmark")
        li = plugin.list_item(
            name=folder["title"],
            iconImage=img,
            thumbnailImage=img,
            properties={"folder-id": str(folder["id"]), "views": str(folder["views"])},
        )
        url = plugin.routing.build_url("remove_bookmarks_folder", folder["id"])
        # Delete
        li.addContextMenuItems([(localize(32029), f"RunPlugin({url})")])
        url = plugin.routing.build_url("bookmarks", f"{folder['id']}/")
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.routing.route("/bookmarks/<folder_id>/")
def show_bookmark_folder(folder_id: str) -> None:
    response = plugin.items.get(f"bookmarks/{folder_id}", data=plugin.kwargs)
    render_items(response.items, content_type="all")
    render_pagination(response.pagination)


@plugin.routing.route("/watching/")
def watching() -> None:
    xbmcplugin.setContent(plugin.handle, "tvshows")
    for tvshow in plugin.items.watching_tvshows:
        xbmcplugin.addDirectoryItem(plugin.handle, tvshow.url, tvshow.list_item, True)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.routing.route("/watching_movies/")
def watching_movies() -> None:
    xbmcplugin.setContent(plugin.handle, "movies")
    playback_data = {}
    for movie in plugin.items.watching_movies:
        if not movie.isdir:
            playback_data[movie.item_id] = movie
        xbmcplugin.addDirectoryItem(plugin.handle, movie.url, movie.list_item, movie.isdir)
    plugin.set_window_property(playback_data)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.routing.route("/collections/")
def collections() -> None:
    img = plugin.routing.build_icon_path("fresh")
    # Fresh
    li = plugin.list_item(name=localize(32020), iconImage=img, thumbnailImage=img)
    url = plugin.routing.build_url("collections", "created/")
    xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)

    img = plugin.routing.build_icon_path("hot")
    # Hot
    li = plugin.list_item(name=localize(32021), iconImage=img, thumbnailImage=img)
    url = plugin.routing.build_url("collections", "watchers/")
    xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)

    img = plugin.routing.build_icon_path("popular")
    # Popular
    li = plugin.list_item(name=localize(32022), iconImage=img, thumbnailImage=img)
    url = plugin.routing.build_url("collections", "views/")
    xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)

    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.routing.route("/collections/<sorting>/")
def sorted_collections(sorting: str) -> None:
    data = {"sort": f"-{sorting}", **plugin.kwargs}
    response = plugin.client("collections/index").get(data=data)
    xbmcplugin.setContent(plugin.handle, "movies")
    for item in response["items"]:
        li = plugin.list_item(name=item["title"], thumbnailImage=item["posters"]["medium"])
        url = plugin.routing.build_url("collection", f"{item['id']}/")
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, True)
    render_pagination(response["pagination"])


@plugin.routing.route("/collection/<item_id>/")
def collection(item_id: str) -> None:
    response = plugin.items.get("collections/view", data={"id": item_id})
    render_items(response.items, content_type="movie")
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.routing.route("/toggle_watched/<item_id>")
def toggle_watched(item_id: str) -> None:
    data = {"id": item_id, **plugin.kwargs}
    plugin.client("watching/toggle").get(data=data)
    if "video" in data:
        data["time"] = "0"
        plugin.client("watching/marktime").get(data=data)
    plugin.clear_window_property()
    xbmc.executebuiltin("Container.Refresh")


@plugin.routing.route("/toggle_watchlist/<item_id>")
def toggle_watchlist(item_id: str) -> None:
    added = int(plugin.kwargs["added"])
    plugin.client("watching/togglewatchlist").get(data={"id": item_id})
    if added:
        # TV show has been added to the watchlist
        popup_info(localize(32030))
    else:
        # TV show has been removed from the watchlist
        popup_info(localize(32031))
    plugin.clear_window_property()
    xbmc.executebuiltin("Container.Refresh")


@plugin.routing.route("/edit_bookmarks/<item_id>")
def edit_bookmarks(item_id: str) -> None:
    item_folders_resp = plugin.client("bookmarks/get-item-folders").get(data={"item": item_id})
    all_folders_resp = plugin.client("bookmarks").get()
    all_folders = [f["title"] for f in all_folders_resp["items"]]
    item_folders = [f["title"] for f in item_folders_resp["folders"]]
    preselect = [all_folders.index(f) for f in item_folders]
    dialog = xbmcgui.Dialog()
    # Bookmarks folders
    indexes = dialog.multiselect(localize(32032), all_folders, preselect=preselect)
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
    # Bookmarks have been changed
    popup_info(localize(32033))


@plugin.routing.route("/remove_bookmarks_folder/<folder_id>")
def remove_bookmarks_folder(folder_id: str) -> None:
    plugin.client("bookmarks/remove-folder").post(data={"folder": folder_id})
    xbmc.executebuiltin("Container.Refresh")


@plugin.routing.route("/create_bookmarks_folder")
def create_bookmarks_folder() -> None:
    kbd = xbmc.Keyboard()
    # Bookmarks folder name
    kbd.setHeading(localize(32034))
    kbd.doModal()
    if kbd.isConfirmed():
        title = kbd.getText()
        plugin.client("bookmarks/create").post(data={"title": title})
        xbmc.executebuiltin("Container.Refresh")


@plugin.routing.route("/profile/")
def profile() -> None:
    user_data = plugin.client("user").get()["user"]
    reg_date = date.fromtimestamp(user_data["reg_date"])
    dialog = xbmcgui.Dialog()
    # User name, Registration date, Subscription days remaining
    message = (
        f"{localize(32035)}: [B]{user_data['username']}[/B]\n"
        f"{localize(32036)}: [B]{reg_date:%d.%m.%Y}[/B]\n"
        f"{localize(32037)}: [B]{int(user_data['subscription']['days'])}[/B]"
    )
    # Account data
    dialog.ok(localize(32038), message)


@plugin.routing.route("/inputstream_adaptive_settings/")
def inputstream_adaptive_settings() -> None:
    xbmcaddon.Addon("inputstream.adaptive").openSettings()


@plugin.routing.route("/comments/<item_id>")
def comments(item_id: str) -> None:
    response = plugin.client("items/comments").get(data={"id": item_id})
    comments = response["comments"]
    title = response["item"]["title"]
    # It's empty here
    message = "" if comments else localize(32039)
    for i in comments:
        if int(i["rating"]) > 0:
            rating = f" [COLOR FF00B159](+{i['rating']})[/COLOR]"
        elif int(i["rating"]) < 0:
            rating = f" [COLOR FFD11141]({i['rating']})[/COLOR]"
        else:
            rating = ""
        message = "{}[COLOR FFFFF000]{}[/COLOR]{}: {}\n\n".format(
            message, i["user"]["name"], rating, i["message"].replace("\n", " ")
        )
    dialog = xbmcgui.Dialog()
    # Comments
    dialog.textviewer(f'{localize(32040)} "{title}"', message)


@plugin.routing.route("/similar/<item_id>")
def similar(item_id: str) -> None:
    response = plugin.items.get("items/similar", data={"id": item_id})
    if not response.items:
        dialog = xbmcgui.Dialog()
        # Similar movies, It's empty here
        dialog.ok(f"{localize(32015)}: {plugin.kwargs['title']}", localize(32039))
    else:
        render_items(response.items, "movie")
        xbmcplugin.endOfDirectory(plugin.handle, cacheToDisc=False)


@plugin.routing.route("/inputstream_helper_install/")
def install_inputstream_helper() -> None:
    try:
        xbmcaddon.Addon("script.module.inputstreamhelper")
        # InputStream helper has been installed
        popup_info(localize(32042))
    except RuntimeError:
        xbmc.executebuiltin("InstallAddon(script.module.inputstreamhelper)")
