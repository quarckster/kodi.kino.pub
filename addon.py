#!/usr/bin/python
from resources.lib import addonworker
from resources.lib.settings import settings


def main():
    if settings.reset_auth == "true":
        settings.access_token = ""
        settings.refresh_token = ""
        settings.access_token_expire = ""
        settings.reset_auth = "0"
        settings.device_info_update = "0"
    addonworker.init()


if __name__ == "__main__":
    main()
