#!/usr/bin/env bash

cd $(dirname $0)

rm -rf ./build/ 2>/dev/null
rm -rf ./doc/sphinx/build/ 2>/dev/null
rm -rf ./dist/ 2>/dev/null
rm -rf ./rbackupd.egg-info/ 2>/dev/null
rm -rf ./.tox/log/ 2>/dev/null
rm -rf ./.tox/*/log/ 2>/dev/null
find . -name '*.py[co]' -delete 2>/dev/null
