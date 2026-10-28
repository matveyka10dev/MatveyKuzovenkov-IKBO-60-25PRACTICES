#!/bin/sh
# VFS: несколько файлов (текст, многострочный текст, base64).
cd "$(dirname "$0")/.." || exit 1
run() { echo "\$ ./run.sh $*"; ./run.sh "$@" < /dev/null; echo "[exit code: $?]"; echo; }
run --vfs examples/vfs/files.csv --script examples/scripts/vfs_files.txt
# Такая же VFS, сохранённая в Excel: BOM, CRLF, разделитель ;
run --vfs examples/vfs/excel.csv --script examples/scripts/vfs_excel.txt
