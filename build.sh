#!/bin/bash

VERSION=`git tag -l | tail -n1`
DIR=video.kino.pub-$VERSION 

mkdir $DIR
cp -r resources addon.xml default.py icon.png $DIR
zip -r -9 -m $DIR.zip $DIR > /dev/null