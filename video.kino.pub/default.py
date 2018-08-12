#!/usr/bin/python
import xbmcaddon
from resources.lib import addonworker


__id__ = "video.kino.pub"
__settings__ = xbmcaddon.Addon(id=__id__)


def main():
    reset_auth = bool(int(__settings__.getSetting("reset_auth")))
    if reset_auth:
        __settings__.setSetting("access_token", "")
        __settings__.setSetting("refresh_token", "")
        __settings__.setSetting("access_token_expire", "")
        __settings__.setSetting("reset_auth", "0")
        __settings__.setSetting("device_info_update", "0")
    addonworker.init()


if __name__ == "__main__":
    main()
