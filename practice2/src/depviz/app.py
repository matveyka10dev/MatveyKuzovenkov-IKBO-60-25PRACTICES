"""Точка входа приложения."""

import sys

from depviz.config import PROG_NAME, format_config, parse_args
from depviz.validation import ConfigError, validate_config

STATUS_OK = 0
STATUS_CONFIG_ERROR = 2


def main(argv=None):
    """Запустить инструмент.

    Порядок работы: разбор опций командной строки, проверка значений,
    вывод всех параметров в формате ключ-значение. При ошибке в опциях
    выводится сообщение в поток ошибок и возвращается код 2 (как при
    синтаксических ошибках argparse).

    :param argv: опции командной строки (по умолчанию sys.argv[1:]).
    :return: код завершения процесса.
    """
    config = parse_args(argv)
    try:
        validate_config(config)
    except ConfigError as exc:
        sys.stderr.write("{}: error: {}\n".format(PROG_NAME, exc))
        return STATUS_CONFIG_ERROR
    for line in format_config(config):
        print(line)
    return STATUS_OK
