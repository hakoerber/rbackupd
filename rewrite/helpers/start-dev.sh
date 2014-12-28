#!/usr/bin/env bash

scriptpath="$(dirname "$0")"
PYTHONPATH="${scriptpath}/../lib" \
    "${scriptpath}/../scripts/rbackupd" \
    --config="${scriptpath}/../conf/rbackupd.yml" "$@"
