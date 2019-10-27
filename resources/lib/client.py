# -*- coding: utf-8 -*-
import json
import sys
import urllib
import urllib2

import logger
from addonutils import notice
from authwindow import auth


class KinoPubClient(object):
    url = "http://api.service-kp.com/v1"

    def __init__(self, action):
        self.action = action

    def _make_request(self, request, timeout=600):
        logger.notice(
            "sending {} request to {}".format(request.get_method(), request.get_full_url())
        )
        request.add_header("Authorization", "Bearer {}".format(auth.access_token))
        try:
            response = urllib2.urlopen(request, timeout=timeout)
        except urllib2.HTTPError as e:
            logger.error("HTTPError. Code: {}. Message: {}".format(e.code, e.message))
            if e.code in [400, 401]:
                status, __ = auth.get_token(refresh=True)
                if status != auth.SUCCESS:
                    # reset access_token
                    auth.reauth()
                if auth.access_token:
                    return self._make_request(request)
                sys.exit()
            else:
                notice("Код ответа сервера {}".format(e.code), "Неизвестная ошибка")
        except Exception as e:
            logger.error("{}. Message: {}".format(type(e).__name__, e.message))
            notice(e.message, "Ошибка")
        else:
            response = json.loads(response.read())
            if response["status"] == 200:
                return response
            else:
                logger.error("Unknown error. Code: {}".format(response["status"]))
                notice("Код ответа сервера {}".format(response["status"]), "Неизвестная ошибка")

    def get(self, data=""):
        data = "?{}".format(urllib.urlencode(data)) if data else ""
        request = urllib2.Request("{}/{}{}".format(self.url, self.action, data))
        return self._make_request(request)

    def post(self, data=""):
        data = urllib.urlencode(data)
        request = urllib2.Request("{}/{}".format(self.url, self.action), data=data)
        return self._make_request(request)
