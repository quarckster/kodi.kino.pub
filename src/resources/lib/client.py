import base64
import http
import json
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.client import HTTPMessage
from typing import Any
from typing import Dict
from typing import IO
from typing import NoReturn
from typing import Optional
from typing import TYPE_CHECKING
from typing import Union

import socks
import xbmc


if TYPE_CHECKING:
    from resources.lib.plugin import Plugin
from resources.lib.utils import localize
from resources.lib.utils import popup_error


TIMEOUT = 60


class KinoApiRequestProcessor(urllib.request.BaseHandler):
    def __init__(self, plugin: "Plugin") -> None:
        self.plugin = plugin
        super().__init__()

    def https_request(self, request: urllib.request.Request) -> urllib.request.Request:
        self.plugin.logger.debug(
            f"Sending {request.get_method()} request to {request.get_full_url()}"
        )
        request.add_header("Authorization", f"Bearer {self.plugin.settings.access_token}")
        self.plugin.logger.debug(
            f"Get system proxy settings: type={self.plugin.proxy_settings.type}, "
            f"host={self.plugin.proxy_settings.host}, port={self.plugin.proxy_settings.port}"
        )
        if self.plugin.proxy_settings.is_enabled:
            if not self.plugin.proxy_settings.is_correct:
                self.plugin.logger.error("http proxy settings are not correct")
                return request
            self.plugin.logger.debug(
                f"Set {self.plugin.proxy_settings.type} proxy from system settings, "
                f"auth: {self.plugin.proxy_settings.with_auth}"
            )
            if self.plugin.proxy_settings.is_http:
                self.set_http_proxy(request=request)
            if self.plugin.proxy_settings.is_socks:
                self.set_socks_proxy()
        return request

    def set_http_proxy(self, request: urllib.request.Request) -> None:
        proxy_settings = self.plugin.proxy_settings
        request.set_proxy(f"{proxy_settings.host}:{proxy_settings.port}", proxy_settings.type)
        if proxy_settings.with_auth:
            self.plugin.logger.debug(f"Use username and password for {proxy_settings.type} proxy")
            user_pass = f"{proxy_settings.username}:{proxy_settings.password}"
            creds = base64.b64encode(user_pass.encode()).decode("ascii")
            request.add_header("Proxy-authorization", f"Basic {creds}")
        return None

    def set_socks_proxy(self) -> None:
        proxy_settings = self.plugin.proxy_settings
        socks.set_default_proxy(
            proxy_type=socks.SOCKS4 if proxy_settings.is_socks4 else socks.SOCKS5,
            addr=proxy_settings.host,
            port=proxy_settings.port,
            rdns=proxy_settings.type == "socks5r",
            username=proxy_settings.username,
            password=proxy_settings.password,
        )
        socket.socket = socks.socksocket  # type: ignore[misc]
        return None

    http_request = https_request


class KinoApiDefaultErrorHandler(urllib.request.HTTPDefaultErrorHandler):
    def __init__(self, plugin: "Plugin") -> None:
        self.plugin = plugin
        super().__init__()

    def http_error_default(
        self,
        request: urllib.request.Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: HTTPMessage,
    ) -> NoReturn:
        self.plugin.logger.fatal(f"HTTPError. {request.get_full_url()}. Code: {code}. Exiting.")
        # Server response status code
        popup_error(f"{localize(32006)} {code}")
        sys.exit()


class KinoApiErrorProcessor(urllib.request.HTTPErrorProcessor):
    def __init__(self, plugin: "Plugin") -> None:
        self.plugin = plugin
        super().__init__()

    def http_error_401(
        self,
        request: urllib.request.Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: HTTPMessage,
    ) -> Union[http.client.HTTPResponse, NoReturn]:
        if request.recursion_counter_401 > 0:  # type: ignore[attr-defined]
            self.plugin.logger.fatal("Recursion limit exceeded in handling status code 401")
            # Authentication failed
            popup_error(localize(32003))
            sys.exit()
        self.plugin.logger.error(f"HTTPError. Code: {code}. Attempting to refresh the token.")
        request.recursion_counter_401 += 1  # type: ignore[attr-defined]
        self.plugin.auth.get_token()
        if not self.plugin.settings.access_token:
            self.plugin.logger.fatal("Access token is empty.")
            # Authentication failed
            popup_error(localize(32003))
            sys.exit()
        return self.parent.open(request, timeout=TIMEOUT)

    def http_error_429(
        self,
        request: urllib.request.Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: HTTPMessage,
    ) -> Union[http.client.HTTPResponse, NoReturn]:
        if request.recursion_counter_429 > 2:  # type: ignore[attr-defined]
            self.plugin.logger.fatal("Recursion limit exceeded in handling status code 429")
            # Server response status code {code}. Try again.
            popup_error(f"{localize(32006)} {code}. {localize(32007)}.")
            sys.exit()
        request.recursion_counter_429 += 1  # type: ignore[attr-defined]
        self.plugin.logger.error(
            f"HTTPError. Code: {code}. Retrying after 5 seconds. "
            f"Attempt {request.recursion_counter_429}."  # type: ignore[attr-defined]
        )
        xbmc.sleep(5000)
        return self.parent.open(request, timeout=TIMEOUT)


class KinoPubClient:
    def __init__(self, plugin: "Plugin") -> None:
        self.plugin = plugin
        self.opener = urllib.request.build_opener(
            KinoApiRequestProcessor(self.plugin),
            KinoApiErrorProcessor(self.plugin),
            KinoApiDefaultErrorHandler(self.plugin),
        )

    def __call__(self, endpoint: str) -> "KinoPubClient":
        self.endpoint = endpoint
        return self

    def _handle_response(
        self, response: http.client.HTTPResponse
    ) -> Union[Dict[str, Any], NoReturn]:
        data = json.loads(response.read())
        if data and data["status"] == 200:
            return data
        elif response.status == 200:
            return {"status": 200}
        else:
            self.plugin.logger.error(f"Unknown error. Code: {data['status']}")
            # Server response status code
            popup_error(f"{localize(32006)} {data['status']}")
            sys.exit()

    def _make_request(self, request: urllib.request.Request) -> Dict[str, Any]:
        request.recursion_counter_401 = 0  # type: ignore[attr-defined]
        request.recursion_counter_429 = 0  # type: ignore[attr-defined]
        request.add_header(
            "user-agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        )
        try:
            response = self.opener.open(request, timeout=TIMEOUT)
        except Exception:
            # kino.pub does not respond
            popup_error(localize(32008))
            raise
        return self._handle_response(response)

    def get(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        urlencoded_data = urllib.parse.urlencode(data or {})
        query = f"?{urlencoded_data}" if urlencoded_data else ""
        request = urllib.request.Request(f"{self.plugin.settings.api_url}/{self.endpoint}{query}")
        return self._make_request(request)

    def post(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        encoded_data = urllib.parse.urlencode(data or {}).encode("utf-8")
        request = urllib.request.Request(
            f"{self.plugin.settings.api_url}/{self.endpoint}", data=encoded_data
        )
        return self._make_request(request)
