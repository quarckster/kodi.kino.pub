# -*- coding: utf-8 -*-
import json
import time

import xbmc
import xbmcgui


class Player(xbmc.Player):
    def __init__(self, list_item):
        self.plugin = list_item.plugin
        self.list_item = list_item
        self.is_playing = True
        self.marktime = 0

    def set_marktime(self):
        if self.isPlaying():
            self.marktime = int(self.getTime())

    @property
    def should_make_resume_point(self):
        # https://kodi.wiki/view/HOW-TO:Modify_automatic_watch_and_resume_points#Settings_explained
        return (
            self.marktime > self.plugin.settings.advanced("video", "ignoresecondsatstart")
            and not self.should_mark_as_watched
        )

    @property
    def should_mark_as_watched(self):
        return 100 * self.marktime / float(
            self.list_item.getProperty("play_duration")
        ) > self.plugin.settings.advanced("video", "playcountminimumpercent")

    @property
    def should_reset_resume_point(self):
        return self.marktime < self.plugin.settings.advanced("video", "ignoresecondsatstart") and (
            float(self.list_item.getProperty("play_resumetime"))
            > self.plugin.settings.advanced("video", "ignoresecondsatstart")
        )

    @property
    def should_refresh_token(self):
        return int(time.time()) + int(self.list_item.getProperty("play_duration")) >= int(
            self.plugin.settings.access_token_expire
        )

    @property
    def _base_data(self):
        item_id = self.list_item.getProperty("item_id")
        video_number = self.list_item.getProperty("video_number")
        season_number = self.list_item.getProperty("season_number")
        if season_number:
            data = {"id": item_id, "season": season_number, "video": video_number}
        else:
            data = {"id": item_id, "video": video_number}
        return data

    def onPlayBackStarted(self):
        self.plugin.logger.notice("playback started")
        # https://github.com/trakt/script.trakt/wiki/Providing-id's-to-facilitate-scrobbling
        # imdb id should be 7 digits with leading zeroes with tt prepended
        imdb_id = "tt{:07d}".format(int(self.list_item.getProperty("imdbnumber")))
        ids = json.dumps({"imdb": imdb_id})
        xbmcgui.Window(10000).setProperty("script.trakt.ids", ids)
        if self.should_refresh_token:
            self.plugin.logger.notice("access token should be refreshed")
            self.plugin.auth.get_token()

    def onPlayBackStopped(self):
        self.is_playing = False
        data = self._base_data
        self.plugin.logger.notice("playback stopped")
        if self.should_make_resume_point:
            data["time"] = self.marktime
            self.plugin.logger.notice("sending resume point")
            self.plugin.client("watching/marktime").get(data=data)
        elif self.should_mark_as_watched and int(self.list_item.getProperty("playcount")) < 1:
            data["status"] = 1
            self.plugin.logger.notice("marking as watched")
            self.plugin.client("watching/toggle").get(data=data)
        elif self.should_reset_resume_point:
            data["time"] = 0
            self.plugin.logger.notice("resetting resume point")
            self.plugin.client("watching/marktime").get(data=data)
        else:
            return

    def onPlayBackEnded(self):
        self.is_playing = False
        self.plugin.logger.notice("playback ended")
        if int(self.list_item.getProperty("playcount")) < 1:
            data = self._base_data
            data["status"] = 1
            self.plugin.logger.notice("marking as watched")
            self.plugin.client("watching/toggle").get(data=data)

    def onPlaybackError(self):
        self.plugin.logger.error("playback error")
        self.is_playing = False
