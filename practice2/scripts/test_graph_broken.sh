#!/bin/sh
# Некорректные файлы тестового репозитория.
cd "$(dirname "$0")/.." || exit 1
run() { echo "\$ ./run.sh $*"; ./run.sh "$@"; echo "[exit code: $?]"; echo; }
run --test-mode --repo examples/repos/broken/bad_name.txt --package A
run --test-mode --repo examples/repos/broken/no_colon.txt --package A
run --test-mode --repo examples/repos/broken/duplicate_package.txt --package A
run --test-mode --repo examples/repos/broken/duplicate_dependency.txt --package A
run --test-mode --repo examples/repos/broken/empty.txt --package A
run --test-mode --repo examples/repos/broken/not_utf8.txt --package A
