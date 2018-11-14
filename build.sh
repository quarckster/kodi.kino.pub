#!/bin/bash

if [[ $# -eq 1 ]]; then
    VERSION=$1
elif [[ -d .git ]]; then
    VERSION=`git tag --sort=committerdate -l | tail -n1`
elif [[ $# -eq 0 ]]; then
    echo "Current directory is not a git repository."
    echo "Provide a version as an argument."
    exit 1
fi

DIR=video.kino.pub-$VERSION

mkdir $DIR
echo "Copying the files to a temporary directory"
echo "=========================================="
VERSION=$VERSION envsubst < addon.xml > $DIR/addon.xml
rsync -rv --exclude=*.pyc resources addon.py LICENSE $DIR
echo
echo "Creating the addon archive"
echo "=========================="
zip -rv -9 -m $DIR.zip $DIR
