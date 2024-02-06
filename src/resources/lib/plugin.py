import codecs
import pickle
import sys
from collections import namedtuple
from typing import Any
from typing import ClassVar
from typing import Dict
from typing import List
from typing import Optional
from typing import Union
from urllib.parse import parse_qsl
from urllib.parse import urlsplit

import xbmcaddon
import xbmcgui

from resources.lib.auth import Auth
from resources.lib.client import KinoPubClient
from resources.lib.listitem import ExtendedListItem
from resources.lib.logger import Logger
from resources.lib.modeling import ItemsCollection
from resources.lib.modeling import Movie
from resources.lib.modeling import Multi
from resources.lib.modeling import TVShow
from resources.lib.routing import Routing
from resources.lib.search_history import SearchHistory
from resources.lib.settings import Settings
from resources.lib.utils import localize
from resources.lib.xbmc_settings import XbmcProxySettings


try:
    import inputstreamhelper
except ImportError:
    inputstreamhelper = None


MainMenuItem = namedtuple("MainMenuItem", ["title", "url", "icon", "is_dir", "is_displayed"])


class Plugin:
    PLUGIN_ID: ClassVar[str] = xbmcaddon.Addon().getAddonInfo("id")
    PLUGIN_URL: ClassVar[str] = f"plugin://{PLUGIN_ID}"
    settings: ClassVar[Settings] = Settings()

    def __init__(self) -> None:
        self.path = urlsplit(sys.argv[0]).path or "/"
        self.handle = int(sys.argv[1])
        self.kwargs = dict(parse_qsl(sys.argv[2].lstrip("?")))
        self.auth = Auth(self)
        self.logger = Logger(self)
        self.routing = Routing(self)
        self.search_history = SearchHistory(self)
        self.main_menu_items = self._main_menu_items()
        self.items = ItemsCollection(self)
        self.client = KinoPubClient(self)
        self.proxy_settings = XbmcProxySettings(self)

    def list_item(
        self,
        *,
        name: str,
        label2: str = "",
        iconImage: str = "",
        thumbnailImage: str = "",
        path: str = "",
        poster: Optional[str] = None,
        fanart: Optional[str] = None,
        video_info: Optional[Dict] = None,
        properties: Optional[Dict[str, Any]] = None,
        addContextMenuItems: bool = False,
        subtitles: Optional[List[str]] = None,
    ) -> ExtendedListItem:
        return ExtendedListItem(
            name=name,
            label2=label2,
            iconImage=iconImage,
            thumbnailImage=thumbnailImage,
            path=path,
            poster=poster,
            fanart=fanart,
            video_info=video_info,
            properties=properties,
            addContextMenuItems=addContextMenuItems,
            subtitles=subtitles,
            plugin=self,
        )

    def run(self) -> None:
        self.routing.dispatch(self.path)

    def _main_menu_items(self) -> List[MainMenuItem]:
        return [
            MainMenuItem(
                localize(32047),
                self.routing.build_url("profile/"),
                self.routing.build_icon_path("profile"),
                False,
                True,
            ),
            MainMenuItem(
                localize(32019),
                self.routing.build_url("search", "all/"),
                self.routing.build_icon_path("search"),
                True,
                self.settings.show_search,
            ),
            MainMenuItem(
                localize(32048),
                self.routing.build_url("bookmarks/"),
                self.routing.build_icon_path("bookmarks"),
                True,
                True,
            ),
            MainMenuItem(
                localize(32049),
                self.routing.build_url("watching/"),
                self.routing.build_icon_path("watching"),
                True,
                True,
            ),
            MainMenuItem(
                localize(32050),
                self.routing.build_url("watching_movies/"),
                self.routing.build_icon_path("watching_movies"),
                True,
                True,
            ),
            MainMenuItem(
                localize(32020),
                self.routing.build_url("items", "all", "fresh/"),
                self.routing.build_icon_path("fresh"),
                True,
                self.settings.show_last,
            ),
            MainMenuItem(
                localize(32022),
                self.routing.build_url("items", "all", "popular/"),
                self.routing.build_icon_path("popular"),
                True,
                self.settings.show_popular,
            ),
            MainMenuItem(
                localize(32021),
                self.routing.build_url("items", "all", "hot/"),
                self.routing.build_icon_path("hot"),
                True,
                self.settings.show_hot,
            ),
            MainMenuItem(
                self.sorting_title,
                self.routing.build_url("items", "all", "sort/"),
                self.routing.build_icon_path("sort"),
                True,
                self.settings.show_sort,
            ),
            MainMenuItem(
                localize(32051),
                self.routing.build_url("tv/"),
                self.routing.build_icon_path("tv"),
                True,
                self.settings.show_tv,
            ),
            MainMenuItem(
                localize(32052),
                self.routing.build_url("collections/"),
                self.routing.build_icon_path("collections"),
                True,
                self.settings.show_collections,
            ),
            MainMenuItem(
                localize(32053),
                self.routing.build_url("items", "movies/"),
                self.routing.build_icon_path("movies"),
                True,
                self.settings.show_movies,
            ),
            MainMenuItem(
                localize(32054),
                self.routing.build_url("items", "serials/"),
                self.routing.build_icon_path("serials"),
                True,
                self.settings.show_serials,
            ),
            MainMenuItem(
                localize(32055),
                self.routing.build_url("items", "tvshow/"),
                self.routing.build_icon_path("tvshows"),
                True,
                self.settings.show_tvshows,
            ),
            MainMenuItem(
                "3D",
                self.routing.build_url("items", "3d/"),
                self.routing.build_icon_path("3d"),
                True,
                self.settings.show_3d,
            ),
            MainMenuItem(
                localize(32056),
                self.routing.build_url("items", "concerts/"),
                self.routing.build_icon_path("concerts"),
                True,
                self.settings.show_concerts,
            ),
            MainMenuItem(
                localize(32057),
                self.routing.build_url("items", "documovies/"),
                self.routing.build_icon_path("documovies"),
                True,
                self.settings.show_documovies,
            ),
            MainMenuItem(
                localize(32058),
                self.routing.build_url("items", "docuserials/"),
                self.routing.build_icon_path("docuserials"),
                True,
                self.settings.show_docuserials,
            ),
        ]

    @property
    def sorting_title(self) -> str:
        sd = self.settings.sorting_direction_title
        sb = self.settings.sort_by_localized
        # By
        return f"{localize(32089)} {sb} {sd}"

    @property
    def sorting_params(self) -> Dict[str, str]:
        return {"sort": f"{self.settings.sort_by}{self.settings.sorting_direction_param}"}

    def clear_window_property(self) -> None:
        xbmcgui.Window(10000).clearProperty("video.kino.pub-playback_data")

    def set_window_property(self, value: Dict) -> None:
        self.clear_window_property()
        pickled = codecs.encode(pickle.dumps(value), "base64").decode("utf-8")
        xbmcgui.Window(10000).setProperty("video.kino.pub-playback_data", pickled)

    def get_window_property(self, item_id: str) -> Union[TVShow, Multi, Movie]:
        try:
            data = xbmcgui.Window(10000).getProperty("video.kino.pub-playback_data").encode("utf-8")
            items = pickle.loads(codecs.decode(data, "base64"))
        except EOFError:
            items = {}
        item = items.get(int(item_id), {})
        if item:
            item._plugin = self
        return item

    @property
    def is_hls_enabled(self) -> bool:
        return (
            "hls" in self.settings.stream_type
            and self.settings.use_inputstream_adaptive == "true"
            and inputstreamhelper
        )
