"""Точка входа приложения."""

import sys

from depviz.config import PROG_NAME, parse_args
from depviz.maven import Coordinate
from depviz.resolver import ResolveError, Resolver
from depviz.validation import ConfigError, validate_config

STATUS_OK = 0
STATUS_ERROR = 1
STATUS_CONFIG_ERROR = 2
INDENT = "  "
NO_DEPENDENCIES = INDENT + "(no dependencies)"
TEST_MODE_NOTE = ("test mode: dependencies from a test repository file "
                  "are not supported yet")


def print_error(message):
    """Вывести сообщение об ошибке в поток ошибок.

    :param message: текст ошибки.
    """
    sys.stdout.flush()
    sys.stderr.write("{}: error: {}\n".format(PROG_NAME, message))


def format_dependencies(coordinate, dependencies):
    """Сформировать вывод списка прямых зависимостей.

    :param coordinate: координаты анализируемого пакета.
    :param dependencies: список Dependency.
    :return: список строк для вывода.
    """
    lines = ["Direct dependencies of {} ({}):".format(
        coordinate, len(dependencies))]
    if not dependencies:
        lines.append(NO_DEPENDENCIES)
    for dependency in dependencies:
        lines.append(INDENT + dependency.describe())
    return lines


def show_direct_dependencies(config):
    """Получить из репозитория и вывести прямые зависимости пакета.

    :param config: проверенная конфигурация.
    :return: код завершения.
    """
    resolver = Resolver(config.repo)
    try:
        coordinate, dependencies = resolver.direct_dependencies(
            Coordinate.parse(config.package))
    except ResolveError as exc:
        print_error(exc)
        return STATUS_ERROR
    for line in format_dependencies(coordinate, dependencies):
        print(line)
    return STATUS_OK


def main(argv=None):
    """Запустить инструмент.

    Порядок работы: разбор опций командной строки, проверка значений,
    получение и вывод прямых зависимостей пакета из репозитория Maven.
    Ошибка в опциях - код 2, ошибка получения зависимостей - код 1.

    :param argv: опции командной строки (по умолчанию sys.argv[1:]).
    :return: код завершения процесса.
    """
    config = parse_args(argv)
    try:
        validate_config(config)
    except ConfigError as exc:
        print_error(exc)
        return STATUS_CONFIG_ERROR
    if config.test_mode:
        print(TEST_MODE_NOTE)
        return STATUS_OK
    return show_direct_dependencies(config)
