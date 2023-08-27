import json
import time
from typing import Dict
from typing import Union

import xbmc
import xbmcgui

from resources.lib import proxy
from resources.lib.listitem import ExtendedListItem


class Player(xbmc.Player):
    def __init__(self, list_item: ExtendedListItem) -> None:
        self.plugin = list_item.plugin
        self.list_item = list_item
        self.is_playing = True
        self.marktime = 0

    def set_marktime(self) -> None:
        if self.isPlaying():
            self.marktime = int(self.getTime())

    @property
    def should_make_resume_point(self) -> bool:
        # https://kodi.wiki/view/HOW-TO:Modify_automatic_watch_and_resume_points#Settings_explained
        return (
            self.marktime > self.plugin.settings.advanced("video", "ignoresecondsatstart")
            and not self.should_mark_as_watched
        )

    @property
    def should_mark_as_watched(self) -> bool:
        return 100 * self.marktime / float(
            self.list_item.getProperty("play_duration")
        ) > self.plugin.settings.advanced("video", "playcountminimumpercent")

    @property
    def should_reset_resume_point(self) -> bool:
        return self.marktime < self.plugin.settings.advanced("video", "ignoresecondsatstart") and (
            float(self.list_item.getProperty("play_resumetime"))
            > self.plugin.settings.advanced("video", "ignoresecondsatstart")
        )

    @property
    def should_refresh_token(self) -> bool:
        return int(time.time()) + int(self.list_item.getProperty("play_duration")) >= int(
            self.plugin.settings.access_token_expire
        )

    @property
    def _base_data(self) -> Dict[str, Union[str, int]]:
        item_id = self.list_item.getProperty("item_id")
        video_number = self.list_item.getProperty("video_number")
        season_number = self.list_item.getProperty("season_number")
        if season_number:
            data = {"id": item_id, "season": season_number, "video": video_number}
        else:
            data = {"id": item_id, "video": video_number}
        return data

    def onPlayBackStarted(self) -> None:
        proxy.stop(self.plugin)
        self.plugin.logger.debug("Playback started")
        self.plugin.clear_window_property()
        if self.should_refresh_token:
            self.plugin.logger.debug("Access token should be refreshed")
            self.plugin.auth.get_token()
        # https://github.com/trakt/script.trakt/wiki/Providing-id's-to-facilitate-scrobbling
        # imdb id should be 7 digits with leading zeroes with tt prepended
        try:
            imdb_id = f"tt{int(self.list_item.getProperty('imdbnumber')):07d}"
        except ValueError:
            self.plugin.logger.debug("IMDB number is missing, skip scrobbling")
            return
        ids = json.dumps({"imdb": imdb_id})
        xbmcgui.Window(10000).setProperty("script.trakt.ids", ids)

    def onPlayBackStopped(self) -> None:
        self.is_playing = False
        data = self._base_data
        self.plugin.logger.debug("Playback stopped")
        if self.should_make_resume_point:
            data["time"] = self.marktime
            self.plugin.logger.debug("Sending resume point")
            self.plugin.client("watching/marktime").get(data=data)
        elif self.should_mark_as_watched and int(self.list_item.getProperty("playcount")) < 1:
            data["status"] = 1
            self.plugin.logger.debug("Marking as watched")
            self.plugin.client("watching/toggle").get(data=data)
        elif self.should_reset_resume_point:
            data["time"] = 0
            self.plugin.logger.debug("Resetting resume point")
            self.plugin.client("watching/marktime").get(data=data)
        else:
            return

    def onPlayBackEnded(self) -> None:
        self.is_playing = False
        self.plugin.logger.debug("Playback ended")
        if int(self.list_item.getProperty("playcount")) < 1:
            data = self._base_data
            data["status"] = 1
            self.plugin.logger.debug("Marking as watched")
            self.plugin.client("watching/toggle").get(data=data)

    def onPlaybackError(self) -> None:
        self.plugin.logger.error("Playback error")
        self.is_playing = False
