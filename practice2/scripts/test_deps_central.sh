#!/bin/sh
# Прямые зависимости реальных пакетов из Maven Central (нужен интернет).
cd "$(dirname "$0")/.." || exit 1
run() { echo "\$ ./run.sh $*"; ./run.sh "$@"; echo "[exit code: $?]"; echo; }
run --package junit:junit:4.13.2
run --package com.google.guava:guava:33.0.0-jre
run --package org.apache.commons:commons-lang3:3.14.0
run --package org.slf4j:slf4j-api
run --package org.springframework:spring-core:6.1.4 --repo https://repo.maven.apache.org/maven2
run --package org.example:no-such-package:1.0
