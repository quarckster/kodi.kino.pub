#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmcgui, xbmcaddon, xbmc
import thread
import threading
import urllib2
import urllib
import json
import time

OAUTH_API_URL = "http://dev.kino.pub/oauth2/device"
CLIENT_ID = "xbmc"
CLIENT_SECRET = "cgg3gtifu46urtfp2zp1nqtba0k2ezxh"

class Auth(object):
    terminated = False
    timer = 0
    ERROR, PENDING_STATUS, SUCCESS, EXPIRED = range(4)

    def __init__(self, settings, window=None):
        self.window = window
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.settings = settings

    def close(self):
        if self.window is not None:
            self.window.close()

    def get_access_token(self):
        return self.settings.getSetting('access_token')

    def set_access_token(self, value):
        if value is not None:
            value = value.encode('utf-8')
        self.settings.setSetting('access_token', value)

    def get_refresh_token(self):
        return self.settings.getSetting('refresh_token')

    def set_refresh_token(self, value):
        if value is not None:
            value = value.encode('utf-8')
        self.settings.setSetting('refresh_token', value)


    access_token = property(get_access_token, set_access_token)
    refresh_token = property(get_refresh_token, set_refresh_token)

    def reauth(self):
        self.access_token = ""
        self.device_token = ""

    def request(self, url, data):
        try:
            udata = urllib.urlencode(data)
            xbmc.log(udata)
            req = urllib2.Request(url)

            resp = urllib2.urlopen(req, udata).read()
            xbmc.log("Response: %s" % resp)
            return json.loads(resp)
        except urllib2.URLError, e:
            if e.code == 400:
                _data = e.read()
                xbmc.log(_data)
                try:
                    resp = json.loads(_data)
                    return resp
                except:
                    pass
        xbmc.executebuiltin("XBMC.Notification(%s,%s)" % ("Internet problems", "Connection timed out!"))
        if self.window:
            self.window.close()

    def get_device_code(self, url=OAUTH_API_URL):
        xbmc.log('Get device code %s - %s' % (self.client_id, self.client_secret))
        data = {
            'grant_type': 'device_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }
        resp = self.request(url, data)
        error = resp.get('error')
        if error:
            #xbmc.executebuiltin("XBMC.Notification(%s,%s)" % ("Unknown device", "Unknown device. Please visit http://kino.pub/device/support for more details."))
            return self.ERROR, resp
        self.device_code = resp['code'].encode('utf-8')
        self.user_code = resp['user_code'].encode('utf-8')
        self.verification_uri = resp['verification_uri'].encode('utf8')
        self.refresh_interval = int(resp['interval'])

        self.settings.setSetting('device_code', str(self.device_code).encode('utf-8'))
        self.settings.setSetting('verification_uri', str(self.verification_uri).encode('utf-8'))
        self.settings.setSetting('interval', str(self.refresh_interval))
        return self.SUCCESS, resp

    def get_token(self, url=OAUTH_API_URL, refresh=False):
        xbmc.log('Get token')
        if refresh:
            xbmc.log('Get token: refresh')
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
            }
        else:
            xbmc.log('Get token: device_token')
            data = {
                'grant_type': 'device_token',
                'client_id': self.client_id,
                'code': self.device_code,
                'client_secret': self.client_secret,
            }
        resp = self.request(url, data)
        error = resp.get('error')
        if error and error == "authorization_pending":
            return self.PENDING_STATUS, resp
        if error and error in ["invalid_grant", "code_expired", "invalid_client"]:
            return self.EXPIRED, resp

        expires_in = int(resp.get('expires_in')) + int(time.time())
        self.access_token = resp.get('access_token')
        self.settings.setSetting('access_token_expire', str(expires_in))

        if self.access_token:
            for key, val in resp.items():
                self.settings.setSetting(key.encode('utf-8'), str(val).encode('utf-8'))
            self.settings.setSetting('device_code', None)
            return self.SUCCESS, resp
        return self.ERROR

    def verify_device_code(self, interval, parent):
        while not parent.stopped.wait(interval):
            success, resp = self.get_token()
            if success == self.SUCCESS:
                parent.closeWindow()
                return True


class AuthWindow(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.stopped = threading.Event()
        self.auth = Auth(kwargs['settings'], window=self)

    def onInit(self):
        status, resp = self.auth.get_device_code()
        if status == self.auth.ERROR:
            label = self.getControl(9111)
            label.setLabel('Устройство не поддерживается.\nПосетите http://kino.pub/device/support для уточнения деталей.')
            return
        label = self.getControl(9112)
        label.setLabel(resp['verification_uri'].encode('utf-8'))
        label = self.getControl(9113)
        label.setLabel(resp['user_code'].encode('utf-8'))
        t = threading.Thread(target=self.auth.verify_device_code, args=[int(resp['interval']), self])
        t.daemon = True
        t.start()


    def onAction(self, action):
        buttonCode =  action.getButtonCode()
        actionID   =  action.getId()
        if (actionID in [9, 10, 13, 14, 15]):
            self.closeWindow()

    def closeWindow(self):
        self.stopped.set()
        for thread in threading.enumerate():
            if (thread.isAlive() and thread != threading.currentThread()):
                thread.join(1)
        self.close()
