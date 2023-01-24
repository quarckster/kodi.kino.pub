#!/bin/bash

function check_version() {
    if [[ ${#} -eq 1 ]]; then
        VERSION=${1}
    elif [[ -d .git ]]; then
        VERSION=$(git tag --sort=committerdate -l | tail -n1)
    elif [[ ${#} -eq 0 ]]; then
        echo "Current directory is not a git repository."
        echo "Provide a version as an argument."
        exit 1
    fi
    DIR=video.kino.pub-"${VERSION}"
}

function build_video_addon() {
    check_version "${1}"
    echo "Creating video.kino.pub add-on archive"
    echo "======================================"
    mkdir "$DIR"
    VERSION="$VERSION" envsubst < src/addon.xml > "$DIR"/addon.xml
    rsync -rv --exclude=*.pyc --exclude=__pycache__/ src/resources src/addon.py LICENSE "$DIR"
    zip -rv -9 -m "$DIR".zip "$DIR"
    echo
}

function build_repo_addon() {
    echo "Creating repo.kino.pub add-on archive"
    echo "====================================="
    mkdir repo.kino.pub
    cp repo_src/addon.xml repo_src/icon.png repo.kino.pub/
    zip -rv -9 -m repo.kino.pub.zip repo.kino.pub
    echo
}

function create_repo() {
    build_video_addon "${1}"
    build_repo_addon
    echo "Creating repository add-on directory structure"
    echo "=============================================="
    mkdir -p repo/video.kino.pub
    VERSION="${VERSION}" envsubst < repo_src/addons.xml > repo/addons.xml
    md5sum repo/addons.xml | cut -d " " -f 1 > repo/addons.xml.md5
    mv repo.kino.pub.zip repo/
    mv "${DIR}".zip repo/video.kino.pub/
    echo
}

function deploy() {
    create_repo "${1}"
    echo "Deploying files to Netlify"
    echo "=========================="
    podman run -t -e NETLIFY_AUTH_TOKEN -e NETLIFY_SITE_ID -v $(pwd):/mnt -w /mnt quay.io/quarck/netlify netlify deploy --dir=repo/ --prod
}

"$@"
