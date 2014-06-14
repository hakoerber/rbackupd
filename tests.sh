#!/usr/bin/env bash

ROOTDIR="$(dirname $0)"
PKGSDIR="rbackupd"
PKGSDIR2="rbackupc"
TESTDIR="test"

failed=0

test_tox() {
    tox
}

test_pep8() {
    pep8 "$ROOTDIR/$PKGSDIR" "$ROOTDIR/$TESTDIR" "$ROOTDIR/$PKGSDIR2" \
        --filename="*.py" \
        --count \
        --ignore=E203,E241 \
        --max-line-length=80 \
        --exclude=.ropeproject
}

test_todo() {
    ! grep -r 'TODO' "$ROOTDIR/$PKGSDIR" "$ROOTDIR/$TESTDIR" "$ROOTDIR/$PKGSDIR2"
}

test_debug() {
    ! grep -r 'pdb' "$ROOTDIR/$PKGSDIR" "$ROOTDIR/$TESTDIR" "$ROOTDIR/$PKGSDIR2"
}

if [[ "$1" == "tox" ]] || [[ -z "$1" ]] ; then
    test_tox && { echo "tox: OK" ; } || { echo "tox: FAILED" ; failed=1 ; }
fi

if [[ "$1" == "pep8" ]] || [[ -z "$1" ]] ; then
    test_pep8 && { echo "pep8: OK" ; } || { echo "pep8: FAILED" ; failed=1 ; }
fi

if [[ "$1" == "pytest" ]] ; then
    py.test "$(dirname $0)/test/" --strict ; failed=$?
fi

test_debug && { : ; } || { echo "debug symbols found! FAILED" ; failed=1 ; }

[[ $failed == 0 ]] && echo "All tests passed." || echo "Tests failed."

exit $failed
