#!/usr/bin/env bash

all_lines="$(cat $(find -name '*.py'))"
wc -l $(find -name "*.py") | sort -gr
echo
echo "SLOC:            $(cat $(find -name '*.py') | grep -v '^[[:space:]]*$' | grep -v '^[[:space:]]*#.*$' | wc -l)"
echo "Blank lines:     $(cat $(find -name '*.py') | grep '^[[:space:]]*$' | wc -l)"
echo "Comment lines:   $(cat $(find -name '*.py') | grep '^[[:space:]]*#.*$' | wc -l)"
echo "Lines overall:   $(cat $(find -name '*.py') | wc -l)"
