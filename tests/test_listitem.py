import importlib
import pathlib
import sys
import types
from copy import copy


RESOURCES = (pathlib.Path(".").parent / "src").absolute()


class FakeActor:
    def __init__(self, name):
        self.name = name


class FakeInfoTagVideo:
    def __init__(self):
        self.calls = {}

    def setTitle(self, value):
        self.calls["title"] = value

    def setPlot(self, value):
        self.calls["plot"] = value

    def setYear(self, value):
        self.calls["year"] = value

    def setDuration(self, value):
        self.calls["duration"] = value

    def setGenres(self, value):
        self.calls["genre"] = value

    def setRating(self, rating, votes, name="default", is_default=False):
        self.calls["rating"] = (rating, votes, name, is_default)

    def setCast(self, value):
        self.calls["cast"] = [actor.name for actor in value]

    def setDirectors(self, value):
        self.calls["director"] = value

    def setIMDBNumber(self, value):
        self.calls["imdbnumber"] = value

    def setUniqueIDs(self, value, default):
        self.calls["unique_ids"] = (value, default)

    def setVotes(self, value):
        self.calls["votes"] = value

    def setCountries(self, value):
        self.calls["country"] = value

    def setTrailer(self, value):
        self.calls["trailer"] = value

    def setMediaType(self, value):
        self.calls["mediatype"] = value

    def setSeason(self, value):
        self.calls["season"] = value

    def setEpisode(self, value):
        self.calls["episode"] = value

    def setTvShowTitle(self, value):
        self.calls["tvshowtitle"] = value

    def setPlaycount(self, value):
        self.calls["playcount"] = value

    def setTvShowStatus(self, value):
        self.calls["status"] = value


def test_populate_video_info_tag(monkeypatch):
    orig_sys_path = copy(sys.path)
    sys.path.append(str(RESOURCES))

    fake_xbmcgui = types.SimpleNamespace(ListItem=type("ListItem", (), {}))
    fake_xbmcaddon = types.SimpleNamespace(
        Addon=lambda: types.SimpleNamespace(getLocalizedString=lambda value: str(value))
    )
    fake_xbmc = types.SimpleNamespace(Actor=FakeActor)

    monkeypatch.setitem(sys.modules, "xbmcgui", fake_xbmcgui)
    monkeypatch.setitem(sys.modules, "xbmcaddon", fake_xbmcaddon)
    monkeypatch.setitem(sys.modules, "xbmc", fake_xbmc)
    sys.modules.pop("resources.lib.utils", None)
    sys.modules.pop("resources.lib.listitem", None)

    listitem = importlib.import_module("resources.lib.listitem")

    info_tag = FakeInfoTagVideo()
    listitem.populate_video_info_tag(
        info_tag,
        {
            "title": "The Example",
            "plot": "A plot",
            "year": 2024,
            "genre": "Drama, Sci-Fi",
            "rating": 8.1,
            "cast": ["Alice", "Bob"],
            "director": "Jane Doe",
            "imdbnumber": 1234567,
            "votes": 456,
            "country": "US, CA",
            "trailer": "plugin://video.kino.pub/trailer/1",
            "mediatype": "episode",
            "season": 2,
            "episode": 3,
            "tvshowtitle": "The Show",
            "duration": 2400,
            "playcount": 1,
            "status": "Continuing",
        },
    )

    assert info_tag.calls == {
        "title": "The Example",
        "plot": "A plot",
        "year": 2024,
        "duration": 2400,
        "genre": ["Drama", "Sci-Fi"],
        "rating": (8.1, 456, "default", True),
        "cast": ["Alice", "Bob"],
        "director": ["Jane Doe"],
        "imdbnumber": "1234567",
        "unique_ids": ({"imdb": "1234567"}, "imdb"),
        "votes": 456,
        "country": ["US", "CA"],
        "trailer": "plugin://video.kino.pub/trailer/1",
        "mediatype": "episode",
        "season": 2,
        "episode": 3,
        "tvshowtitle": "The Show",
        "playcount": 1,
        "status": "Continuing",
    }

    sys.path = orig_sys_path
