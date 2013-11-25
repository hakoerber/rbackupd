#!/usr/bin/env bash
# This script runs all tests in ./tests, and adds ./src to PYTHONPATH
# before doing so.

retval=0

ROOTDIR="$(dirname $0)"
TESTDIR="tests"
PKGSDIR="rbackupd"

TESTPATTERN='test_*.py'

PYTHONPATH="$ROOTDIR/$PKGSDIR" \
python -m unittest discover \
--start-directory "$ROOTDIR/$TESTDIR" \
--pattern "$TESTPATTERN" \
--top-level-directory "$ROOTDIR"

retval=$?

pep8 "$ROOTDIR/$PKGSDIR" "$ROOTDIR/$TESTDIR" --filename="*.py" --count
[[ $? != 0 ]] && retval=10 || echo "pep8: OK"

[[ $retval == 0 ]] && echo "All tests passed." || echo "Tests failed."
exit $retval
