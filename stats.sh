#!/usr/bin/env bash

all_lines="$(cat $(find src/ -name '*.py'))"
wc -l $(find src/ -name "*.py") | sort -gr
echo
echo "SLOC:            $(cat $(find src/ -name '*.py') | grep -v '^[[:space:]]*$' | grep -v '^[[:space:]]*#.*$' | wc -l)"
echo "Blank lines:     $(cat $(find src/ -name '*.py') | grep '^[[:space:]]*$' | wc -l)"
echo "Comment lines:   $(cat $(find src/ -name '*.py') | grep '^[[:space:]]*#.*$' | wc -l)"
echo "Lines overall:   $(cat $(find src/ -name '*.py') | wc -l)"
