#!/bin/bash

function check_version() {
    if [[ "$#" -eq 1 ]]; then
        VERSION="$1"
    elif [[ -d .git ]]; then
        VERSION=$(git tag --sort=committerdate -l | tail -n1)
    elif [[ "$#" -eq 0 ]]; then
        echo "Current directory is not a git repository."
        echo "Provide a version as an argument."
        exit 1
    fi
    DIR=video.kino.pub-"$VERSION"
}

function build() {
    check_version $1
    mkdir "$DIR"
    echo "Copying the files to a temporary directory"
    echo "=========================================="
    VERSION="$VERSION" envsubst < src/addon.xml > "$DIR"/addon.xml
    rsync -rv --exclude=*.pyc src/resources src/addon.py LICENSE "$DIR"
    echo
    echo "Creating the addon archive"
    echo "=========================="
    zip -rv -9 -m "$DIR".zip "$DIR"
}

function deploy() {
    build $1
    echo "Deploying files to Netlify"
    echo "=========================="
    mkdir -p repo.kino.pub repo/video.kino.pub
    VERSION="$VERSION" envsubst < repo_src/addons.xml > repo/addons.xml
    md5sum repo/addons.xml | cut -d " " -f 1 > repo/addons.xml.md5
    cp repo_src/addon.xml repo_src/icon.png repo.kino.pub/
    zip -rv -9 -m repo/repo.kino.pub.zip repo.kino.pub
    mv "$DIR".zip repo/video.kino.pub
    node_modules/netlify-cli/bin/run deploy --dir=repo --prod --auth="$NETLIFY_AUTH_TOKEN" --site="$NETLIFY_SITE_ID"
}

"$@"
