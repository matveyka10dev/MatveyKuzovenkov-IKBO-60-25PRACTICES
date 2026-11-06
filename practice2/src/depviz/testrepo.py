"""Файл описания графа тестового репозитория.

Формат - текстовый файл UTF-8 (с BOM или без), по одному пакету на
строку::

    # комментарий
    A: B C      пакет A зависит от B и C
    B: D
    C: D E
    D:          пакет без зависимостей

Пакеты называются заглавными латинскими буквами (``A``, ``B``, ``AB``).
Зависимости разделяются пробелами. Пустые строки и текст после ``#``
пропускаются. Пакет, указанный только как зависимость, считается
отсутствующим в репозитории (как пакет без POM в репозитории Maven).
"""

import re

COMMENT = "#"
NAME_SEPARATOR = ":"
FILE_ENCODING = "utf-8-sig"
PACKAGE_NAME = re.compile(r"[A-Z]+")


class TestRepoError(Exception):
    """Ошибка чтения или формата файла тестового репозитория."""


def read_lines(path):
    """Прочитать строки файла тестового репозитория.

    :param path: путь к файлу.
    :return: список строк.
    :raises TestRepoError: если файл нельзя прочитать.
    """
    try:
        with open(path, encoding=FILE_ENCODING) as file:
            return file.read().splitlines()
    except OSError as exc:
        raise TestRepoError("cannot read '{}': {}".format(
            path, exc.strerror)) from None
    except UnicodeDecodeError:
        raise TestRepoError("'{}' is not a UTF-8 text file".format(
            path)) from None


def check_name(name):
    """Проверить имя пакета тестового репозитория.

    :param name: имя пакета.
    :raises TestRepoError: если имя не из заглавных латинских букв.
    """
    if not PACKAGE_NAME.fullmatch(name):
        raise TestRepoError("invalid package name '{}': expected capital "
                            "Latin letters".format(name))


def parse_line(line):
    """Разобрать строку вида ``A: B C``.

    :param line: строка без комментария и пробелов по краям.
    :return: кортеж (имя пакета, список зависимостей).
    :raises TestRepoError: при ошибке формата.
    """
    if NAME_SEPARATOR not in line:
        raise TestRepoError("expected 'PACKAGE: DEPENDENCIES', got "
                            "'{}'".format(line))
    name, rest = line.split(NAME_SEPARATOR, 1)
    name = name.strip()
    check_name(name)
    dependencies = []
    for dependency in rest.split():
        check_name(dependency)
        if dependency in dependencies:
            raise TestRepoError("duplicate dependency '{}' of {}".format(
                dependency, name))
        dependencies.append(dependency)
    return name, dependencies


def load_test_repo(path):
    """Загрузить тестовый репозиторий из файла.

    :param path: путь к файлу описания графа.
    :return: словарь ``пакет -> список зависимостей``.
    :raises TestRepoError: при ошибке чтения или формата (с номером
        строки).
    """
    packages = {}
    for number, raw_line in enumerate(read_lines(path), start=1):
        line = raw_line.split(COMMENT, 1)[0].strip()
        if not line:
            continue
        try:
            name, dependencies = parse_line(line)
            if name in packages:
                raise TestRepoError("duplicate package '{}'".format(name))
        except TestRepoError as exc:
            raise TestRepoError("{}:{}: {}".format(
                path, number, exc)) from None
        packages[name] = dependencies
    return packages
