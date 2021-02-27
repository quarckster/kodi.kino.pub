import json
import time

import requests
from wait_for import wait_for


def verify_request(request):
    r = requests.put("http://localhost:1080/mockserver/verify", data=json.dumps(request))
    return r.ok


def close_keyboard(kodi):
    def _fail_condition(result):
        return (
            kodi.GUI.GetProperties(properties=["currentwindow"])["result"]["currentwindow"]["label"]
            == "Virtual keyboard"
        )

    time.sleep(3)
    wait_for(kodi.Input.Back, fail_condition=_fail_condition, timeout=15, delay=3)
