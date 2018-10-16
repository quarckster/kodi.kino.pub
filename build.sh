#!/bin/bash

if [[ -d .git ]]; then
    VERSION=`git tag -l | tail -n1`
elif [[ $# -eq 0 ]]; then
    echo "Current directory is not a git repository."
    echo "Provide a version as an argument."
    exit 1
else
    VERSION=$1
fi

DIR=video.kino.pub-$VERSION

mkdir $DIR
echo "Copying the files to a temporary directory"
echo "=========================================="
VERSION=$VERSION envsubst < addon.xml > $DIR/addon.xml
rsync -rv --exclude=*.pyc resources default.py icon.png $DIR
echo
echo "Creating the addon archive"
echo "=========================="
zip -rv -9 -m $DIR.zip $DIR
