# -*- coding: utf-8 -*-
import xbmc

from client import KinoPubClient
from data import get_adv_setting


class Player(xbmc.Player):

    def __new__(cls, *args, **kwargs):
        return super(Player, cls).__new__(cls)

    def __init__(self, list_item):
        self.list_item = list_item
        self.is_playing = True
        self.marktime = 0
        super(Player, self).__init__()

    def set_marktime(self):
        if self.isPlaying():
            self.marktime = int(self.getTime())

    @property
    def ignore_marktime(self):
        # https://kodi.wiki/view/HOW-TO:Modify_automatic_watch_and_resume_points#Settings_explained
        return (
            self.marktime <= get_adv_setting("video", "ignoresecondsatstart") or
            (100 * self.marktime / float(self.list_item.getduration()) >=
                100 - get_adv_setting("video", "ignorepercentatend"))
        )

    def onPlayBackStopped(self):
        if not self.ignore_marktime:
            video_number = self.list_item.getVideoInfoTag().getEpisode()
            video_number = 1 if video_number == -1 else video_number
            season_number = self.list_item.getVideoInfoTag().getSeason()
            season_number = None if season_number == -1 else season_number
            KinoPubClient("watching/marktime").get(data={
                "id": self.list_item.getProperty("id"),
                "video": video_number,
                "time": self.marktime,
                "season": season_number
            })
            xbmc.executebuiltin("Container.Refresh")
        self.is_playing = False

    def onPlayBackEnded(self):
        if self.list_item.getVideoInfoTag().getPlayCount() < 1:
            video_number = self.list_item.getVideoInfoTag().getEpisode()
            video_number = 1 if video_number == -1 else video_number
            season_number = self.list_item.getVideoInfoTag().getSeason()
            season_number = None if season_number == -1 else season_number
            KinoPubClient("watching/toggle").get(data={
                "id": self.list_item.getProperty("id"),
                "video": video_number,
                "season": season_number,
                "status": 1
            })
            xbmc.executebuiltin("Container.Refresh")
        self.is_playing = False

    def onPlaybackError(self):
        self.is_playing = False
