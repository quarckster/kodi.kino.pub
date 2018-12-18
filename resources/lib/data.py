import xml.etree.ElementTree as ET

import xbmc
import xbmcaddon


__id__ = "video.kino.pub"
__settings__ = xbmcaddon.Addon(id=__id__)
__extended_plot__ = __settings__.getSetting('extended_plot')
__ratings_source__ = __settings__.getSetting('ratings_source')
__plugin__ = "plugin://{}".format(__id__)
advancedsettings_file = xbmc.translatePath("special://home/userdata/advancedsettings.xml")
defaults = {
    ("video", "playcountminimumpercent"): 90,
    ("video", "ignoresecondsatstart"): 180,
    ("video", "ignorepercentatend"): 8
}


def get_adv_setting(*args):
    try:
        root = ET.parse(advancedsettings_file).getroot()
    except (ET.ParseError, IOError):
        return defaults.get(args)
    elem = root.find("./{}".format("/".join(args)))
    return elem.text if elem else defaults.get(args)
