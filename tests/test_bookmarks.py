import time

import pytest

import expected_results
from paths import HOST_DIR


@pytest.fixture
def change_token():
    "This fixture is required in order to coorectly match http request in he mock server."
    with open(f"{HOST_DIR}/addon_data/settings.xml", "r+") as settings_xml:
        orig_content = settings_xml.read()
        new_content = orig_content.replace("some_token", "token_after_bookmark_creating")
        settings_xml.seek(0)
        settings_xml.write(new_content)
    yield
    with open(f"{HOST_DIR}/addon_data/settings.xml", "w") as settings_xml:
        settings_xml.write(orig_content)


def test_create_bookmarks_folder(request, kodi, change_token):
    @request.addfinalizer
    def _cleanup():
        time.sleep(3)
        while (
            kodi.GUI.GetProperties(properties=["currentwindow"])["result"]["currentwindow"]["label"]
            == "Virtual keyboard"
        ):
            kodi.Input.Back()
            time.sleep(3)

    resp = kodi.Addons.ExecuteAddon(addonid="video.kino.pub", params="/create_bookmarks_folder")
    assert resp["result"] == "OK"
    time.sleep(3)
    resp = kodi.Input.SendText(text="Test")
    assert resp["result"] == "OK"
    resp = kodi.Files.GetDirectory(directory="plugin://video.kino.pub/bookmarks/")
    assert expected_results.TEST_CREATE_BOOKMARK == resp["result"]["files"]
