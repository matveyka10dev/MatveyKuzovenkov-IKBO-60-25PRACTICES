#!/bin/sh
# Оба параметра одновременно, в разном порядке.
cd "$(dirname "$0")/.." || exit 1
run() { echo "\$ ./run.sh $*"; ./run.sh "$@" < /dev/null; echo "[exit code: $?]"; echo; }
run --vfs examples/vfs/minimal.csv --script examples/scripts/stage2_ok.txt
run --script examples/scripts/stage2_ok.txt --vfs examples/vfs/minimal.csv
