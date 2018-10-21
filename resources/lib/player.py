# -*- coding: utf-8 -*-
import xbmc
from client import KinoPubClient


class Player(xbmc.Player):

    def __init__(self, id=None, video_number=None, season_number=None):
        self.video_id = id
        self.video_number = video_number
        self.season_number = season_number
        self.is_playing = True
        self.marktime = 0
        super(Player, self).__init__()

    def set_marktime(self):
        if self.isPlaying():
            self.marktime = int(self.getTime())

    def onPlayBackStopped(self):
        KinoPubClient("watching/marktime").get(data={
            "id": self.video_id,
            "video": self.video_number,
            "time": self.marktime,
            "season": self.season_number
        })
        xbmc.executebuiltin("Container.Refresh")
        self.is_playing = False

    def onPlayBackEnded(self):
        KinoPubClient("watching/toggle").get(data={
            "id": self.video_id,
            "video": self.video_number,
            "season": self.season_number,
            "status": 1
        })
        xbmc.executebuiltin("Container.Refresh")
        self.is_playing = False

    def onPlaybackError(self):
        self.is_playing = False
