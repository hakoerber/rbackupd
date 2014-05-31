#!/usr/bin/env bash
dir="$(dirname $0)"
PYTHONPATH="$dir:$PYTHONPATH" "$dir/scripts/rbackupd" $@
