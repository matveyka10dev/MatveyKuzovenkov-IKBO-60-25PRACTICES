#!/bin/sh
# Все команды этапов 1-3 на VFS с глубокой вложенностью.
cd "$(dirname "$0")/.." || exit 1
run() { echo "\$ ./run.sh $*"; ./run.sh "$@" < /dev/null; echo "[exit code: $?]"; echo; }
run --vfs examples/vfs/deep.csv --script examples/scripts/stage3_all.txt
