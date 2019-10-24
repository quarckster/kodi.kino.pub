# -*- coding: utf-8 -*-
import json
import time

import xbmc
import xbmcgui
from authwindow import auth
from client import KinoPubClient
from data import __plugin__
from data import get_adv_setting


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
            self.marktime > get_adv_setting("video", "ignoresecondsatstart")
            and not self.should_mark_as_watched
        )

    @property
    def should_mark_as_watched(self):
        return 100 * self.marktime / float(
            self.list_item.getProperty("play_duration")
        ) > get_adv_setting("video", "playcountminimumpercent")

    @property
    def should_reset_resume_point(self):
        return self.marktime < get_adv_setting("video", "ignoresecondsatstart") and (
            float(self.list_item.getProperty("play_resumetime"))
            > get_adv_setting("video", "ignoresecondsatstart")
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
        xbmc.log("{}: playback started".format(__plugin__), level=xbmc.LOGNOTICE)
        # https://github.com/trakt/script.trakt/wiki/Providing-id's-to-facilitate-scrobbling
        # imdb id should be 7 digits with leading zeroes with tt prepended
        imdb_id = "tt{:07d}".format(int(self.list_item.getProperty("imdbnumber")))
        ids = json.dumps({u"imdb": imdb_id})
        xbmcgui.Window(10000).setProperty("script.trakt.ids", ids)
        if self.should_refresh_token:
            xbmc.log(
                "{}: access token should be refreshed".format(__plugin__), level=xbmc.LOGNOTICE
            )
            status, __ = auth.get_token(refresh=True)
            if status != auth.SUCCESS:
                auth.reauth()

    def onPlayBackStopped(self):
        self.is_playing = False
        data = self._base_data
        xbmc.log("{}: playback stopped".format(__plugin__), level=xbmc.LOGNOTICE)
        if self.should_make_resume_point:
            data["time"] = self.marktime
            xbmc.log("{}: sending resume point".format(__plugin__), level=xbmc.LOGNOTICE)
            KinoPubClient("watching/marktime").get(data=data)
        elif self.should_mark_as_watched and int(self.list_item.getProperty("playcount")) < 1:
            data["status"] = 1
            xbmc.log("{}: marking as watched".format(__plugin__), level=xbmc.LOGNOTICE)
            KinoPubClient("watching/toggle").get(data=data)
        elif self.should_reset_resume_point:
            data["time"] = 0
            xbmc.log("{}: resetting resume point".format(__plugin__), level=xbmc.LOGNOTICE)
            KinoPubClient("watching/marktime").get(data=data)
        else:
            return

    def onPlayBackEnded(self):
        self.is_playing = False
        xbmc.log("{}: playback ended".format(__plugin__), level=xbmc.LOGNOTICE)
        if int(self.list_item.getProperty("playcount")) < 1:
            data = self._base_data
            data["status"] = 1
            xbmc.log("{}: marking as watched".format(__plugin__), level=xbmc.LOGNOTICE)
            KinoPubClient("watching/toggle").get(data=data)

    def onPlaybackError(self):
        xbmc.log("{}: Playback error".format(__plugin__), level=xbmc.LOGNOTICE)
        self.is_playing = False
