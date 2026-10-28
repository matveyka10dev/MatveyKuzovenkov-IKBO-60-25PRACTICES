#!/bin/sh
# Обработка ошибок: каждый скрипт останавливается на первой ошибке.
cd "$(dirname "$0")/.." || exit 1
run() { echo "\$ ./run.sh $*"; ./run.sh "$@" < /dev/null; echo "[exit code: $?]"; echo; }
for file in examples/scripts/errors/*.txt; do
    run --vfs examples/vfs/deep.csv --script "$file"
done
