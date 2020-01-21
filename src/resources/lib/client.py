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
        self.plugin.logger.notice(
            "sending {} request to {}".format(request.get_method(), request.get_full_url())
        )
        request.add_header("Authorization", "Bearer {}".format(self.plugin.settings.access_token))
        try:
            response = urllib.request.urlopen(request, timeout=timeout)
        except urllib.error.HTTPError as e:
            self.plugin.logger.error("HTTPError. Code: {}.".format(e.code))
            if e.code == 401:
                self.plugin.auth.get_token()
                if self.plugin.settings.access_token:
                    return self._make_request(request)
                sys.exit()
            else:
                notice("Код ответа сервера {}".format(e.code), "Ошибка")
                sys.exit()
        except Exception as e:
            self.plugin.logger.error("{}. Message: {}".format(type(e).__name__, e.reason))
            notice(e.reason, "Ошибка")
        else:
            response = json.loads(response.read())
            if response["status"] == 200:
                return response
            else:
                self.plugin.logger.error("Unknown error. Code: {}".format(response["status"]))
                notice("Код ответа сервера {}".format(response["status"]), "Неизвестная ошибка")

    def get(self, data=""):
        data = "?{}".format(urllib.parse.urlencode(data)) if data else ""
        request = urllib.request.Request("{}/{}{}".format(self.url, self.action, data))
        return self._make_request(request)

    def post(self, data=""):
        data = urllib.parse.urlencode(data)
        request = urllib.request.Request("{}/{}".format(self.url, self.action), data=data)
        return self._make_request(request)
