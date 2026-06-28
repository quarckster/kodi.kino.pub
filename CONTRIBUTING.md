# How to develop on this project

kodi.kino.pub welcomes contributions from the community.

The code is written to be compatible with Python 3.8. Development can be done with more modern
Python.

## Setting up your own fork of this repo

* on github interface click on `Fork` button.
* clone your fork of this repo: `git clone git@github.com:YOUR_GIT_USERNAME/kodi.kino.pub.git`
* enter the directory: `cd kodi.kino.pub`
* add upstream repo: `git remote add upstream https://github.com/quarckster/kodi.kino.pub`

## Install development dependencies

This project uses [uv](https://docs.astral.sh/uv/) to manage the development environment. After
[installing uv](https://docs.astral.sh/uv/getting-started/installation/), run `uv sync` to create a
virtual environment and install the development dependencies pinned in `uv.lock`. You also need
[`podman`](https://podman.io) to run the integration tests.

## Run the tests to ensure everything is working

Run `uv run pytest` (or `uv run make test_unit` / `uv run make test_integration`).

## Create a new branch to work on your contribution

Run `git checkout -b <BRANCH NAME>`.

## Make your changes

Edit the files using your preferred editor.

## Run pre-commit

`uv run pre-commit run --all`

## Test your changes

Run `uv run pytest` to test your changes.

## Push your changes to your fork

Run `git push origin <BRANCH NAME>`.

## Submit a pull request

On Github interface, click on `Pull Request` button.

Wait CI to run and the maintainer will review your PR.
