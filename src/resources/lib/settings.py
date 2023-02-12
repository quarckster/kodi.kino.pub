import os
import xml.etree.ElementTree as ET

import xbmcaddon
import xbmcvfs

from resources.lib.utils import localize


class Settings:
    advancedsettings_file = xbmcvfs.translatePath("special://profile/advancedsettings.xml")
    defaults = {
        ("video", "playcountminimumpercent"): 90,
        ("video", "ignoresecondsatstart"): 180,
        ("video", "ignorepercentatend"): 8,
    }

    is_testing = bool(os.getenv("KINO_PUB_TEST"))
    sorting_direction_title_map = {"asc": localize(32068), "desc": localize(32067)}
    sorting_direction_param_map = {"asc": "", "desc": "-"}
    sort_by_map = {
        "updated": localize(32059),
        "created": localize(32060),
        "year": localize(32061),
        "title": localize(32062),
        "rating": localize(32063),
        "kinopoisk_rating": localize(32064),
        "imdb_rating": "IMDB",
        "views": localize(32065),
        "watchers": localize(32066),
    }

    def __getattr__(self, name):
        if name == "advanced":
            return self._get_adv_setting
        if name.startswith("show_"):
            return eval(xbmcaddon.Addon().getSetting(name).title())
        return xbmcaddon.Addon().getSetting(name)

    def __setattr__(self, name: str, value: str) -> None:
        if value is not None:
            value = str(value)
        xbmcaddon.Addon().setSetting(name, value)

    def _get_adv_setting(self, *args):
        try:
            root = ET.parse(self.advancedsettings_file).getroot()
        except (ET.ParseError, OSError):
            return self.defaults.get(args)
        elem = root.find("./{}".format("/".join(args)))
        return elem.text if elem else self.defaults.get(args)

    @property
    def sorting_direction_title(self) -> str:
        return self.sorting_direction_title_map[self.sort_direction]

    @property
    def sorting_direction_param(self) -> str:
        return self.sorting_direction_param_map[self.sort_direction]

    @property
    def sort_by_localized(self) -> str:
        return self.sort_by_map[self.sort_by]

    @property
    def api_url(self) -> str:
        return "http://localhost:1080/v1" if self.is_testing else "https://api.service-kp.com/v1"

    @property
    def oauth_api_url(self) -> str:
        if self.is_testing:
            return "http://localhost:1080/v1/oauth2/device"
        return "https://api.service-kp.com/oauth2/device"
