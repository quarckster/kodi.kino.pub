# -*- coding: utf-8 -*-
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

from resources.lib.utils import notice


class KinoPubClient(object):
    url = "https://api.service-kp.com/v1"

    def __init__(self, plugin, action):
        self.action = action
        self.plugin = plugin

    def _make_request(self, request, timeout=600):
        self.plugin.logger.info(
            f"sending {request.get_method()} request to {request.get_full_url()}"
        )
        request.add_header("Authorization", f"Bearer {self.plugin.settings.access_token}")
        try:
            response = urllib.request.urlopen(request, timeout=timeout)
        except urllib.error.HTTPError as e:
            self.plugin.logger.error(f"HTTPError. Code: {e.code}")
            if e.code == 401:
                self.plugin.auth.get_token()
                if self.plugin.settings.access_token:
                    return self._make_request(request)
                sys.exit()
            else:
                notice(f"Код ответа сервера {e.code}", "Ошибка")
                sys.exit()
        except Exception as e:
            self.plugin.logger.error(f"{type(e).__name__}. Message: {e.message}")
            notice(e.message, "Ошибка")
        else:
            if r := response.read():
                response = json.loads(r)
                if response["status"] == 200:
                    return response
                else:
                    self.plugin.logger.error(f"Unknown error. Code: {response['status']}")
                    notice(f"Код ответа сервера {response['status']}", "Ошибка")

    def get(self, data=""):
        data = f"?{urllib.parse.urlencode(data)}" if data else ""
        request = urllib.request.Request(f"{self.url}/{self.action}{data}")
        return self._make_request(request)

    def post(self, data=""):
        data = urllib.parse.urlencode(data).encode("utf-8")
        request = urllib.request.Request(f"{self.url}/{self.action}", data=data)
        return self._make_request(request)
