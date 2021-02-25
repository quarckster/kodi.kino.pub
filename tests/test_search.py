import time
from pathlib import Path

import pytest
from wait_for import TimedOutError
from wait_for import wait_for

import expected_results
from paths import HOST_DIR


history_path = Path(f"{HOST_DIR}/addon_data/history")


def test_new_search(request, kodi):
    @request.addfinalizer
    def _cleanup():
        if history_path.exists():
            history_path.unlink()
        time.sleep(3)
        kodi.Input.Back()

    resp = kodi.Addons.ExecuteAddon(addonid="video.kino.pub", params="/new_search/all/")
    assert resp["result"] == "OK"
    time.sleep(3)
    resp = kodi.Input.SendText(text="Matrix")
    assert resp["result"] == "OK"
    try:
        wait_for(history_path.exists, timeout=3)
    except TimedOutError:
        pytest.fail("search history is not saved")
    assert history_path.read_text() == '["Matrix"]', "query is not stored in history file"


def test_search_result(kodi):
    resp = kodi.Files.GetDirectory(
        directory="plugin://video.kino.pub/search/all/results/?title=Matrix",
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
    assert resp["result"]["files"] == expected_results.SEARCH_RESULT


@pytest.fixture
def history():
    history_path.write_text('["Matrix", "Тест", "123", "Some video"]')
    yield
    if history_path.exists():
        history_path.unlink()


def test_history(kodi, history):
    resp = kodi.Files.GetDirectory(directory="plugin://video.kino.pub/search/all/")
    assert resp["result"]["files"] == expected_results.HISTORY


def test_clean_search_history(kodi, history):
    history_path.chmod(0o777)
    resp = kodi.Addons.ExecuteAddon(addonid="video.kino.pub", params="/clean_search_history/")
    assert resp["result"] == "OK"
    time.sleep(3)
    resp = kodi.Input.Left()
    assert resp["result"] == "OK"
    time.sleep(3)
    resp = kodi.Input.ButtonEvent(button="Enter", keymap="KB")
    assert resp["result"] == "OK"
    assert history_path.exists(), "search history doesn't exist"
    try:
        wait_for(history_path.read_text, fail_condition=lambda res: res != "[]", timeout=3)
    except TimedOutError:
        pytest.fail("search history is not cleaned")
    resp = kodi.Files.GetDirectory(directory="plugin://video.kino.pub/search/all/")
    assert resp["result"]["files"] == expected_results.EMPTY_HISTORY
