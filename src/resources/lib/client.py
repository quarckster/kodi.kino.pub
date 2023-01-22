import http
import json
import os
import sys
import time
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

if TYPE_CHECKING:
    from resources.lib.plugin import Plugin
from resources.lib.utils import notice


class KinoApiRequestProcessor(urllib.request.BaseHandler):
    def __init__(self, plugin: "Plugin") -> None:
        self.plugin = plugin
        super().__init__()

    def https_request(self, request: urllib.request.Request) -> urllib.request.Request:
        self.plugin.logger.debug("Preparing request")
        request.add_header("Authorization", f"Bearer {self.plugin.settings.access_token}")
        return request

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
        self.plugin.logger.error(f"HTTPError. Code: {code}")
        notice(f"Код ответа сервера {code}", "Ошибка")
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
            self.plugin.logger.error("Recursion limit exceeded in handling status code 401")
            notice("Аутентификация не удалась", "Ошибка")
            sys.exit()
        self.plugin.logger.error(f"HTTPError. Code: {code}. Attempting to refresh the token.")
        request.recursion_counter_401 += 1  # type: ignore[attr-defined]
        self.plugin.auth.get_token()
        if not self.plugin.settings.access_token:
            self.plugin.logger.error("Access token is empty.")
            notice("Аутентификация не удалась", "Ошибка")
            sys.exit()
        return self.parent.open(request, timeout=60)

    def http_error_429(
        self,
        request: urllib.request.Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: HTTPMessage,
    ) -> Union[http.client.HTTPResponse, NoReturn]:
        if request.recursion_counter_429 > 2:  # type: ignore[attr-defined]
            self.plugin.logger.error("Recursion limit exceeded in handling status code 429")
            notice(f"Код ответа сервера {code}. Попробуйте ещё раз.", "Ошибка")
            sys.exit()
        request.recursion_counter_429 += 1  # type: ignore[attr-defined]
        self.plugin.logger.error(
            f"HTTPError. Code: {code}. Retrying after 5 seconds. "
            f"Attempt {request.recursion_counter_429}."  # type: ignore[attr-defined]
        )
        time.sleep(5)
        return self.parent.open(request, timeout=60)


class KinoPubClient:
    url = os.getenv("KINO_PUB_API_URL", "https://api.service-kp.com/v1")

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
            notice(f"Код ответа сервера kino.pub {data['status']}", "Ошибка")
            sys.exit()

    def _make_request(self, request: urllib.request.Request) -> Dict[str, Any]:
        self.plugin.logger.info(
            f"sending {request.get_method()} request to {request.get_full_url()}"
        )
        request.recursion_counter_401 = 0  # type: ignore[attr-defined]
        request.recursion_counter_429 = 0  # type: ignore[attr-defined]
        try:
            response = self.opener.open(request, timeout=60)
        except Exception:
            notice("Не удалось получить ответ от kino.pub", "Ошибка")
            raise
        return self._handle_response(response)

    def get(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        urlencoded_data = urllib.parse.urlencode(data or {})
        query = f"?{urlencoded_data}" if urlencoded_data else ""
        request = urllib.request.Request(f"{self.url}/{self.endpoint}{query}")
        return self._make_request(request)

    def post(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        encoded_data = urllib.parse.urlencode(data or {}).encode("utf-8")
        request = urllib.request.Request(f"{self.url}/{self.endpoint}", data=encoded_data)
        return self._make_request(request)
