"""Точка входа приложения."""

import sys

from depviz.config import PROG_NAME, parse_args
from depviz.graph import SourceError, build_graph
from depviz.image import ImageError, show_image
from depviz.report import format_dot, format_tree
from depviz.resolver import Resolver
from depviz.sources import MavenSource, TestRepoSource
from depviz.testrepo import TestRepoError, load_test_repo
from depviz.validation import ConfigError, validate_config

STATUS_OK = 0
STATUS_ERROR = 1
STATUS_CONFIG_ERROR = 2


def print_error(message):
    """Вывести сообщение об ошибке в поток ошибок.

    :param message: текст ошибки.
    """
    sys.stdout.flush()
    sys.stderr.write("{}: error: {}\n".format(PROG_NAME, message))


def make_source(config):
    """Создать источник данных о зависимостях по конфигурации.

    :param config: проверенная конфигурация.
    :return: TestRepoSource в тестовом режиме, иначе MavenSource.
    :raises TestRepoError: если файл тестового репозитория некорректен.
    """
    if config.test_mode:
        return TestRepoSource(load_test_repo(config.repo))
    return MavenSource(Resolver(config.repo))


def show_graph(config):
    """Построить граф, вывести его текст и изображение.

    На экран выводится описание графа на языке Graphviz, а с флагом
    ``--ascii-tree`` - ASCII-дерево зависимостей. Затем изображение
    графа открывается в программе просмотра.

    :param config: проверенная конфигурация.
    :return: код завершения.
    """
    try:
        source = make_source(config)
        graph = build_graph(source, config.package, config.name_filter)
    except (TestRepoError, SourceError) as exc:
        print_error(exc)
        return STATUS_ERROR
    dot_lines = format_dot(graph)
    lines = format_tree(graph) if config.ascii_tree else dot_lines
    for line in lines:
        print(line)
    try:
        show_image("\n".join(dot_lines) + "\n")
    except ImageError as exc:
        print_error(exc)
        return STATUS_ERROR
    return STATUS_OK


def main(argv=None):
    """Запустить инструмент.

    Порядок работы: разбор опций командной строки, проверка значений,
    построение графа зависимостей пакета, вывод его текста и
    изображения. Ошибка в опциях - код 2, ошибка получения данных о
    пакете или показа изображения - код 1.

    :param argv: опции командной строки (по умолчанию sys.argv[1:]).
    :return: код завершения процесса.
    """
    config = parse_args(argv)
    try:
        validate_config(config)
    except ConfigError as exc:
        print_error(exc)
        return STATUS_CONFIG_ERROR
    return show_graph(config)
