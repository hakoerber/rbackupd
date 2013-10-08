# This script runs all tests in ./tests, and adds ./src to PYTHONPATH
# before doing so.

ROOTDIR="$(dirname $0)"
TESTDIR="tests"
PKGSDIR="src"

TESTPATTERN='test_*.py'

PYTHONPATH="$ROOTDIR/$PKGSDIR" \
python -m unittest discover \
--start-directory "$ROOTDIR/$TESTDIR" \
--pattern "$TESTPATTERN" \
--top-level-directory "$ROOTDIR"
