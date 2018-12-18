import xml.etree.ElementTree as ET

import xbmc
import xbmcaddon
import xbmcvfs
import json
import errno


__id__ = "video.kino.pub"
# use addon object only for read/update addon settings
__addon__ = xbmcaddon.Addon(id=__id__)
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


class Device(object):
    ADDON_DIRECTORY = __addon__.getAddonInfo('profile')
    DEVICE_FILE = xbmc.translatePath("{}device.json".format(ADDON_DIRECTORY))
    DEVICE_KEYS = ["verification_uri", "code", "access_token", "interval", "expires_in",
                   "device_info_update", "access_token_expire", "user_code", "refresh_token"]

    def __init__(self):
        # migrate existing saved settings
        if not xbmcvfs.exists(self.DEVICE_FILE):
            try:
                xbmcvfs.mkdirs(self.ADDON_DIRECTORY)
            except OSError as exc:  # Guard against raise condition
                if exc.errno != errno.EEXIST:
                    heading = __addon__.getAddonInfo('name')
                    icon = __addon__.getAddonInfo('icon')
                    time = 4000
                    xbmc.executebuiltin(
                        'Notification(%s, %s, %d, %s)' % (heading, exc.strerror, time, icon)
                        )
            self.info = {key: __addon__.getSetting(key) for key in self.DEVICE_KEYS}

    @property
    def info(self):
        with open(self.DEVICE_FILE, 'r') as f:
            return json.load(f)

    @info.setter
    def info(self, device_dict):
        with open(self.DEVICE_FILE, 'w+') as f:
            f.write(json.dumps(device_dict))

    def get(self, key):
        return self.info.get(key)

    def update(self, **kwargs):
        device_info = self.info
        for key, value in kwargs.items():
            device_info[key] = None if value is None else str(value).encode('utf-8')
        self.info = device_info

    def reset(self):
        self.info = {key: None for key in self.DEVICE_KEYS}


# use device object to read/update device auth data
__device__ = Device()
