import re
import subprocess

import pytest

import expected_results
from helpers import podman

HTTP_PATTERN = r".*\[http\] 127\.0\.0\.1:\d{5} <-> localhost:1080 via DIRECT"
SOCKS5_PATTERN = r".*\[socks5\] 127\.0\.0\.1:\d{5} <-> 127.0.0.1:1080 via DIRECT"

PARAMS = (
    pytest.param((0, False, False), id="http-non-auth"),
    pytest.param((0, True, False), id="http-auth"),
    pytest.param((0, True, True), id="http-auth-negative"),
    pytest.param((3, False, False), id="socks5-non-auth"),
    pytest.param((3, True, False), id="socks5-auth"),
    pytest.param((3, True, True), id="socks5-auth-negative"),
)


@pytest.fixture(scope="module", params=PARAMS)
def proxy(kodi, request):
    proxy_type, is_auth, negative = request.param
    user = "test_user"
    password = "test_password"
    listen_arg = f"{user}:{password}@:8443" if is_auth else ":8443"
    podman(
        "run",
        "--detach",
        "--pod=kodipod",
        "--name=proxy",
        "docker.io/nadoo/glider:0.16",
        "-listen",
        listen_arg,
        "-verbose",
    )
    kodi.Settings.SetSettingValue(setting="network.usehttpproxy", value=True)
    kodi.Settings.SetSettingValue(setting="network.httpproxytype", value=proxy_type)
    kodi.Settings.SetSettingValue(setting="network.httpproxyserver", value="127.0.0.1")
    kodi.Settings.SetSettingValue(setting="network.httpproxyport", value=8443)
    if is_auth:
        kodi.Settings.SetSettingValue(setting="network.httpproxyusername", value=user)
        password = "wrong_password" if negative else password
        kodi.Settings.SetSettingValue(setting="network.httpproxypassword", value=password)
    yield proxy_type, negative
    kodi.Settings.ResetSettingValue(setting="network.usehttpproxy")
    kodi.Settings.ResetSettingValue(setting="network.httpproxytype")
    kodi.Settings.ResetSettingValue(setting="network.httpproxyserver")
    kodi.Settings.ResetSettingValue(setting="network.httpproxyport")
    if is_auth:
        kodi.Settings.ResetSettingValue(setting="network.httpproxyusername")
        kodi.Settings.ResetSettingValue(setting="network.httpproxypassword")
    podman("rm", "-f", "proxy")


def test_proxy(kodi, proxy):
    proxy_type, negative = proxy
    resp = kodi.Files.GetDirectory(directory="plugin://video.kino.pub/bookmarks/")
    if not negative:
        assert expected_results.BOOKMARKS == resp["result"]["files"]
    ps = subprocess.run(["podman", "logs", "proxy"], capture_output=True)
    last_line = ps.stderr.splitlines()[-1].decode("utf-8")
    if negative:
        assert "auth failed" in last_line
    else:
        pattern = HTTP_PATTERN if proxy_type == 0 else SOCKS5_PATTERN
        assert re.match(pattern, last_line)
