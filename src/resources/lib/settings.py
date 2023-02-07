import os
import xml.etree.ElementTree as ET

import xbmcaddon
import xbmcvfs


class Settings:
    advancedsettings_file = xbmcvfs.translatePath("special://profile/advancedsettings.xml")
    defaults = {
        ("video", "playcountminimumpercent"): 90,
        ("video", "ignoresecondsatstart"): 180,
        ("video", "ignorepercentatend"): 8,
    }

    _locs = {
        "Россия": "ru",
        "Нидерланды": "nl",
    }

    is_testing = bool(os.getenv("KINO_PUB_TEST"))

    def __getattr__(self, name):
        if name == "advanced":
            return self._get_adv_setting
        if name.startswith("show_"):
            return eval(xbmcaddon.Addon().getSetting(name).title())
        if name == "loc":
            return self._locs[xbmcaddon.Addon().getSetting(name)]
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
    def api_url(self) -> str:
        return "http://localhost:1080/v1" if self.is_testing else "https://api.service-kp.com/v1"

    @property
    def oauth_api_url(self) -> str:
        if self.is_testing:
            return "http://localhost:1080/v1/oauth2/device"
        return "https://api.service-kp.com/oauth2/device"
