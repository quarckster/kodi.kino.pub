# -*- coding: utf-8 -*-
import json
import time
import urllib
import urllib2

import xbmc
import xbmcgui

from addonutils import nav_internal_link, update_device_info
from data import __plugin__, __device__


class AuthDialog(object):
    def __init__(self):
        self.total = 0
        self._dialog = xbmcgui.DialogProgress()

    def close(self, cancel=False):
        if self._dialog:
            self._dialog.close()
            self._dialog = None
            xbmc.executebuiltin("Container.Refresh")
        if cancel:
            nav_internal_link("/")

    def update(self, step):
        position = int(100 * step / float(self.total))
        self._dialog.update(position)

    def show(self, text):
        self._dialog.create("Активация устройства", text)

    @property
    def iscanceled(self):
        return self._dialog.iscanceled() if self._dialog else True


class Auth(object):
    device = __device__
    terminated = False
    timer = 0
    CLIENT_ID = "xbmc"
    CLIENT_SECRET = "cgg3gtifu46urtfp2zp1nqtba0k2ezxh"
    OAUTH_API_URL = "http://api.service-kp.com/oauth2/device"
    ERROR, PENDING_STATUS, SUCCESS, EXPIRED = range(4)

    def __init__(self):
        self.window = AuthDialog()

    @property
    def access_token_expire(self):
        access_token_expire = self.device.get("access_token_expire")
        return None if access_token_expire is None else int(access_token_expire)

    @property
    def access_token(self):
        return self.device.get("access_token")

    @property
    def device_code(self):
        return self.device.get("code")

    @property
    def refresh_token(self):
        return self.device.get("refresh_token")

    def reauth(self):
        self.device.reset()
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
        self.device.update(**resp)
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
        self.device.update(access_token_expire=expires_in)

        if resp.get("access_token"):
            self.device.update(**resp)
            self.device.update(code=None, user_code=None)
            return self.SUCCESS, resp
        return self.ERROR, resp

    def verify_device_code(self, interval):
        steps = (5 * 60) // interval
        self.window.total = steps
        for i in range(steps):
            if self.window.iscanceled:
                self.window.close(cancel=True)
                break
            else:
                success, resp = self.get_token()
                if success == self.SUCCESS:
                    update_device_info(force=True)
                    self.window.close()
                    break
                self.window.update(i)
                xbmc.sleep(interval * 1000)
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
