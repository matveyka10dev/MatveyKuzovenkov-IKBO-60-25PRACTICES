#!/bin/sh
# Ошибки флагов --test-mode и --ascii-tree.
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
run --package A --repo examples/repos/simple.txt --test-mode=yes
run --package A --repo examples/repos/simple.txt --test-mode --test-mode
run --package A --repo examples/repos/simple.txt -tt
run --package org.junit:junit --ascii-tree=on
run --package org.junit:junit --ascii-tree --ascii-tree
run --package org.junit:junit -a 1
