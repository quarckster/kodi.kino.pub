import pathlib
import sys
from copy import copy
from unittest.mock import MagicMock

import pytest

RESOURCES = (pathlib.Path(".").parent / "src").absolute()


@pytest.fixture
def settings_mod():
    orig_sys_path = copy(sys.path)
    sys.path.append(str(RESOURCES))
    from resources.lib import settings

    yield settings
    sys.path = orig_sys_path


@pytest.mark.parametrize("loc", ["ru", "nl"])
def test_settings_locs(monkeypatch, loc, settings_mod):
    addon_mock = MagicMock()
    addon_mock.getSetting = MagicMock(return_value=loc)
    addon_mock_class = MagicMock(return_value=addon_mock)
    monkeypatch.setattr(settings_mod.xbmcaddon, "Addon", addon_mock_class)
    settings = settings_mod.Settings()
    assert settings.loc == loc


@pytest.mark.parametrize("direction", ["asc", "desc"])
def test_settings_sorting_direction_param(monkeypatch, direction, settings_mod):
    addon_mock = MagicMock()
    addon_mock.getSetting = MagicMock(return_value=direction)
    addon_mock_class = MagicMock(return_value=addon_mock)
    monkeypatch.setattr(settings_mod.xbmcaddon, "Addon", addon_mock_class)
    settings = settings_mod.Settings()
    assert settings.sorting_direction_param == "" if direction == "asc" else "-"


@pytest.mark.parametrize(
    "xml, expected",
    [
        ("<video><playcountminimumpercent>95</playcountminimumpercent></video>", 95.0),
        ("<video><playcountminimumpercent> 80.5 </playcountminimumpercent></video>", 80.5),
        ("<video><playcountminimumpercent>abc</playcountminimumpercent></video>", 90),
        ("<video><playcountminimumpercent/></video>", 90),
        ("<video/>", 90),
    ],
)
def test_settings_advanced_numbers(monkeypatch, tmp_path, xml, expected, settings_mod):
    advancedsettings = tmp_path / "advancedsettings.xml"
    advancedsettings.write_text(f"<advancedsettings>{xml}</advancedsettings>")
    monkeypatch.setattr(settings_mod.Settings, "advancedsettings_file", str(advancedsettings))
    value = settings_mod.Settings().advanced("video", "playcountminimumpercent")
    assert value == expected
    # the values are compared with numbers in listitem.py / player.py
    assert 100 * 700 / 2500 <= value
