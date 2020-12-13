# -*- coding: utf-8 -*-
import xbmc


def notice(message, heading="", time=4000):
    xbmc.executebuiltin('XBMC.Notification("{}", "{}", "{}")'.format(heading, message, time))
