import xbmcgui


def notice(message, heading="", time=4000):
    xbmcgui.Dialog().notification(heading, message, time=time)
