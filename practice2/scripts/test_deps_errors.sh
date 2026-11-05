#!/bin/sh
# Ошибки получения зависимостей: нет пакета, неверный POM, сеть.
cd "$(dirname "$0")/.." || exit 1
PORT=8765
REPO_URL="http://127.0.0.1:$PORT"
python3 -m http.server "$PORT" --bind 127.0.0.1 \
    --directory examples/maven-repo > /dev/null 2>&1 &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2> /dev/null' EXIT
sleep 1
run() { echo "\$ ./run.sh $*"; ./run.sh "$@"; echo "[exit code: $?]"; echo; }
run --package org.example:ghost:1.0 --repo "$REPO_URL"
run --package org.example:ghost --repo "$REPO_URL"
run --package org.example:no-versions --repo "$REPO_URL"
run --package org.example:broken-xml:1.0 --repo "$REPO_URL"
run --package org.example:not-a-pom:1.0 --repo "$REPO_URL"
run --package org.example:orphan:1.0 --repo "$REPO_URL"
run --package org.example:cycle-a:1.0 --repo "$REPO_URL"
run --package junit:junit --repo http://127.0.0.1:1
run --package junit:junit --repo http://no-such-host.invalid/maven2
