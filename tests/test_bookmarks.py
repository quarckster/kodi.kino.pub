import time

import pytest
from wait_for import wait_for

from helpers import close_keyboard
from helpers import verify_request
from paths import HOST_DIR


@pytest.fixture
def change_token():
    "This fixture is required in order to correctly match an http request in the mock server."
    with open(f"{HOST_DIR}/addon_data/settings.xml", "r+") as settings_xml:
        orig_content = settings_xml.read()
        new_content = orig_content.replace("some_token", "token_after_bookmark_creating")
        settings_xml.seek(0)
        settings_xml.write(new_content)
    yield
    with open(f"{HOST_DIR}/addon_data/settings.xml", "w") as settings_xml:
        settings_xml.write(orig_content)


def test_create_bookmarks_folder(request, kodi, change_token):
    request.addfinalizer(lambda: close_keyboard(kodi))
    resp = kodi.Addons.ExecuteAddon(addonid="video.kino.pub", params="/create_bookmarks_folder")
    assert resp["result"] == "OK"
    time.sleep(3)
    resp = kodi.Input.SendText(text="Test")
    assert resp["result"] == "OK"
    expected_request = {
        "httpRequest": {
            "method": "POST",
            "path": "/v1/bookmarks/create",
            "body": {"string": "title=Test"},
        },
        "times": {"atLeast": 1, "atMost": 1},
    }
    wait_for(verify_request, func_args=[expected_request], timeout=5)


def test_remove_bookmarks_folder(kodi):
    resp = kodi.Addons.ExecuteAddon(
        addonid="video.kino.pub", params="/remove_bookmarks_folder/814132"
    )
    assert resp["result"] == "OK"
    expected_request = {
        "httpRequest": {
            "method": "POST",
            "path": "/v1/bookmarks/remove-folder",
            "body": {"string": "folder=814132"},
        },
        "times": {"atLeast": 1, "atMost": 1},
    }
    wait_for(verify_request, func_args=[expected_request], timeout=5)
