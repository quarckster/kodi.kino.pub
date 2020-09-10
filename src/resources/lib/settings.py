from __future__ import absolute_import

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
            value = self._get_adv_setting
        else:
            value = xbmcaddon.Addon().getSetting(name)
        return self._parse(value)

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

    def _parse(self, value):
        if value in ["true", "True"]:
            return True
        elif value in ["false", "False"]:
            return False
        else:
            try:
                return int(value)
            except (TypeError, ValueError):
                return value
