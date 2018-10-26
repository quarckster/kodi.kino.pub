import xml.etree.ElementTree as ET

import xbmc
import xbmcaddon
import xbmcvfs


__id__ = "video.kino.pub"
__settings__ = xbmcaddon.Addon(id=__id__)
__plugin__ = "plugin://{}".format(__id__)
advancedsettings_file = xbmc.translatePath("special://home/userdata/advancedsettings.xml")
defaults = {
    ("video", "playcountminimumpercent"): 90,
    ("video", "ignoresecondsatstart"): 180,
    ("video", "ignorepercentatend"): 8
}


def get_adv_setting(*args):
    if xbmcvfs.exists(advancedsettings_file):
        root = ET.parse(advancedsettings_file).getroot()
        elem = root.find("./{}".format("/".join(args)))
        return elem.text if elem else defaults.get(args)
    else:
        return defaults.get(args)
