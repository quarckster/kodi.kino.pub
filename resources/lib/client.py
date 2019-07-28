# -*- coding: utf-8 -*-
import json
import sys
import urllib
import urllib2
import xbmc
import xbmcgui
from addonutils import notice
from authwindow import auth
from data import __plugin__


class KinoPubClient(object):
    url = "http://api.service-kp.com/v1"

    def __init__(self, action):
        self.action = action

    def _make_request(self, request, timeout=600):
        # in order to avoid a race condition from
        # https://github.com/quarckster/kodi.kino.pub/issues/49
        for _ in range(10):
            if xbmcgui.Window(10000).getProperty("kinopub_api_lock") == "true":
                xbmc.sleep(300)
            else:
                break
        request.add_header("Authorization", "Bearer {}".format(auth.access_token))
        try:
            response = urllib2.urlopen(request, timeout=timeout)
        except urllib2.HTTPError as e:
            xbmc.log("{}. HTTPError. Code: {}. Message: {}".format(
                     __plugin__, e.code, e.message), level=xbmc.LOGERROR)
            if e.code in [400, 401]:
                xbmcgui.Window(10000).setProperty("kinopub_api_lock", "true")
                status, __ = auth.get_token(refresh=True)
                if status != auth.SUCCESS:
                    # reset access_token
                    auth.reauth()
                xbmcgui.Window(10000).clearProperty("kinopub_api_lock")
                if auth.access_token:
                    return self._make_request(request)
                sys.exit()
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
