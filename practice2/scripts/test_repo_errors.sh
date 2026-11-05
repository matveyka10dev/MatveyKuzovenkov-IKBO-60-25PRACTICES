#!/bin/sh
# Ошибки параметра --repo.
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
run --package org.junit:junit --repo
run --package org.junit:junit --repo ''
run --package org.junit:junit --repo ftp://repo.example.com/maven2
run --package org.junit:junit --repo https:///maven2
run --package org.junit:junit --repo 'https://repo.example.com/my repo'
run --package org.junit:junit --repo examples/repos/simple.txt
run --package A --test-mode
run --package A --test-mode --repo https://repo1.maven.org/maven2
run --package A --test-mode --repo no/such/file.txt
run --package A --test-mode --repo examples/repos
run --package A --repo http://a.org --repo http://b.org
