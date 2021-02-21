from copy import deepcopy

import expected_results
import pytest
from paths import HOST_DIR


def test_home_activated(kodi):
    resp = kodi.Files.GetDirectory(directory="plugin://video.kino.pub")
    assert expected_results.ACTIVATED_HOME == resp["result"]["files"]


@pytest.fixture
def remove_access_token():
    with open(f"{HOST_DIR}/addon_data/settings.xml", "r+") as settings_xml:
        orig_content = settings_xml.read()
        new_content = orig_content.replace(
            '<setting id="access_token" default="true">some_token</setting>', ""
        )
        settings_xml.seek(0)
        settings_xml.write(new_content)
    yield
    with open(f"{HOST_DIR}/addon_data/settings.xml", "w") as settings_xml:
        settings_xml.write(orig_content)


def test_home_nonactivated(kodi, remove_access_token):
    resp = kodi.Files.GetDirectory(directory="plugin://video.kino.pub")
    assert expected_results.NONACTIVATED_HOME == resp["result"]["files"]


@pytest.mark.parametrize("sorting", ["fresh", "hot", "popular"])
def test_all(kodi, sorting):
    resp = kodi.Files.GetDirectory(
        directory=f"plugin://video.kino.pub/items/all/{sorting}/",
        properties=[
            "country",
            "year",
            "rating",
            "duration",
            "director",
            "trailer",
            "plot",
            "cast",
            "imdbnumber",
            "votes",
            "fanart",
        ],
    )
    ITEMS_ALL = deepcopy(expected_results.ITEMS_ALL)
    next_page = ITEMS_ALL[-2]["file"].format(sorting=sorting)
    ITEMS_ALL[-2]["file"] = next_page
    assert ITEMS_ALL == resp["result"]["files"]
