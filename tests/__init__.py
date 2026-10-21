"""Модульные тесты эмулятора.

При импорте пакета каталог ``src`` добавляется в ``sys.path``,
поэтому тесты запускаются из корня репозитория командой
``python3 -m unittest discover -s tests -t . -v``.
"""

import os
import sys

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                       "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
