#!/usr/bin/env bash

ROOTDIR="$(dirname $0)"
PKGSDIR="rbackupd"
TESTDIR="test"

failed=0

test_tox() {
    tox
}

test_pep8() {
    pep8 "$ROOTDIR/$PKGSDIR" "$ROOTDIR/$TESTDIR" \
        --filename="*.py" \
        --count \
        --ignore=E203,E241 \
        --max-line-length=80 \
        --exclude=.ropeproject
}

test_tox && { echo "tox: OK" ; } || { echo "tox: FAILED" ; failed=1 ; }
test_pep8 && { echo "pep8: OK" ; } || { echo "pep8: FAILED" ; failed=1 ; }

[[ $failed == 0 ]] && echo "All tests passed." || echo "Tests failed."

exit $failed
