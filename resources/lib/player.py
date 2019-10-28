# -*- coding: utf-8 -*-
import json
import time

import logger
import xbmc
import xbmcgui
from authwindow import auth
from client import KinoPubClient
from settings import settings


class Player(xbmc.Player):
    def __init__(self, list_item=None):
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
            self.marktime > settings.advanced("video", "ignoresecondsatstart")
            and not self.should_mark_as_watched
        )

    @property
    def should_mark_as_watched(self):
        return 100 * self.marktime / float(
            self.list_item.getProperty("play_duration")
        ) > settings.advanced("video", "playcountminimumpercent")

    @property
    def should_reset_resume_point(self):
        return self.marktime < settings.advanced("video", "ignoresecondsatstart") and (
            float(self.list_item.getProperty("play_resumetime"))
            > settings.advanced("video", "ignoresecondsatstart")
        )

    @property
    def should_refresh_token(self):
        return int(time.time()) + int(self.list_item.getProperty("play_duration")) >= int(
            auth.access_token_expire
        )

    @property
    def _base_data(self):
        id = self.list_item.getProperty("id")
        video_number = self.list_item.getProperty("video_number")
        season_number = self.list_item.getProperty("season_number")
        if season_number:
            data = {"id": id, "season": season_number, "video": video_number}
        else:
            data = {"id": id, "video": video_number}
        return data

    def onPlayBackStarted(self):
        logger.notice("playback started")
        # https://github.com/trakt/script.trakt/wiki/Providing-id's-to-facilitate-scrobbling
        # imdb id should be 7 digits with leading zeroes with tt prepended
        imdb_id = "tt{:07d}".format(int(self.list_item.getProperty("imdbnumber")))
        ids = json.dumps({u"imdb": imdb_id})
        xbmcgui.Window(10000).setProperty("script.trakt.ids", ids)
        if self.should_refresh_token:
            logger.notice("access token should be refreshed")
            status, __ = auth.get_token(refresh=True)
            if status != auth.SUCCESS:
                auth.reauth()

    def onPlayBackStopped(self):
        self.is_playing = False
        data = self._base_data
        logger.notice("playback stopped")
        if self.should_make_resume_point:
            data["time"] = self.marktime
            logger.notice("sending resume point")
            KinoPubClient("watching/marktime").get(data=data)
        elif self.should_mark_as_watched and int(self.list_item.getProperty("playcount")) < 1:
            data["status"] = 1
            logger.notice("marking as watched")
            KinoPubClient("watching/toggle").get(data=data)
        elif self.should_reset_resume_point:
            data["time"] = 0
            logger.notice("resetting resume point")
            KinoPubClient("watching/marktime").get(data=data)
        else:
            return

    def onPlayBackEnded(self):
        self.is_playing = False
        logger.notice("playback ended")
        if int(self.list_item.getProperty("playcount")) < 1:
            data = self._base_data
            data["status"] = 1
            logger.notice("marking as watched")
            KinoPubClient("watching/toggle").get(data=data)

    def onPlaybackError(self):
        logger.error("playback error")
        self.is_playing = False
