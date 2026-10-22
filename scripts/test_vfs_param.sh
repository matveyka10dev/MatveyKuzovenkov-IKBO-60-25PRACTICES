#!/bin/sh
# Параметр --vfs: путь к физическому расположению VFS.
cd "$(dirname "$0")/.." || exit 1
run() { echo "\$ ./run.sh $*"; ./run.sh "$@" < /dev/null; echo "[exit code: $?]"; echo; }
run --vfs examples/vfs/minimal.csv
run --vfs=examples/vfs/deep.csv
