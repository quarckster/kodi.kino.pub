# -*- coding: utf-8 -*-
import json
import platform
import time
import urllib
import urllib2

import logger
import xbmc
import xbmcgui
from addonutils import nav_internal_link
from settings import settings


class AuthException(Exception):
    pass


class AuthPendingException(AuthException):
    pass


class AuthExpiredException(AuthException):
    pass


class EmptyTokenException(AuthException):
    pass


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
    CLIENT_ID = "xbmc"
    CLIENT_SECRET = "cgg3gtifu46urtfp2zp1nqtba0k2ezxh"
    OAUTH_API_URL = "http://api.service-kp.com/oauth2/device"

    def __init__(self):
        self.auth_dialog = AuthDialog()

    def _make_request(self, payload):
        logger.notice("sending payload {} to oauth api url".format(payload))
        try:
            response = urllib2.urlopen(
                urllib2.Request(self.OAUTH_API_URL), urllib.urlencode(payload)
            ).read()
            return json.loads(response)
        except urllib2.HTTPError as e:
            if e.code == 400:
                _data = e.read()
                response = json.loads(_data)
                return response
            # server can respond with 429 status, so we just wait until it gives a correct response
            elif e.code == 429:
                for _ in range(2):
                    time.sleep(3)
                    return self.request(payload)
            else:
                logger.fatal(
                    "oauth request error; status: {}; message: {}".format(e.code, e.message)
                )
                raise

    def _get_device_code(self):
        payload = {
            "grant_type": "device_code",
            "client_id": self.CLIENT_ID,
            "client_secret": self.CLIENT_SECRET,
        }
        resp = self._make_request(payload)
        if "error" in resp:
            raise AuthException
        return {
            "device_code": resp["code"].encode("utf-8"),
            "user_code": resp["user_code"].encode("utf-8"),
            "verification_uri": resp["verification_uri"].encode("utf8"),
            "refresh_interval": int(resp["interval"]),
        }

    def _refresh_token(self):
        logger.notice("refreshing token")
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": settings.refresh_token,
            "client_id": self.CLIENT_ID,
            "client_secret": self.CLIENT_SECRET,
        }
        resp = self._make_request(payload)
        if "access_token" not in resp:
            raise EmptyTokenException
        error = resp.get("error")
        if error and error in ["invalid_grant", "code_expired", "invalid_client"]:
            logger.error(error)
            self._activate()
            return
        self._update_settings(
            resp["refresh_token"].encode("utf-8"),
            resp["access_token"].encode("utf-8"),
            resp["expires_in"],
        )

    def _get_device_token(self, device_code):
        logger.notice("getting a new device token")
        payload = {
            "grant_type": "device_token",
            "client_id": self.CLIENT_ID,
            "code": device_code,
            "client_secret": self.CLIENT_SECRET,
        }
        resp = self._make_request(payload)
        error = resp.get("error")
        if error and error == "authorization_pending":
            raise AuthPendingException
        if error and error in ["invalid_grant", "code_expired", "invalid_client"]:
            raise AuthExpiredException
        self._update_settings(
            resp["refresh_token"].encode("utf-8"),
            resp["access_token"].encode("utf-8"),
            resp["expires_in"],
        )

    def _update_device_info(self):
        from client import KinoPubClient

        result = {"build_version": "Busy", "friendly_name": "Busy"}
        while "Busy" in result.values():
            result = {
                "build_version": xbmc.getInfoLabel("System.BuildVersion"),
                "friendly_name": xbmc.getInfoLabel("System.FriendlyName"),
            }
        software = "Kodi {}".format(result["build_version"].split()[0])
        KinoPubClient("device/notify").post(
            data={
                "title": result["friendly_name"],
                "hardware": platform.machine(),
                "software": software,
            }
        )

    def _verify_device_code(self, interval, device_code):
        steps = (5 * 60) // interval
        self.auth_dialog.total = steps
        for i in range(steps):
            if self.auth_dialog.iscanceled:
                self.auth_dialog.close(cancel=True)
                break
            else:
                try:
                    self._get_device_token(device_code)
                except AuthPendingException:
                    self.auth_dialog.update(i)
                    xbmc.sleep(interval * 1000)
                else:
                    self._update_device_info()
                    self.auth_dialog.close()
                    break
        else:
            self.auth_dialog.close(cancel=True)

    def _update_settings(self, refresh_token, access_token, expires_in):
        settings.refresh_token = refresh_token
        settings.access_token = access_token
        settings.access_token_expire = str(expires_in + int(time.time()))
        logger.notice(
            "refresh token - {}; access token - {}; expires in - {}".format(
                refresh_token, access_token, expires_in
            )
        )

    def _activate(self):
        resp = self._get_device_code()
        self.auth_dialog.show(
            "\n".join(
                [
                    "Откройте [B]{}[/B]".format(resp["verification_uri"]),
                    "и введите следующий код: [B]{}[/B]".format(resp["user_code"]),
                ]
            )
        )
        self._verify_device_code(resp["refresh_interval"], resp["device_code"])

    @property
    def is_token_expired(self):
        return int(settings.access_token_expire) < int(time.time())

    def get_token(self):
        if not settings.access_token:
            self._activate()
        if self.is_token_expired:
            self._refresh_token()


auth = Auth()
