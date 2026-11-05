#!/bin/sh
# Ошибки параметра --package.
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
run --repo examples/repos/simple.txt
run --package
run --package ''
run --package junit
run --package 'org.junit:junit 4'
run --package org.junit:junit:4.13:extra
run --test-mode --repo examples/repos/simple.txt --package a
run --test-mode --repo examples/repos/simple.txt --package org.junit:junit
run --package A --package B
