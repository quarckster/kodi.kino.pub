import os
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
KODI_VERSION = os.getenv("KODI_VERSION", "20")
KODI_IMAGE = f"ghcr.io/quarckster/conkodi:{KODI_VERSION}"


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: test drives a running Kodi container over JSON-RPC"
    )


def pytest_collection_modifyitems(items):
    # Any test that needs the `kodi` fixture (directly or transitively) talks to a
    # real Kodi container, so mark it as an integration test. This lets the unit
    # and integration suites be selected with `-m "not integration"` / `-m integration`.
    for item in items:
        if "kodi" in getattr(item, "fixturenames", ()):
            item.add_marker("integration")


@pytest.fixture(scope="session")
def build_plugin():
    shutil.copytree("src", f"{HOST_DIR}/addons/video.kino.pub")
    with open(f"{HOST_DIR}/addons/video.kino.pub/addon.xml", "r+") as addon_xml:
        content = addon_xml.read()
        content = content.replace("${VERSION}", "4.99")
        addon_xml.seek(0)
        addon_xml.write(content)
        # The replacement shortens the file, so truncate the leftover bytes.
        # Otherwise stale trailing text (e.g. "ddon>") survives after </addon>;
        # Kodi 22's stricter TinyXML2 rejects it (XML_ERROR_PARSING_TEXT) and the
        # add-on fails to load, while Kodi 20/21 tolerated the trailing junk.
        addon_xml.truncate()
    yield
    shutil.rmtree(f"{HOST_DIR}/addons/video.kino.pub")


@pytest.fixture(scope="session")
def run_kodi_pod(build_plugin):
    # The Kodi container runs as a non-root, rootless-mapped user and must be able to
    # write the bind-mounted databases/settings (otherwise it aborts on boot with
    # "SqliteDatabase ... is read only"). Running chmod inside `podman unshare` fixes
    # the permissions in the user namespace, which also covers files left over from a
    # previous run (owned by a mapped sub-uid). This replaces a manual/CI chmod step.
    podman("unshare", "chmod", "-R", "a+rwX", HOST_DIR)
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
        KODI_IMAGE,
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
    yield
    podman("pod", "stop", "kodipod")


def _jsonrpc_ready(kodi):
    return kodi.JSONRPC.Ping().get("result") == "pong"


@pytest.fixture(scope="session")
def kodi(run_kodi_pod):
    wait_for(
        urlopen,
        func_args=[f"{MOCKSERVER_URL}/"],
        timeout=60,
        handle_exception=True,
    )
    kodi = Kodi(JSON_RPC_URL)
    # Wait until the JSON-RPC API actually answers a request, not just until the
    # web server binds the port -- Kodi 20+ accepts connections well before it has
    # finished starting. (The conkodi image also drops the version-check service,
    # whose startup call to kodi.tv hangs in the isolated pod and otherwise wedges
    # the web server.)
    wait_for(_jsonrpc_ready, func_args=[kodi], timeout=90, handle_exception=True, delay=1)
    # Enable the add-on at runtime instead of relying on a pre-seeded Addons
    # database. The Addons schema version can differ between Kodi releases, so
    # this keeps the suite working across Kodi 20/21/22 without per-version DBs.
    wait_for(
        kodi.Addons.SetAddonEnabled,
        func_kwargs={"addonid": "video.kino.pub", "enabled": True},
        timeout=30,
        handle_exception=True,
    )
    return kodi
