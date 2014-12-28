#!/usr/bin/env bash
cd "$(dirname "$0")/doc/sphinx/"
make html
xdg-open ./build/html/index.html
