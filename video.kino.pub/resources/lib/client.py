# -*- coding: utf-8 -*-
import json
import urllib
import urllib2
import xbmc
from addonutils import notice
from authwindow import auth
from data import __plugin__, __settings__


class KinoPubClient(object):
    url = "http://api.service-kp.com/v1"

    def __init__(self, action):
        self.action = action

    def _make_request(self, request, timeout=600):
        request.add_header("Authorization", "Bearer {}".format(auth.access_token))
        try:
            response = urllib2.urlopen(request, timeout=timeout)
        except urllib2.HTTPError as e:
            xbmc.log("{}. HTTPError. Code: {}. Message: {}".format(
                     __plugin__, e.code, e.message), level=xbmc.LOGERROR)
            if e.code in [400, 401]:
                status, __ = auth.get_token(refresh=True)
                if status != auth.SUCCESS:
                    # reset access_token
                    auth.reauth()
                return self._make_request(request)
            else:
                notice("Код ответа сервера {}".format(e.code), "Неизвестная ошибка")
        except Exception as e:
            xbmc.log("{}. {}. Message: {}".format(
                     __plugin__, e.__class__.__name__, e.message), level=xbmc.LOGERROR)
            notice(e.message, "Ошибка")
        else:
            response = json.loads(response.read())
            if response["status"] == 200:
                return response
            else:
                xbmc.log("{}. Unknown error. Code: {}".format(
                         __plugin__, response["status"]), level=xbmc.LOGERROR)
                notice("Код ответа сервера {}".format(response["status"]), "Неизвестная ошибка")

    def get(self, data=""):
        data = "?{}".format(urllib.urlencode(data)) if data else ""
        request = urllib2.Request("{}/{}{}".format(self.url, self.action, data))
        return self._make_request(request)

    def post(self, data=""):
        data = urllib.urlencode(data)
        request = urllib2.Request("{}/{}".format(self.url, self.action), data=data)
        return self._make_request(request)
