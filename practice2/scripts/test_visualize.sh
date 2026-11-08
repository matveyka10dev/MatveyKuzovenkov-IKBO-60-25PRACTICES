#!/bin/sh
# Визуализация трёх пакетов: Graphviz, изображение и ASCII-дерево.
# Каждый запуск открывает изображение графа.
cd "$(dirname "$0")/.." || exit 1
run() { echo "\$ ./run.sh $*"; ./run.sh "$@"; echo "[exit code: $?]"; echo; }
run --test-mode --repo examples/repos/simple.txt --package A
run --test-mode --repo examples/repos/cycles.txt --package A
run --test-mode --repo examples/repos/names.txt --package APP
run --test-mode --repo examples/repos/simple.txt --package A --ascii-tree
run --test-mode --repo examples/repos/cycles.txt --package A --ascii-tree
run --test-mode --repo examples/repos/names.txt --package APP --ascii-tree
