#!/usr/bin/python
import os, xbmc, xbmcaddon

__addon__ = xbmcaddon.Addon(id='plugin.video.kino.pub')
__settings__ = xbmcaddon.Addon(id='plugin.video.kino.pub')

_ADDON_PATH =   xbmc.translatePath(__addon__.getAddonInfo('path'))
if (sys.platform == 'win32') or (sys.platform == 'win64'):
    _ADDON_PATH = _ADDON_PATH.decode('utf-8')
sys.path.append( os.path.join( _ADDON_PATH, 'resources', 'lib') )


"""
   Authentication
"""
# username = __settings__.getSetting('username')
# password = __settings__.getSetting('password')
# if not (username or password):
#     xbmc.log("Show plugin settings")
#     __addon__.openSettings()

if (__name__ == '__main__' ):
    import addonworker
    xbmc.log("Addonworker init")
    addonworker.init()






