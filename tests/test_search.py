import os
from pathlib import Path

import expected_results
from paths import HOST_DIR


def test_new_search(request, kodi):
    @request.addfinalizer
    def _cleanup():
        if Path(f"{HOST_DIR}/addon_data/history").exists():
            os.remove(f"{HOST_DIR}/addon_data/history")

    resp = kodi.Addons.ExecuteAddon(addonid="video.kino.pub", params="/new_search/all/")
    assert resp["result"] == "OK"
    resp = kodi.Input.SendText(text="Matrix")
    assert resp["result"] == "OK"
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
