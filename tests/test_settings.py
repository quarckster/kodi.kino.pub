import pytest

from expected_results import ACTIVATED_HOME
from paths import HOST_DIR


HOME_ITEMS = [
    ("search", "plugin://video.kino.pub/search/all/"),
    ("last", "plugin://video.kino.pub/items/all/fresh/"),
    ("popular", "plugin://video.kino.pub/items/all/popular/"),
    ("hot", "plugin://video.kino.pub/items/all/hot/"),
    ("sort", "plugin://video.kino.pub/items/all/sort/"),
    ("tv", "plugin://video.kino.pub/tv/"),
    ("collections", "plugin://video.kino.pub/collections/"),
    ("movies", "plugin://video.kino.pub/items/movies/"),
    ("serials", "plugin://video.kino.pub/items/serials/"),
    ("tvshows", "plugin://video.kino.pub/items/tvshow/"),
    ("3d", "plugin://video.kino.pub/items/3d/"),
    ("concerts", "plugin://video.kino.pub/items/concerts/"),
    ("documovies", "plugin://video.kino.pub/items/documovies/"),
    ("docuserials", "plugin://video.kino.pub/items/docuserials/"),
]


@pytest.fixture(params=HOME_ITEMS, ids=lambda param: param[0])
def home_menu(request):
    item, url = request.param
    with open(f"{HOST_DIR}/addon_data/settings.xml", "r+") as settings_xml:
        orig_content = settings_xml.read()
        new_content = orig_content.replace(
            f'<setting id="show_{item}">true</setting>',
            f'<setting id="show_{item}">false</setting>',
        )
        settings_xml.seek(0)
        settings_xml.write(new_content)
    yield [item for item in ACTIVATED_HOME if item["file"] != url]
    with open(f"{HOST_DIR}/addon_data/settings.xml", "w") as settings_xml:
        settings_xml.write(orig_content)


def test_toggle_home_items(kodi, home_menu):
    resp = kodi.Files.GetDirectory(directory="plugin://video.kino.pub")
    assert home_menu == resp["result"]["files"]
