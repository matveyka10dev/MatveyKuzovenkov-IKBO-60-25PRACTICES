#!/bin/sh
# VFS: минимальный вариант (только корневой каталог).
cd "$(dirname "$0")/.." || exit 1
run() { echo "\$ ./run.sh $*"; ./run.sh "$@" < /dev/null; echo "[exit code: $?]"; echo; }
run --vfs examples/vfs/minimal.csv --script examples/scripts/vfs_minimal.txt
# Без параметра --vfs используется пустая VFS
run --script examples/scripts/vfs_minimal.txt
