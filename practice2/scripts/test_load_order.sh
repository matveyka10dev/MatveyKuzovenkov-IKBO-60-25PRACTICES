#!/bin/sh
# Порядок загрузки зависимостей в тестовых репозиториях.
cd "$(dirname "$0")/.." || exit 1
run() { echo "\$ ./run.sh $*"; ./run.sh "$@"; echo "[exit code: $?]"; echo; }
run --test-mode --repo examples/repos/simple.txt --package A --load-order
run --test-mode --repo examples/repos/cycle.txt --package A --load-order
run --test-mode --repo examples/repos/cycles.txt --package A --load-order
run --test-mode --repo examples/repos/names.txt --package APP --load-order
run --test-mode --repo examples/repos/names.txt --package APP --filter T --load-order
run --test-mode --repo examples/repos/missing.txt --package A --load-order
