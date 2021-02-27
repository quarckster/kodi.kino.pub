import json

import requests


def verify_request(request):
    r = requests.put("http://localhost:1080/mockserver/verify", data=json.dumps(request))
    return r.ok
