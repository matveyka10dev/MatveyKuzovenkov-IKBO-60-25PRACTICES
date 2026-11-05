#!/bin/sh
# Справка, неизвестные опции и лишние аргументы.
cd "$(dirname "$0")/.." || exit 1
show() {
    line="\$ ./run.sh"
    for arg in "$@"; do
        case $arg in
            ""|*" "*) line="$line '$arg'" ;;
            *) line="$line $arg" ;;
        esac
    done
    echo "$line"
}
run() { show "$@"; ./run.sh "$@"; echo "[exit code: $?]"; echo; }
run --help
run 
run --package org.junit:junit --unknown
run --package org.junit:junit extra
