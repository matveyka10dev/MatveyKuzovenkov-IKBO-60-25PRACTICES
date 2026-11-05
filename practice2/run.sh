#!/bin/sh
# Запуск инструмента: ./run.sh [опции]
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" \
    exec python3 -m depviz "$@"
