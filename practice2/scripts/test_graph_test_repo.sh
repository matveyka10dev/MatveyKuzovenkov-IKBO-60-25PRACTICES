#!/bin/sh
# Граф зависимостей в тестовом репозитории: ромб, циклы, глубина,
# отсутствующие пакеты.
cd "$(dirname "$0")/.." || exit 1
run() { echo "\$ ./run.sh $*"; ./run.sh "$@"; echo "[exit code: $?]"; echo; }
run --test-mode --repo examples/repos/simple.txt --package A
run --test-mode --repo examples/repos/cycle.txt --package A
run --test-mode --repo examples/repos/cycle.txt --package C
run --test-mode --repo examples/repos/self_cycle.txt --package A
run --test-mode --repo examples/repos/cycles.txt --package A
run --test-mode --repo examples/repos/cycles.txt --package D
run --test-mode --repo examples/repos/deep.txt --package A
run --test-mode --repo examples/repos/names.txt --package APP
run --test-mode --repo examples/repos/missing.txt --package A
run --test-mode --repo examples/repos/simple.txt --package Q
