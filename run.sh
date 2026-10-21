#!/bin/sh
# Запуск эмулятора: ./run.sh [параметры эмулятора]
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" \
    exec python3 -m shell_emu "$@"
