#!/bin/sh
# VFS: некорректные CSV-файлы и отсутствующий файл.
cd "$(dirname "$0")/.." || exit 1
run() { echo "\$ ./run.sh $*"; ./run.sh "$@" < /dev/null; echo "[exit code: $?]"; echo; }
for file in examples/vfs/broken/*.csv; do
    run --vfs "$file"
done
run --vfs examples/vfs/no_such_file.csv
