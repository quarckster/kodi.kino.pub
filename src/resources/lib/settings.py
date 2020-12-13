import xml.etree.ElementTree as ET

import xbmc
import xbmcaddon


class Settings(object):
    advancedsettings_file = xbmc.translatePath("special://home/userdata/advancedsettings.xml")
    defaults = {
        ("video", "playcountminimumpercent"): 90,
        ("video", "ignoresecondsatstart"): 180,
        ("video", "ignorepercentatend"): 8,
    }

    def __getattr__(self, name):
        if name == "advanced":
            return self._get_adv_setting
        if name.startswith("show_"):
            return eval(xbmcaddon.Addon().getSetting(name).title())
        return xbmcaddon.Addon().getSetting(name)

    def __setattr__(self, name, value):
        if value is not None:
            value = str(value)
        xbmcaddon.Addon().setSetting(name, value)

    def _get_adv_setting(self, *args):
        try:
            root = ET.parse(self.advancedsettings_file).getroot()
        except (ET.ParseError, IOError):
            return self.defaults.get(args)
        elem = root.find("./{}".format("/".join(args)))
        return elem.text if elem else self.defaults.get(args)
