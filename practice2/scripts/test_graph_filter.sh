#!/bin/sh
# Фильтрация пакетов по подстроке в тестовом репозитории.
cd "$(dirname "$0")/.." || exit 1
run() { echo "\$ ./run.sh $*"; ./run.sh "$@"; echo "[exit code: $?]"; echo; }
run --test-mode --repo examples/repos/simple.txt --package A --filter C
run --test-mode --repo examples/repos/cycle.txt --package A --filter B
run --test-mode --repo examples/repos/cycles.txt --package A --filter E
run --test-mode --repo examples/repos/names.txt --package APP --filter LO
run --test-mode --repo examples/repos/names.txt --package APP --filter T
run --test-mode --repo examples/repos/names.txt --package APP --filter O
run --test-mode --repo examples/repos/names.txt --package WEB --filter ON
