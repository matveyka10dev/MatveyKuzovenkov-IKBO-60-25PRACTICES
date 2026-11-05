#!/bin/sh
# Корректные параметры: все опции, короткие формы, любой порядок.
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
run --package org.junit:junit:4.13.2
run --package com.google.guava:guava
run -p org.slf4j:slf4j-api:2.0.9 -r https://repo.maven.apache.org/maven2 -a
run --package=org.junit:junit:4.13.2 --repo=https://repo.maven.apache.org/maven2 --filter=hamcrest
run --test-mode --repo examples/repos/simple.txt --package A
run -t -a -f E -r examples/repos/simple.txt -p A
