import shutil
import subprocess
from urllib.request import urlopen

import pytest
from kodijson import Kodi
from paths import CON_DIR
from paths import HOST_DIR
from wait_for import wait_for


JSON_RPC_URL = "http://127.0.0.1:8080/jsonrpc"


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
            "--detach",
            "--name=kodi",
            "--umask=0002",
            f"--volume={HOST_DIR}/addons/:{CON_DIR}/addons",
            f"--volume={HOST_DIR}/Database/:{CON_DIR}/userdata/Database",
            f"--volume={HOST_DIR}/addon_data/:{CON_DIR}/userdata/addon_data/video.kino.pub/",
            "--publish=5999:5999",
            "--publish=8080:8080",
            "quay.io/quarck/conkodi:19",
        ],
        stdout=subprocess.DEVNULL,
    )
    yield
    subprocess.run(["podman", "stop", "kodi"], stdout=subprocess.DEVNULL)


@pytest.fixture(scope="session")
def kodi(run_conkodi):
    wait_for(urlopen, func_args=[JSON_RPC_URL], timeout=60, handle_exception=True)
    return Kodi(JSON_RPC_URL)
