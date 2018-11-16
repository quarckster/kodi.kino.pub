# -*- coding: utf-8 -*-
import xbmc

from client import KinoPubClient
from data import get_adv_setting


class Player(xbmc.Player):

    def __init__(self, list_item=None):
        super(Player, self).__init__()
        self.list_item = list_item
        self.is_playing = True
        self.marktime = 0

    def set_marktime(self):
        if self.isPlaying():
            self.marktime = int(self.getTime())

    @property
    def should_make_resume_point(self):
        # https://kodi.wiki/view/HOW-TO:Modify_automatic_watch_and_resume_points#Settings_explained
        return (self.marktime > get_adv_setting("video", "ignoresecondsatstart") and
                not self.should_mark_as_watched)

    @property
    def should_mark_as_watched(self):
        return (100 * self.marktime / float(self.list_item.getProperty("play_duration")) >
                get_adv_setting("video", "playcountminimumpercent"))

    @property
    def should_reset_resume_point(self):
        return (
            self.marktime < get_adv_setting("video", "ignoresecondsatstart") and
            (float(self.list_item.getProperty("play_resumetime")) >
                get_adv_setting("video", "ignoresecondsatstart"))
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

    def onPlayBackStopped(self):
        self.is_playing = False
        data = self._base_data
        if self.should_make_resume_point:
            data["time"] = self.marktime
            KinoPubClient("watching/marktime").get(data=data)
        elif self.should_mark_as_watched and int(self.list_item.getProperty("playcount")) < 1:
            data["status"] = 1
            KinoPubClient("watching/toggle").get(data=data)
        elif self.should_reset_resume_point:
            data["time"] = 0
            KinoPubClient("watching/marktime").get(data=data)
        else:
            return

    def onPlayBackEnded(self):
        self.is_playing = False
        if int(self.list_item.getProperty("playcount")) < 1:
            data = self._base_data
            data["status"] = 1
            KinoPubClient("watching/toggle").get(data=data)

    def onPlaybackError(self):
        self.is_playing = False
