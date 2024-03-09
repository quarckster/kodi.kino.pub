import re
import subprocess
import pytest

import expected_results

HTTP_PATTERN = r".*\[http\] 127\.0\.0\.1:\d{5} <-> localhost:1080 via DIRECT"
SOCKS5_PATTERN = r".*\[socks5\] 127\.0\.0\.1:\d{5} <-> 127.0.0.1:1080 via DIRECT"

@pytest.fixture(scope="module", params=[pytest.param(0, id="http"), pytest.param(3, id="socks5")], autouse=True)
def proxy(kodi, request):
    kodi.Settings.SetSettingValue(setting="network.usehttpproxy", value=True)
    kodi.Settings.SetSettingValue(setting="network.httpproxytype", value=request.param)
    kodi.Settings.SetSettingValue(setting="network.httpproxyserver", value="127.0.0.1")
    kodi.Settings.SetSettingValue(setting="network.httpproxyport", value=8443)
    yield request.param
    kodi.Settings.ResetSettingValue(setting="network.usehttpproxy")
    kodi.Settings.ResetSettingValue(setting="network.httpproxytype")
    kodi.Settings.ResetSettingValue(setting="network.httpproxyserver")
    kodi.Settings.ResetSettingValue(setting="network.httpproxyport")


def test_bookmarks_proxy(kodi, proxy):
    resp = kodi.Files.GetDirectory(directory="plugin://video.kino.pub/bookmarks/")
    assert expected_results.BOOKMARKS == resp["result"]["files"]
    ps = subprocess.run(["podman", "logs", "proxy"], capture_output=True)
    pattern = HTTP_PATTERN if proxy == 0 else SOCKS5_PATTERN
    last_line = ps.stderr.splitlines()[-1].decode("utf-8")
    assert re.match(pattern, last_line)
