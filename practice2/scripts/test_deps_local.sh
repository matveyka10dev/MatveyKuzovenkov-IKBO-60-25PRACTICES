#!/bin/sh
# Прямые зависимости из локального репозитория Maven (без интернета).
# Репозиторий examples/maven-repo раздаётся встроенным HTTP-сервером
# Python на время работы скрипта.
cd "$(dirname "$0")/.." || exit 1
PORT=8765
REPO_URL="http://127.0.0.1:$PORT"
python3 -m http.server "$PORT" --bind 127.0.0.1 \
    --directory examples/maven-repo > /dev/null 2>&1 &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2> /dev/null' EXIT
sleep 1
run() { echo "\$ ./run.sh $*"; ./run.sh "$@"; echo "[exit code: $?]"; echo; }
run --package junit:junit:4.13.2 --repo "$REPO_URL"
run --package junit:junit --repo "$REPO_URL"
run --package org.example:demo-app --repo "$REPO_URL"
run --package org.example:demo-app:1.0.0 --repo "$REPO_URL"
run --package org.hamcrest:hamcrest-library:1.3 --repo "$REPO_URL"
run --package org.example:no-deps:1.0 --repo "$REPO_URL"
