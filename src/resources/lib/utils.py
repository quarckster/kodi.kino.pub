import xbmc


def notice(message, heading="", time=4000):
    xbmc.executebuiltin(f'XBMC.Notification("{heading}", "{message}", "{time}")')
