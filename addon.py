#!/usr/bin/python
import xbmcaddon

from resources.lib import addonworker


def main():
    if xbmcaddon.Addon().getSetting("reset_auth") == "true":
        xbmcaddon.Addon().setSetting("access_token", "")
        xbmcaddon.Addon().setSetting("refresh_token", "")
        xbmcaddon.Addon().setSetting("access_token_expire", "")
        xbmcaddon.Addon().setSetting("reset_auth", "0")
        xbmcaddon.Addon().setSetting("device_info_update", "0")
    addonworker.init()


if __name__ == "__main__":
    main()
