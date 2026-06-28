import pathlib
import sys
from copy import copy
from unittest.mock import MagicMock

import pytest


RESOURCES = (pathlib.Path(".").parent / "src").absolute()


@pytest.fixture
def client_mod(monkeypatch):
    orig_sys_path = copy(sys.path)
    sys.path.append(str(RESOURCES))
    for name in ("xbmc", "xbmcgui", "xbmcaddon", "socks"):
        monkeypatch.setitem(sys.modules, name, MagicMock())
    sys.modules.pop("resources.lib.utils", None)
    sys.modules.pop("resources.lib.client", None)
    from resources.lib import client

    yield client
    sys.path = orig_sys_path


def _request():
    request = MagicMock()
    request.recursion_counter_401 = 0
    request.recursion_counter_429 = 0
    return request


def test_http_error_401_refreshes_token_and_retries(client_mod):
    plugin = MagicMock()
    plugin.settings.access_token = "fresh_token"
    processor = client_mod.KinoApiErrorProcessor(plugin)
    processor.parent = MagicMock()
    request = _request()

    result = processor.http_error_401(request, MagicMock(), 401, "msg", {})

    plugin.auth.get_token.assert_called_once_with()
    processor.parent.open.assert_called_once()
    assert result is processor.parent.open.return_value
    assert request.recursion_counter_401 == 1


def test_http_error_401_gives_up_after_one_retry(client_mod):
    plugin = MagicMock()
    processor = client_mod.KinoApiErrorProcessor(plugin)
    request = _request()
    request.recursion_counter_401 = 1

    with pytest.raises(SystemExit):
        processor.http_error_401(request, MagicMock(), 401, "msg", {})


def test_http_error_401_exits_when_token_is_empty(client_mod):
    plugin = MagicMock()
    plugin.settings.access_token = ""
    processor = client_mod.KinoApiErrorProcessor(plugin)
    processor.parent = MagicMock()

    with pytest.raises(SystemExit):
        processor.http_error_401(_request(), MagicMock(), 401, "msg", {})


def test_http_error_429_retries_after_sleeping(client_mod):
    plugin = MagicMock()
    processor = client_mod.KinoApiErrorProcessor(plugin)
    processor.parent = MagicMock()
    request = _request()

    result = processor.http_error_429(request, MagicMock(), 429, "msg", {})

    client_mod.xbmc.sleep.assert_called_once_with(5000)
    processor.parent.open.assert_called_once()
    assert result is processor.parent.open.return_value
    assert request.recursion_counter_429 == 1


def test_http_error_429_gives_up_after_recursion_limit(client_mod):
    plugin = MagicMock()
    processor = client_mod.KinoApiErrorProcessor(plugin)
    request = _request()
    request.recursion_counter_429 = 3

    with pytest.raises(SystemExit):
        processor.http_error_429(request, MagicMock(), 429, "msg", {})


def test_http_error_default_logs_and_exits(client_mod):
    plugin = MagicMock()
    handler = client_mod.KinoApiDefaultErrorHandler(plugin)

    with pytest.raises(SystemExit):
        handler.http_error_default(MagicMock(), MagicMock(), 500, "msg", {})

    plugin.logger.fatal.assert_called_once()
