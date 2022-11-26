# How to develop on this project

kodi.kino.opub welcomes contributions from the community.

You need PYTHON>=3.6!

## Setting up your own fork of this repo

* on github interface click on `Fork` button.
* clone your fork of this repo: `git clone git@github.com:YOUR_GIT_USERNAME/kodi.kino.pub.git`
* enter the directory: `cd kodi.kino.pub`
* add upstream repo: `git remote add upstream https://github.com/quarckster/kodi.kino.pub`

## Setting up your own virtual environment

Run `python3 -m venv <PATH>` to create a virtual environment. Then activate it with
`source <PATH>/bin/activate`.

## Install development dependencies

Run `pip install -r requirements_dev.txt` to install python development dependencies. You also need
(`podman`)[https://podman.io] to run tests.

## Run the tests to ensure everything is working

Run `pytest` to run the tests.

## Create a new branch to work on your contribution

Run `git checkout -b <BRANCH NAME>`.

## Make your changes

Edit the files using your preferred editor.

## Run pre-commit

`pre-commit run --all`

## Test your changes

Run `pytest` to test your changes.

## Push your changes to your fork

Run `git push origin <BRANCH NAME>`.

## Submit a pull request

On Github interface, click on `Pull Request` button.

Wait CI to run and the maintainer will review your PR.
