# -*- coding: utf-8 -*-
import json
import sys
import urllib

import urllib2

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
            response = urllib2.urlopen(request, timeout=timeout)
        except urllib2.HTTPError as e:
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
            self.plugin.logger.error("{}. Message: {}".format(type(e).__name__, e.message))
            notice(e.message, "Ошибка")
        else:
            response = json.loads(response.read())
            if response["status"] == 200:
                return response
            else:
                self.plugin.logger.error("Unknown error. Code: {}".format(response["status"]))
                notice("Код ответа сервера {}".format(response["status"]), "Неизвестная ошибка")

    def get(self, data=""):
        data = "?{}".format(urllib.urlencode(data)) if data else ""
        request = urllib2.Request("{}/{}{}".format(self.url, self.action, data))
        return self._make_request(request)

    def post(self, data=""):
        data = urllib.urlencode(data)
        request = urllib2.Request("{}/{}".format(self.url, self.action), data=data)
        return self._make_request(request)
