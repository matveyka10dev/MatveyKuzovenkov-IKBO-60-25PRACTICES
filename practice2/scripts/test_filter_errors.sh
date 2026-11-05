#!/bin/sh
# Ошибки параметра --filter.
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
run --package org.junit:junit --filter
run --package org.junit:junit --filter ''
run --package org.junit:junit --filter 'ham crest'
run --package org.junit:junit --filter junit
run --test-mode --repo examples/repos/simple.txt --package ABC --filter B
run --package org.junit:junit --filter a --filter b
