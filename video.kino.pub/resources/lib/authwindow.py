# -*- coding: utf-8 -*-

import json
import time
import threading
import xbmc
import xbmcgui
import urllib
import urllib2


class Auth(object):
    terminated = False
    timer = 0
    CLIENT_ID = "xbmc"
    CLIENT_SECRET = "cgg3gtifu46urtfp2zp1nqtba0k2ezxh"
    OAUTH_API_URL = "http://api.service-kp.com/oauth2/device"
    ERROR, PENDING_STATUS, SUCCESS, EXPIRED = range(4)

    def __init__(self, settings, window=None, afterAuth=None):
        self.window = window
        self.settings = settings
        self.afterAuth = afterAuth

    def close(self):
        if self.window is not None:
            self.window.close()

    @property
    def is_token_valid(self):
        return self.access_token_expire > int(time.time())

    @property
    def access_token(self):
        return self.settings.getSetting("access_token")

    @access_token.setter
    def access_token(self, value):
        if value is not None:
            value = value.encode("utf-8")
        self.settings.setSetting("access_token", value)

    @property
    def access_token_expire(self):
        return int(self.settings.getSetting("access_token_expire"))

    @access_token_expire.setter
    def access_token_expire(self, value):
        if value is not None:
            value = value.encode("utf-8")
        self.settings.setSetting("access_token_expire", value)

    @property
    def refresh_token(self):
        return self.settings.getSetting("refresh_token")

    @refresh_token.setter
    def refresh_token(self, value):
        if value is not None:
            value = value.encode("utf-8")
        self.settings.setSetting("refresh_token", value)

    def reauth(self):
        self.access_token = ""
        self.device_token = ""

    def request(self, url, data):
        xbmc.log("REQUEST URL={}".format(url))
        xbmc.log("DATA {}".format(data))
        try:
            udata = urllib.urlencode(data)
            req = urllib2.Request(url)

            resp = urllib2.urlopen(req, udata).read()
            return json.loads(resp)
        except urllib2.URLError, e:
            if e.code == 400:
                _data = e.read()
                try:
                    resp = json.loads(_data)
                    return resp
                except Exception:
                    pass
            return {"status": e.code, "error": "unknown error"}
        xbmc.executebuiltin("XBMC.Notification(Internet problems,Connection timed out!)")
        if self.window:
            self.window.close()

    def get_device_code(self):
        data = {
            "grant_type": "device_code",
            "client_id": self.CLIENT_ID,
            "client_secret": self.CLIENT_SECRET
        }
        resp = self.request(self.OAUTH_API_URL, data)
        error = resp.get("error")
        if error:
            return self.ERROR, resp
        self.device_code = resp["code"].encode("utf-8")
        self.user_code = resp["user_code"].encode("utf-8")
        self.verification_uri = resp["verification_uri"].encode("utf8")
        self.refresh_interval = int(resp["interval"])

        self.settings.setSetting("device_code", str(self.device_code).encode("utf-8"))
        self.settings.setSetting("verification_uri", str(self.verification_uri).encode("utf-8"))
        self.settings.setSetting("interval", str(self.refresh_interval))
        return self.SUCCESS, resp

    def get_token(self, refresh=False):
        if refresh:
            data = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.CLIENT_ID,
                "client_secret": self.CLIENT_SECRET
            }
        else:
            data = {
                "grant_type": "device_token",
                "client_id": self.CLIENT_ID,
                "code": self.device_code,
                "client_secret": self.CLIENT_SECRET
            }
        resp = self.request(self.OAUTH_API_URL, data)

        error = resp.get("error")
        if error and error == "authorization_pending":
            return self.PENDING_STATUS, resp
        if error and error in ["invalid_grant", "code_expired", "invalid_client"]:
            return self.EXPIRED, resp
        if error:
            return self.ERROR, resp

        xbmc.log("ERROR IS {}".format(error))
        expires_in = int(resp.get("expires_in")) + int(time.time())
        self.access_token = resp.get("access_token")
        self.access_token_expire = str(expires_in)

        if self.access_token:
            for key, val in resp.items():
                self.settings.setSetting(key.encode("utf-8"), str(val).encode("utf-8"))
            self.settings.setSetting("device_code", "")
            return self.SUCCESS, resp
        return self.ERROR, resp

    def verify_device_code(self, interval, parent):
        while not parent.stopped.wait(interval):
            success, resp = self.get_token()
            if success == self.SUCCESS:
                self.afterAuth(force=True)
                parent.closeWindow()
                return True


class AuthWindow(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.stopped = threading.Event()
        self.auth = Auth(kwargs["settings"], window=self, afterAuth=kwargs["afterAuth"])

    def onInit(self):
        status, resp = self.auth.get_device_code()
        if status == self.auth.ERROR:
            label = self.getControl(9111)
            label.setLabel(
                "Устройство не поддерживается.\n"
                "Посетите http://kino.pub/device/support для уточнения деталей."
            )
            return
        label = self.getControl(9112)
        label.setLabel(resp["verification_uri"].encode("utf-8"))
        label = self.getControl(9113)
        label.setLabel(resp["user_code"].encode("utf-8"))
        t = threading.Thread(
            target=self.auth.verify_device_code,
            args=[int(resp["interval"]), self]
        )
        t.daemon = True
        t.start()

    def onAction(self, action):
        actionID = action.getId()
        if actionID in [9, 10, 13, 14, 15]:
            self.closeWindow()

    def closeWindow(self):
        self.stopped.set()
        for thread in threading.enumerate():
            if (thread.isAlive() and thread != threading.currentThread()):
                thread.join(1)
        self.close()
