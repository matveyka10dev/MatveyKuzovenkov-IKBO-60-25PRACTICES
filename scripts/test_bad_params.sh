#!/bin/sh
# Ошибочные параметры командной строки.
cd "$(dirname "$0")/.." || exit 1
run() { echo "\$ ./run.sh $*"; ./run.sh "$@" < /dev/null; echo "[exit code: $?]"; echo; }
run --help
run --unknown
run --vfs
run --script no/such/script.txt
