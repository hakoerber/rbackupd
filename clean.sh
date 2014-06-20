#!/usr/bin/env bash

cd $(dirname $0)

rm -rf ./build/
rm -rf ./doc/sphinx/build/
rm -rf ./dist/
rm -rf ./rbackupd.egg-info/
rm -rf ./.tox/log/
rm -rf ./.tox/*/log/
find . -name '*.py[co]' -delete
