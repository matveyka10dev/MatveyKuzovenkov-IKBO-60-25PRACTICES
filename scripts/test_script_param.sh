#!/bin/sh
# Параметр --script: стартовые скрипты эмулятора.
cd "$(dirname "$0")/.." || exit 1
run() { echo "\$ ./run.sh $*"; ./run.sh "$@" < /dev/null; echo "[exit code: $?]"; echo; }
run --script examples/scripts/stage2_ok.txt
run --script examples/scripts/stage2_error.txt
run --script examples/scripts/stage2_exit.txt
