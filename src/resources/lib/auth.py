# -*- coding: utf-8 -*-
import json
import platform
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from functools import cached_property

import xbmc
import xbmcgui

from resources.lib.utils import notice


class AuthException(Exception):
    pass


class AuthPendingException(AuthException):
    pass


class AuthExpiredException(AuthException):
    pass


class EmptyTokenException(AuthException):
    pass


class AuthDialog(object):
    def __init__(self, plugin):
        self.total = 0
        self.plugin = plugin

    @cached_property
    def _dialog(self):
        # In order to prevent WARNING: has left several classes in memory that we couldn't clean up.
        # The classes include: N9XBMCAddon7xbmcgui14DialogProgressE
        return xbmcgui.DialogProgress()

    def close(self, cancel=False):
        if self._dialog:
            self._dialog.close()
            self._dialog = None
            xbmc.executebuiltin("Container.Refresh")
        if cancel:
            self.plugin.routing.redirect("/")

    def update(self, step):
        position = int(100 * step / float(self.total))
        self._dialog.update(position)

    def show(self, text):
        self._dialog.create("Активация устройства", text)

    @property
    def iscanceled(self):
        return self._dialog.iscanceled() if self._dialog else True


class Auth(object):
    CLIENT_ID = "xbmc"
    CLIENT_SECRET = "cgg3gtifu46urtfp2zp1nqtba0k2ezxh"
    OAUTH_API_URL = "http://api.service-kp.com/oauth2/device"

    def __init__(self, plugin):
        self._auth_dialog = AuthDialog(plugin)
        self.plugin = plugin

    def _make_request(self, payload):
        self.plugin.logger.info(f"sending payload {payload} to oauth api")
        try:
            response = urllib.request.urlopen(
                urllib.request.Request(self.OAUTH_API_URL),
                urllib.parse.urlencode(payload).encode("utf-8"),
            ).read()
            return json.loads(response)
        except urllib.error.HTTPError as e:
            if e.code == 400:
                response = json.loads(e.read())
                error = response.get("error")
                if error and error in ["code_expired", "authorization_expired"]:
                    raise AuthExpiredException
                if error and error == "authorization_pending":
                    raise AuthPendingException
                if error:
                    notice("Ошибка аутентификации")
                    raise AuthException(error)
                return response
            # server can respond with 429 status, so we just wait until it gives a correct response
            elif e.code == 429:
                for _ in range(2):
                    time.sleep(3)
                    return self._make_request(payload)
            else:
                self._auth_dialog.close(cancel=True)
                self.plugin.logger.fatal(
                    f"oauth request error; status: {e.code}; message: {e.message}"
                )
                notice(f"Server status code {e.code}", "Activation error")
                sys.exit()

    def _get_device_code(self):
        payload = {
            "grant_type": "device_code",
            "client_id": self.CLIENT_ID,
            "client_secret": self.CLIENT_SECRET,
        }
        resp = self._make_request(payload)
        return {
            "device_code": resp["code"],
            "user_code": resp["user_code"],
            "verification_uri": resp["verification_uri"],
            "refresh_interval": int(resp["interval"]),
        }

    def _get_device_token(self, device_code):
        self.plugin.logger.info("getting a new device token")
        payload = {
            "grant_type": "device_token",
            "client_id": self.CLIENT_ID,
            "code": device_code,
            "client_secret": self.CLIENT_SECRET,
        }
        resp = self._make_request(payload)
        self._update_settings(resp["refresh_token"], resp["access_token"], resp["expires_in"])

    def _refresh_token(self):
        self.plugin.logger.info("refreshing token")
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.plugin.settings.refresh_token,
            "client_id": self.CLIENT_ID,
            "client_secret": self.CLIENT_SECRET,
        }
        try:
            resp = self._make_request(payload)
        except AuthExpiredException:
            self._activate()
            return
        self._update_settings(resp["refresh_token"], resp["access_token"], resp["expires_in"])

    def _update_device_info(self):
        result = {"build_version": "Busy", "friendly_name": "Busy"}
        while "Busy" in list(result.values()):
            result = {
                "build_version": xbmc.getInfoLabel("System.BuildVersion"),
                "friendly_name": xbmc.getInfoLabel("System.FriendlyName"),
            }
        software = f"Kodi {result['build_version'].split()[0]}"
        title = result["friendly_name"] if result["friendly_name"] != "unknown" else platform.node()
        self.plugin.client("device/notify").post(
            data={"title": title, "hardware": platform.machine(), "software": software}
        )

    def _verify_device_code(self, interval, device_code):
        steps = (5 * 60) // interval
        self._auth_dialog.total = steps
        for i in range(steps):
            if self._auth_dialog.iscanceled:
                self._auth_dialog.close(cancel=True)
                break
            else:
                try:
                    self._get_device_token(device_code)
                except AuthPendingException:
                    self._auth_dialog.update(i)
                    xbmc.sleep(interval * 1000)
                else:
                    self._update_device_info()
                    self._auth_dialog.close()
                    break
        else:
            self._auth_dialog.close(cancel=True)

    def _update_settings(self, refresh_token, access_token, expires_in):
        self.plugin.settings.refresh_token = refresh_token
        self.plugin.settings.access_token = access_token
        self.plugin.settings.access_token_expire = str(expires_in + int(time.time()))
        self.plugin.logger.info(
            f"refresh token - {refresh_token}; access token - {access_token}; "
            f"expires in - {expires_in}"
        )

    def _activate(self):
        resp = self._get_device_code()
        self._auth_dialog.show(
            f"Откройте [B]{resp['verification_uri']}[/B]\n"
            f"и введите следующий код: [B]{resp['user_code']}[/B]",
        )
        self._verify_device_code(resp["refresh_interval"], resp["device_code"])

    @property
    def is_token_expired(self):
        return int(self.plugin.settings.access_token_expire) < int(time.time())

    def get_token(self):
        if not self.plugin.settings.access_token:
            self._activate()
        else:
            self._refresh_token()
