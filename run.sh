#!/usr/bin/env bash
dir="$(dirname $0)"
PYTHONPATH="$dir:$PYTHONPATH" python "$dir/scripts/rbackupd" $*
