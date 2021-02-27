from copy import deepcopy

import pytest

import expected_results
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


def test_watching(kodi):
    resp = kodi.Files.GetDirectory(
        directory="plugin://video.kino.pub/watching/", properties=["thumbnail"]
    )
    assert expected_results.WATCHING == resp["result"]["files"]


def test_watching_movies(kodi):
    resp = kodi.Files.GetDirectory(
        directory="plugin://video.kino.pub/watching_movies/",
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
    assert expected_results.WATCHING_MOVIES == resp["result"]["files"]


@pytest.mark.parametrize(
    "item", ["movies", "serials", "tvshow", "3d", "concerts", "documovies", "docuserials"]
)
def test_items_headings(kodi, item):
    expected_headings = deepcopy(expected_results.BASIC_HEADINGS)
    for directory in expected_headings:
        directory["file"] = directory["file"].format(item=item)
    resp = kodi.Files.GetDirectory(directory=f"plugin://video.kino.pub/items/{item}/")
    assert expected_headings == resp["result"]["files"]


def test_collections_headings(kodi):
    resp = kodi.Files.GetDirectory(directory="plugin://video.kino.pub/collections/")
    assert expected_results.COLLECTIONS_HEADINGS == resp["result"]["files"]


def test_bookmarks(kodi):
    resp = kodi.Files.GetDirectory(directory="plugin://video.kino.pub/bookmarks/")
    assert expected_results.BOOKMARKS == resp["result"]["files"]


def test_bookmarks_folder(kodi):
    resp = kodi.Files.GetDirectory(
        directory="plugin://video.kino.pub/bookmarks/161701/",
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
    assert expected_results.BOOKMARK_FOLDER_CONTENT == resp["result"]["files"]


def test_seasons(kodi):
    resp = kodi.Files.GetDirectory(
        directory="plugin://video.kino.pub/seasons/8632/",
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
    assert expected_results.SEASONS == resp["result"]["files"]


def test_season_episodes(kodi):
    resp = kodi.Files.GetDirectory(
        directory="plugin://video.kino.pub/season_episodes/8632/1/",
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
    assert expected_results.SEASON_EPISODES == resp["result"]["files"]
