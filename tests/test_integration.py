import shutil
import subprocess
from pathlib import Path
from urllib.request import urlopen

import pytest
from expected_results import ACTIVATED_HOME
from expected_results import NONACTIVATED_HOME
from kodijson import Kodi
from wait_for import wait_for


JSON_RPC_URL = "http://127.0.0.1:8080/jsonrpc"
HOST_DIR = f"{Path('.').absolute()}/tests/data"
CON_DIR = "/home/kodi/.kodi"


@pytest.fixture(scope="session")
def build_plugin():
    shutil.copytree("src", f"{HOST_DIR}/addons/video.kino.pub")
    with open(f"{HOST_DIR}/addons/video.kino.pub/addon.xml", "r+") as addon_xml:
        content = addon_xml.read()
        content = content.replace("${VERSION}", "3.99")
        addon_xml.seek(0)
        addon_xml.write(content)
    yield
    shutil.rmtree(f"{HOST_DIR}/addons/video.kino.pub")


@pytest.fixture(scope="session")
def run_conkodi(build_plugin):
    subprocess.run(["podman", "rm", "-f", "kodi"], stdout=subprocess.DEVNULL)
    subprocess.run(
        [
            "podman",
            "run",
            "--name",
            "kodi",
            "-d",
            "--rm",
            "-v",
            f"{HOST_DIR}/addons/:{CON_DIR}/addons",
            "-v",
            f"{HOST_DIR}/Database/:{CON_DIR}/userdata/Database",
            "-v",
            f"{HOST_DIR}/addon_data/:{CON_DIR}/userdata/addon_data/video.kino.pub/",
            "-p",
            "5999:5999",
            "-p",
            "8080:8080",
            "--userns=keep-id",
            "quay.io/quarck/conkodi:19",
        ],
        stdout=subprocess.PIPE,
    )
    yield
    subprocess.run(["podman", "stop", "kodi"], stdout=subprocess.DEVNULL)


@pytest.fixture(scope="session")
def kodi(run_conkodi):
    wait_for(lambda: urlopen(JSON_RPC_URL), timeout=60, handle_exception=True)
    return Kodi(JSON_RPC_URL)


def test_home_activated(kodi):
    resp = kodi.Files.GetDirectory(directory="plugin://video.kino.pub")
    assert ACTIVATED_HOME == resp["result"]["files"]


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
    assert NONACTIVATED_HOME == resp["result"]["files"]
