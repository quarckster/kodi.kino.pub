import subprocess
from pathlib import Path

from paths import HOST_DIR


def get_addon_logs():
    ps = subprocess.run(
        ["podman", "exec", "-t", "kodi", "cat", ".kodi/temp/video_kino_pub.log"],
        capture_output=True,
    )
    return ps.stdout.decode("utf-8")


def test_http_401(request, kodi):
    settings_xml = Path(f"{HOST_DIR}/addon_data/settings.xml")
    orig_content = settings_xml.read_text(encoding="utf-8")

    @request.addfinalizer
    def _tear_down():
        settings_xml.write_text(data=orig_content, encoding="utf-8")

    resp = kodi.Files.GetDirectory(directory="plugin://video.kino.pub/bookmarks/401/")
    assert resp["result"]
    logs = get_addon_logs()
    assert "HTTPError. Code: 401. Attempting to refresh the token." in logs


def test_http_429(kodi):
    kodi.Files.GetDirectory(directory="plugin://video.kino.pub/bookmarks/429/")
    logs = get_addon_logs()
    assert "HTTPError. Code: 429. Retrying after 5 seconds." in logs
    assert "Recursion limit exceeded in handling status code 429" in logs


def test_http_500(kodi):
    kodi.Files.GetDirectory(directory="plugin://video.kino.pub/bookmarks/500/")
    logs = get_addon_logs()
    assert "HTTPError. http://localhost:1080/v1/bookmarks/500. Code: 500. Exiting." in logs
