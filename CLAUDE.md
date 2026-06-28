# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Kodi 20+ video add-on for the kino.pub online movie service (the 4.x.x series supports Kodi 20, 21,
and 22; for Kodi 19 use 3.x.x). The runtime is Kodi's embedded Python: modules like `xbmc`,
`xbmcaddon`, `xbmcgui`, `xbmcplugin`, `xbmcvfs` are provided by Kodi itself (stubbed via `Kodistubs`
for local dev / type-checking, not real pip packages). Add-on source under `src/` must stay **Python
3.8 compatible**; dev tooling and tests run on Python 3.10. Video metadata is set through the
`InfoTagVideo` setters (Kodi 20+), not the deprecated `ListItem.setInfo()`.

## Commands

Setup: `pip install -r requirements_dev.txt` (and install [`podman`](https://podman.io) for
integration tests).

- **Lint / format / type-check:** `pre-commit run --all` (black @ line-length 100, flake8, mypy,
  reorder-python-imports, pyupgrade).
- **Unit tests:** `make test_unit` → `pytest -v tests/test_unit.py`. These mock `xbmc*` and need no
  containers.
- **Integration tests:** `make test_integration` → `pytest -v -k "(not test_unit)"`. Requires podman;
  spins up real Kodi + a mock API server (see Testing below). CI runs these against Kodi 19 and 20.
- **Single test:** `pytest tests/test_items.py::test_watching`.
- **Build add-on zip:** `make video_addon VERSION=4.99.0` (VERSION is required; substituted into
  `addon.xml`). `make repo VERSION=...` also builds the Kodi-repository structure. `make deploy`
  publishes to Netlify (needs `NETLIFY_*` env vars). Releases are normally driven by git tags via
  `.github/workflows/deploy.yaml`.

## Architecture

Kodi launches the add-on fresh on **every navigation action**, passing `sys.argv = [plugin_url,
handle, query_string]`. `src/addon.py` calls `plugin.run()`; there is no long-running process —
state that must survive between invocations is stashed in a Kodi window property (see Modeling).

**`Plugin` (`plugin.py`) is the central service-locator.** A single `plugin` instance (created in
`main.py`) parses `sys.argv` and wires together every subsystem: `settings`, `auth`, `logger`,
`routing`, `search_history`, `items` (the model factory), `client`, `proxy_settings`. Nearly every
other object holds a back-reference to `plugin` and reaches collaborators through it.

**Routing (`routing.py`) is a custom Flask-like router.** View functions in `main.py` are registered
with `@plugin.routing.route("/items/<content_type>/<heading>/")`. `Routing.dispatch` regex-matches
the incoming path and calls the matching view with captured kwargs. `build_url(...)` constructs
`plugin://` URLs that become directory item targets. Adding a screen = add a `@route`d function in
`main.py` that calls `xbmcplugin.addDirectoryItem(...)` / `endOfDirectory(...)`.

**API access (`client.py`).** `plugin.client("some/endpoint").get(data={...})` / `.post(...)` against
the kino.pub REST API. `KinoPubClient` builds a urllib opener with custom handlers that:
- inject the `Authorization: Bearer <access_token>` header,
- apply HTTP/SOCKS proxy settings read from **Kodi's system settings** via JSON-RPC
  (`xbmc_settings.py`),
- on **401** refresh the OAuth token and retry once, on **429** sleep and retry up to 3×.

**Auth (`auth.py`)** implements the OAuth2 **device-code flow** (show user a code + verification URL,
poll for token). Tokens are persisted through `Settings`.

**Modeling (`modeling.py`)** is the domain layer. `ItemsCollection` is a factory that turns API JSON
into model objects — `Movie`, `TVShow` (→ `Season` → `SeasonEpisode`), `Multi` (→ `Episode`) — chosen
via `CONTENT_TYPE_MAP` and the `subtype` field. Each model exposes `video_info`, `url`, and a
`list_item` (an `ExtendedListItem`). Key trick: because the add-on restarts each navigation, rendered
items are **pickled into the `10000` window property** `video.kino.pub-playback_data`
(`Plugin.set_window_property`). `instantiate_from_item_id` first tries that cache, only hitting the
API on a miss — this avoids refetching when the user clicks into an already-listed item.

**Playback (`player.py`).** `play` view sets a resolved URL and loops while a `Player(xbmc.Player)`
subclass receives playback callbacks. On stop/end it reports marktime / resume-point / watched status
back to the API, honoring Kodi's `advancedsettings.xml` thresholds (`ignoresecondsatstart`,
`playcountminimumpercent`, …) and sets Trakt scrobbling ids.

**Settings (`settings.py`).** `Settings.__getattr__`/`__setattr__` transparently proxy attribute
access to `xbmcaddon.Addon().getSetting/setSetting` (so `plugin.settings.access_token = "..."`
writes add-on settings). `show_*` attributes are eval'd to bool. `is_testing` (env `KINO_PUB_TEST`)
switches API base URLs between production and the local mock server.

**Localization.** All user-facing strings are numeric IDs resolved via `localize(32019)` →
`resources/language/resource.language.*/strings.po` (en_gb, ru_ru, uk_ua). Never hardcode UI text;
add a string id and translate it in all three `.po` files. Comments above `localize(...)` calls note
the English text for readers.

## Testing

Two distinct suites:
- **Unit** (`tests/test_unit.py`): import `resources.lib.*` with `xbmc*` mocked, assert pure logic.
- **Integration** (everything else): `conftest.py` copies `src/` into `tests/data/addons/`, then
  launches a podman **pod** with two containers — `quay.io/quarck/conkodi` (a headless real Kodi) and
  `mockserver` seeded from `tests/data/fake_api/persistedExpectations.json`. Tests drive Kodi over
  JSON-RPC (`kodijson.Kodi`) — e.g. `kodi.Files.GetDirectory(directory="plugin://video.kino.pub/...")`
  — and assert the returned directory listing equals a fixture in `tests/expected_results.py`. The
  add-on talks to the mock server because `KINO_PUB_TEST=1` is set in the container.

When you change rendering/listing behavior, the corresponding `expected_results.py` fixture usually
needs updating in lockstep. The `tests/data/Database/*.db` files and `addon_data/settings.xml` are
pre-seeded Kodi state (e.g. an existing `access_token`).

Import resolution across the repo uses application dirs `.:src:tests`, so both
`from resources.lib.foo import Bar` and `from paths import HOST_DIR` work.
