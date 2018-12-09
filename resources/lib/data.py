import xml.etree.ElementTree as ET

import xbmc
import xbmcaddon
import xbmcvfs
import json


__id__ = "video.kino.pub"
__plugin__ = "plugin://{}".format(__id__)
__addon__ = xbmcaddon.Addon(id=__id__)
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


class Device(object):
    DEVICE_FILE = xbmc.translatePath("{}/device.json".format(__addon__.getAddonInfo('profile')))
    DEVICE_KEYS = ["device_code", "verification_uri", "access_token", "interval",
                   "expires_in", "access_token_expire", "refresh_token"]

    def __init__(self):
        # migrate existing saved settings
        if not xbmcvfs.exists(self.DEVICE_FILE):
            self.info = {key: __addon__.getSetting(key) for key in self.DEVICE_KEYS}

    @property
    def info(self):
        with open(self.DEVICE_FILE, 'r') as f:
            return json.load(f)

    @info.setter
    def info(self, new_attrs):
        with open(self.DEVICE_FILE, 'w') as f:
            f.write(json.dumps(new_attrs))

    def get(self, key):
        return self.info.get(key)

    # def update(self, key, value):
    #     current_info = self.info
    #     current_info[key] = value
    #     self.info = current_info
    
    def update(self, **kwargs):
        current_info = self.info
        for key, value in kwargs.items():
            current_info[key] = str(value).encode('utf-8')
        self.info = current_info

    def reset(self):
        current_info = self.info
        for key in current_info:
            current_info[key] = None
        self.info = current_info


__device__ = Device()
