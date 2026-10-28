#!/bin/sh
# VFS: не менее 3 уровней вложенности файлов и каталогов.
cd "$(dirname "$0")/.." || exit 1
run() { echo "\$ ./run.sh $*"; ./run.sh "$@" < /dev/null; echo "[exit code: $?]"; echo; }
run --vfs examples/vfs/deep.csv --script examples/scripts/vfs_deep.txt
