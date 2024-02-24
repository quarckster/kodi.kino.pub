import json
import platform
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any
from typing import Dict
from typing import TYPE_CHECKING

import xbmc
import xbmcgui

from resources.lib.client import KinoApiRequestProcessor

if TYPE_CHECKING:
    from resources.lib.plugin import Plugin
from resources.lib.utils import cached_property
from resources.lib.utils import localize
from resources.lib.utils import popup_error


TIMEOUT = 60


class AuthException(Exception):
    pass


class AuthPendingException(AuthException):
    pass


class AuthExpiredException(AuthException):
    pass


class EmptyTokenException(AuthException):
    pass


class AuthDialog:
    def __init__(self, plugin: "Plugin") -> None:
        self.total = 0
        self.plugin = plugin

    @cached_property
    def _dialog(self):
        # In order to prevent WARNING: has left several classes in memory that we couldn't clean up.
        # The classes include: N9XBMCAddon7xbmcgui14DialogProgressE
        return xbmcgui.DialogProgress()

    def close(self, cancel: bool = False) -> None:
        if self._dialog:
            self._dialog.close()
            self._dialog = None
            xbmc.executebuiltin("Container.Refresh")
        if cancel:
            self.plugin.routing.redirect("/")

    def update(self, step: int) -> None:
        position = int(100 * step / float(self.total))
        self._dialog.update(position)

    def show(self, text: str) -> None:
        # Device activation
        self._dialog.create(localize(32001), text)

    @property
    def iscanceled(self) -> bool:
        return self._dialog.iscanceled() if self._dialog else True


class Auth:
    CLIENT_ID = "xbmc"
    CLIENT_SECRET = "cgg3gtifu46urtfp2zp1nqtba0k2ezxh"

    def __init__(self, plugin: "Plugin") -> None:
        self._auth_dialog = AuthDialog(plugin)
        self.plugin = plugin
        self.opener = urllib.request.build_opener(
            KinoApiRequestProcessor(self.plugin),
        )

    def _make_request(self, payload):
        self.plugin.logger.debug(f"Sending payload {payload} to oauth api")
        try:
            request = urllib.request.Request(
                self.plugin.settings.oauth_api_url,
                data=urllib.parse.urlencode(payload or {}).encode("utf-8"),
            )
            request.add_header(
                "user-agent",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            )
            response = self.opener.open(request, timeout=TIMEOUT)
            return json.loads(response.read())
        except urllib.error.HTTPError as e:
            if e.code == 400:
                response = json.loads(e.read())
                error = response.get("error")
                if error and error in [
                    "code_expired",
                    "authorization_expired",
                    "invalid_refresh_token",
                ]:
                    raise AuthExpiredException
                if error and error == "authorization_pending":
                    raise AuthPendingException
                if error:
                    # Authentication error
                    popup_error(localize(32002))
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
                    f"Oauth request error; status: {e.code}; message: {e.message}"
                )
                # Authentication failed
                popup_error(localize(32003))
                sys.exit()

    def _get_device_code(self) -> Dict[str, Any]:
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

    def _get_device_token(self, device_code: str) -> None:
        self.plugin.logger.debug("Getting a new device token")
        payload = {
            "grant_type": "device_token",
            "client_id": self.CLIENT_ID,
            "code": device_code,
            "client_secret": self.CLIENT_SECRET,
        }
        resp = self._make_request(payload)
        self._update_settings(resp["refresh_token"], resp["access_token"], resp["expires_in"])

    def _refresh_token(self) -> None:
        self.plugin.logger.debug("Refreshing token")
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

    def _update_device_info(self) -> None:
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

    def _verify_device_code(self, interval: int, device_code: str) -> None:
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

    def _update_settings(self, refresh_token: str, access_token: str, expires_in: int) -> None:
        self.plugin.settings.refresh_token = refresh_token
        self.plugin.settings.access_token = access_token
        self.plugin.settings.access_token_expire = str(expires_in + int(time.time()))
        self.plugin.logger.debug(
            f"Refresh token - {refresh_token}; access token - {access_token}; "
            f"expires in - {expires_in}"
        )

    def _activate(self) -> None:
        resp = self._get_device_code()
        self._auth_dialog.show(
            # Open and enter the code
            f"{localize(32004)} [B]{resp['verification_uri']}[/B]\n"
            f"{localize(32005)}: [B]{resp['user_code']}[/B]",
        )
        self._verify_device_code(resp["refresh_interval"], resp["device_code"])

    @property
    def is_token_expired(self) -> bool:
        return int(self.plugin.settings.access_token_expire) < int(time.time())

    def get_token(self) -> None:
        if not self.plugin.settings.access_token:
            self._activate()
        else:
            self._refresh_token()
