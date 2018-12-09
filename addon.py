#!/usr/bin/python
from resources.lib import addonworker
from resources.lib.data import __addon__, __device__


def main():
    if __addon__.getSetting("reset_auth") == "true":
        # reset all device auth data
        __device__.reset()
        __addon__.setSetting("reset_auth", "false")
    addonworker.init()


if __name__ == "__main__":
    main()
