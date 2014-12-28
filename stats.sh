#!/usr/bin/env bash

all_lines="$(cat $(find rbackupd/ -name '*.py'))"
wc -l $(find rbackupd/ -name "*.py") | sort -gr
echo
echo "SLOC:            $(cat $(find rbackupd/ -name '*.py') | grep -v '^[[:space:]]*$' | grep -v '^[[:space:]]*#.*$' | wc -l)"
echo "Blank lines:     $(cat $(find rbackupd/ -name '*.py') | grep '^[[:space:]]*$' | wc -l)"
echo "Comment lines:   $(cat $(find rbackupd/ -name '*.py') | grep '^[[:space:]]*#.*$' | wc -l)"
echo "Lines overall:   $(cat $(find rbackupd/ -name '*.py') | wc -l)"

echo "All files:       $(find . ! -wholename "*/build/*" ! -wholename "*/__pycache__/*" ! -wholename "*/.*" -type f | xargs cat | wc -l)"
