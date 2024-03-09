import shutil
from urllib.request import urlopen

import pytest
from kodijson import Kodi
from wait_for import wait_for

from helpers import podman
from paths import CON_DIR
from paths import HOST_DIR


JSON_RPC_URL = "http://127.0.0.1:8080/jsonrpc"
MOCKSERVER_URL = "http://127.0.0.1:1080/v1"


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
def run_kodi_pod(build_plugin):
    podman("pod", "rm", "-f", "kodipod")
    podman(
        "pod",
        "create",
        "--publish=8080:8080",
        "--publish=1080:1080",
        "--publish=5999:5999",
        "--name=kodipod",
    )
    podman(
        "run",
        "--detach",
        "--pod=kodipod",
        "--name=kodi",
        "--umask=0002",
        "--env=KINO_PUB_TEST=1",
        f"--volume={HOST_DIR}/addons/:{CON_DIR}/addons",
        f"--volume={HOST_DIR}/Database/:{CON_DIR}/userdata/Database",
        f"--volume={HOST_DIR}/addon_data/:{CON_DIR}/userdata/addon_data/video.kino.pub",
        "quay.io/quarck/conkodi:19",
    )
    podman(
        "run",
        "--detach",
        "--pod=kodipod",
        "--name=mockserver",
        "--env=MOCKSERVER_INITIALIZATION_JSON_PATH=/fake_api/persistedExpectations.json",
        f"--volume={HOST_DIR}/fake_api/:/fake_api",
        "docker.io/mockserver/mockserver:mockserver-5.11.2",
    )
    podman(
        "run",
        "--detach",
        "--pod=kodipod",
        "--name=proxy",
        "docker.io/nadoo/glider:0.16",
        "-listen",
        ":8443",
        "-verbose",
    )
    yield
    podman("pod", "stop", "kodipod")


@pytest.fixture(scope="session")
def kodi(run_kodi_pod):
    wait_for(urlopen, func_args=[JSON_RPC_URL], timeout=10, handle_exception=True)
    wait_for(
        urlopen,
        func_args=[f"{MOCKSERVER_URL}/"],
        timeout=10,
        handle_exception=True,
    )
    return Kodi(JSON_RPC_URL)
