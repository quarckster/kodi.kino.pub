#!/usr/bin/python
import xbmcaddon
from resources.lib import addonworker
from resources.lib.data import __id__


def main():
    if xbmcaddon.Addon(id=__id__).getSetting("reset_auth") == "true":
        xbmcaddon.Addon(id=__id__).setSetting("access_token", "")
        xbmcaddon.Addon(id=__id__).setSetting("refresh_token", "")
        xbmcaddon.Addon(id=__id__).setSetting("access_token_expire", "")
        xbmcaddon.Addon(id=__id__).setSetting("reset_auth", "0")
        xbmcaddon.Addon(id=__id__).setSetting("device_info_update", "0")
    addonworker.init()


if __name__ == "__main__":
    main()
