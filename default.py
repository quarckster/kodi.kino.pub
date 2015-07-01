#!/usr/bin/python
# -*- coding: utf-8 -*-
import os, xbmc, xbmcaddon
import time
__id__ = 'plugin.video.kino.pub'
__addon__ = xbmcaddon.Addon(id=__id__)
__settings__ = xbmcaddon.Addon(id=__id__)
__skinsdir__ = "DefaultSkin"

_ADDON_PATH =   xbmc.translatePath(__addon__.getAddonInfo('path'))
if (sys.platform == 'win32') or (sys.platform == 'win64'):
    _ADDON_PATH = _ADDON_PATH.decode('utf-8')
sys.path.append( os.path.join( _ADDON_PATH, 'resources', 'lib') )
sys.path.append( os.path.join( _ADDON_PATH, 'resources', 'skins') )
sys.path.append( os.path.join( _ADDON_PATH, 'resources', 'skins', 'DefaultSkin') )

# username = __settings__.getSetting('username')
# password = __settings__.getSetting('password')
# if not (username or password):
#     xbmc.log("Show plugin settings")
#     __addon__.openSettings()

if (__name__ == '__main__' ):
    """
       Authentication
    """
    import authwindow as auth

    au = auth.Auth(__settings__)
    #au.reauth()
    access_token = __settings__.getSetting('access_token')
    device_code = __settings__.getSetting('device_code')

    xbmc.log("Access token is '%s'" % access_token)
    xbmc.log("Device code is '%s'" % device_code)
    access_token_expire = __settings__.getSetting('access_token_expire')
    if device_code or (not device_code and not access_token):
        wn = auth.AuthWindow("auth.xml", _ADDON_PATH, __skinsdir__, settings=__settings__)
        wn.doModal()
        xbmc.log("RERTURN FROM DOMODAL")
        del wn

    access_token = __settings__.getSetting('access_token')
    device_code = __settings__.getSetting('device_code')        
    xbmc.log("AfterModal: Access token is '%s'" % access_token)
    xbmc.log("AfterModal: Device code is '%s'" % device_code)
    if access_token and not device_code:
        # Check if our token need refresh
        access_token_expire = __settings__.getSetting('access_token_expire')
        xbmc.log("Access token expires = %s" % access_token_expire)
        xbmc.log("Access token expires in %s" % (int(float(access_token_expire)) - int(time.time())))
        if access_token_expire and int(float(access_token_expire)) - int(time.time()) <= 3600:
            # refresh access token here
            xbmc.log('We need to refresh token')
            au.get_token(refresh=True)
        import addonworker
        xbmc.log("Addonworker init")
        addonworker.init()






