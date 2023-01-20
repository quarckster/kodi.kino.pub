import importlib
import pathlib
from unittest.mock import MagicMock

import pytest

LIB = pathlib.Path(".").parent / "src" / "resources" / "lib"


@pytest.fixture
def kodi_kino_pub():
    loader = importlib.machinery.SourceFileLoader("kodi_kino_pub", str(LIB / "settings.py"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


@pytest.mark.parametrize(
    "loc", [pytest.param(["Россия", "ru"], id="ru"), pytest.param(["Нидерланды", "nl"], id="nl")]
)
def test_settings_locs(monkeypatch, loc, kodi_kino_pub):
    addon_mock = MagicMock()
    addon_mock.getSetting = MagicMock(return_value=loc[0])
    addon_mock_class = MagicMock(return_value=addon_mock)
    monkeypatch.setattr(kodi_kino_pub.xbmcaddon, "Addon", addon_mock_class)
    settings = kodi_kino_pub.Settings()
    assert settings.loc == loc[1]


def test_settings_locs_negative(monkeypatch, kodi_kino_pub):
    addon_mock = MagicMock()
    addon_mock.getSetting = MagicMock(return_value="NONSENSE")
    addon_mock_class = MagicMock(return_value=addon_mock)
    monkeypatch.setattr(kodi_kino_pub.xbmcaddon, "Addon", addon_mock_class)
    settings = kodi_kino_pub.Settings()
    with pytest.raises(KeyError):
        settings.loc
