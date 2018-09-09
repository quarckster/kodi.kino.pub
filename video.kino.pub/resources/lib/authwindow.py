# -*- coding: utf-8 -*-
import json
import time
import urllib
import urllib2

import xbmc
import xbmcgui

from addonutils import nav_internal_link, update_device_info
from data import __plugin__, __settings__


class AuthDialog(object):
    def __init__(self):
        self.total = 0
        self.position = 1
        self._dialog = xbmcgui.DialogProgress()

    def close(self, cancel=False):
        if self._dialog:
            self._dialog.close()
            self._dialog = None
        if cancel:
            nav_internal_link("/")

    def update(self, steps=1):
        self.position += steps
        position = int(float((100.0 // self.total)) * self.position)
        self._dialog.update(position)

    def show(self, text):
        self._dialog.create("Активация устройства", text)

    @property
    def iscanceled(self):
        return self._dialog.iscanceled() if self._dialog else True


class Auth(object):
    settings = __settings__
    terminated = False
    timer = 0
    CLIENT_ID = "xbmc"
    CLIENT_SECRET = "cgg3gtifu46urtfp2zp1nqtba0k2ezxh"
    OAUTH_API_URL = "http://api.service-kp.com/oauth2/device"
    ERROR, PENDING_STATUS, SUCCESS, EXPIRED = range(4)

    def __init__(self):
        self.window = AuthDialog()

    @property
    def is_token_expired(self):
        return self.access_token_expire < int(time.time())

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
        self.do_login()

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

    def verify_device_code(self, interval):
        steps = (10 * 60) // interval
        self.window.total = steps
        for _ in range(steps):
            if self.window.iscanceled:
                self.window.close(cancel=True)
                break
            else:
                success, resp = self.get_token()
                if success == self.SUCCESS:
                    update_device_info(force=True)
                    self.window.close()
                    break
                self.window.update()
                time.sleep(interval)
        else:
            self.window.close(cancel=True)

    def do_login(self):
        xbmc.log("{}: No access_token. Show modal auth".format(__plugin__))
        status, resp = self.get_device_code()
        if status == self.ERROR:
            self.window.show("\n".join([
                "Устройство не поддерживается.",
                "Посетите http://kino.pub/device/support для уточнения деталей."
            ]))
            self.window.close(cancel=True)
        self.window.show("\n".join([
            "Откройте [B]{}[/B]".format(resp["verification_uri"].encode("utf-8")),
            "и введите следующий код: [B]{}[/B]".format(resp["user_code"].encode("utf-8"))
        ]))
        self.verify_device_code(int(resp["interval"]))
        xbmc.log("{}: Close modal auth".format(__plugin__))


auth = Auth()
