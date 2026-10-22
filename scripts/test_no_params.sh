#!/bin/sh
# Запуск без параметров: оба параметра не заданы.
cd "$(dirname "$0")/.." || exit 1
run() { echo "\$ ./run.sh $*"; ./run.sh "$@" < /dev/null; echo "[exit code: $?]"; echo; }
run
