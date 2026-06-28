import subprocess
from pathlib import Path

import pytest
from wait_for import wait_for

from paths import HOST_DIR


def get_addon_logs():
    ps = subprocess.run(
        ["podman", "exec", "-t", "kodi", "cat", ".kodi/temp/video_kino_pub.log"],
        capture_output=True,
    )
    return ps.stdout.decode("utf-8")


def assert_in_logs(message):
    # The add-on logs from a separate process and the file write lags behind the
    # JSON-RPC response, so poll the log until the expected message shows up.
    wait_for(lambda: message in get_addon_logs(), timeout=15, delay=1)


@pytest.mark.skip(
    reason="The 401 handler refreshes the access token; Kodi 20+ caches add-on "
    "settings for its whole lifetime, so the refreshed token leaks into the rest "
    "of the shared session and breaks token-matched endpoints (e.g. bookmarks). "
    "The refresh/retry logic is covered by a unit test instead."
)
def test_http_401(request, kodi):
    settings_xml = Path(f"{HOST_DIR}/addon_data/settings.xml")
    orig_content = settings_xml.read_text(encoding="utf-8")

    @request.addfinalizer
    def _tear_down():
        settings_xml.write_text(data=orig_content, encoding="utf-8")

    resp = kodi.Files.GetDirectory(directory="plugin://video.kino.pub/bookmarks/401/")
    assert resp["result"]
    assert_in_logs("HTTPError. Code: 401. Attempting to refresh the token.")


_BLOCKING_HANDLER = pytest.mark.skip(
    reason="The handler blocks (~15s of xbmc.sleep retries for 429) and then "
    "sys.exit()s inside a JSON-RPC call, which wedges the headless Kodi web server "
    "(seen on Kodi 21). The 429/500 handler logic is covered by unit tests "
    "(tests/test_client.py)."
)


@_BLOCKING_HANDLER
def test_http_429(kodi):
    kodi.Files.GetDirectory(directory="plugin://video.kino.pub/bookmarks/429/")
    assert_in_logs("HTTPError. Code: 429. Retrying after 5 seconds.")
    assert_in_logs("Recursion limit exceeded in handling status code 429")


@_BLOCKING_HANDLER
def test_http_500(kodi):
    kodi.Files.GetDirectory(directory="plugin://video.kino.pub/bookmarks/500/")
    assert_in_logs("HTTPError. http://localhost:1080/v1/bookmarks/500. Code: 500. Exiting.")
