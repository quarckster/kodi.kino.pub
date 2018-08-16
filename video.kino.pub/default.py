#!/usr/bin/python
from resources.lib import addonworker
from resources.lib.data import __settings__


def main():
    if __settings__.getSetting("reset_auth") == "false":
        __settings__.setSetting("access_token", "")
        __settings__.setSetting("refresh_token", "")
        __settings__.setSetting("access_token_expire", "")
        __settings__.setSetting("reset_auth", "0")
        __settings__.setSetting("device_info_update", "0")
    addonworker.init()


if __name__ == "__main__":
    main()
