"""Проверка значений параметров, заданных пользователем.

Синтаксис командной строки проверяет argparse (неизвестная опция,
опция без значения, повтор опции). Здесь проверяются сами значения
и их согласованность между собой:

* ``--package`` - координаты Maven ``groupId:artifactId[:version]``,
  а в тестовом режиме - имя из заглавных латинских букв;
* ``--repo`` - URL HTTP(S) репозитория, а в тестовом режиме - путь
  к существующему файлу; без опции используется Maven Central;
* ``--filter`` - непустая подстрока без пробелов, не совпадающая
  с частью имени самого анализируемого пакета.
"""

import os
import re
import urllib.parse

DEFAULT_REPO_URL = "https://repo1.maven.org/maven2"
URL_SCHEMES = ("http", "https")
MAVEN_PART = r"[A-Za-z0-9_.\-]+"
MAVEN_COORDINATE = re.compile(
    r"{0}:{0}(:{0})?".format(MAVEN_PART))
TEST_PACKAGE_NAME = re.compile(r"[A-Z]+")
COORDINATE_SEPARATOR = ":"
PACKAGE_ID_PARTS = 2
WHITESPACE = re.compile(r"\s")


class ConfigError(Exception):
    """Ошибка в значении параметра."""

    def __init__(self, option, message):
        """Создать ошибку.

        :param option: имя опции, например ``--repo``.
        :param message: описание ошибки.
        """
        super().__init__("{}: {}".format(option, message))
        self.option = option


def validate_package(name, test_mode):
    """Проверить имя анализируемого пакета.

    :param name: имя пакета.
    :param test_mode: True - режим тестового репозитория.
    :raises ConfigError: если имя пустое или имеет неверный формат.
    """
    if not name.strip():
        raise ConfigError("--package", "package name must not be empty")
    if test_mode:
        if not TEST_PACKAGE_NAME.fullmatch(name):
            raise ConfigError(
                "--package", "'{}': in test mode package name must "
                "consist of capital Latin letters".format(name))
    elif not MAVEN_COORDINATE.fullmatch(name):
        raise ConfigError(
            "--package", "'{}' is not a Maven coordinate "
            "groupId:artifactId[:version]".format(name))


def is_url(value):
    """Проверить, похоже ли значение на URL HTTP(S).

    :param value: значение параметра.
    :return: True, если схема значения - http или https.
    """
    return urllib.parse.urlsplit(value).scheme.lower() in URL_SCHEMES


def validate_repo_url(url):
    """Проверить URL репозитория Maven.

    :param url: значение ``--repo``.
    :raises ConfigError: если это не URL HTTP(S) с именем сервера.
    """
    if WHITESPACE.search(url):
        raise ConfigError("--repo", "'{}': URL must not contain "
                          "whitespace".format(url))
    if not is_url(url):
        hint = ""
        if os.path.exists(url):
            hint = " (use --test-mode for a test repository file)"
        raise ConfigError("--repo", "'{}' is not an HTTP(S) URL{}".format(
            url, hint))
    if not urllib.parse.urlsplit(url).hostname:
        raise ConfigError("--repo", "'{}': URL has no host".format(url))


def validate_repo_file(path):
    """Проверить путь к файлу тестового репозитория.

    :param path: значение ``--repo``.
    :raises ConfigError: если файл не существует или его нельзя читать.
    """
    if is_url(path):
        raise ConfigError("--repo", "'{}': test mode requires a file "
                          "path, not a URL".format(path))
    if not os.path.exists(path):
        raise ConfigError("--repo", "{}: No such file or directory".format(
            path))
    if os.path.isdir(path):
        raise ConfigError("--repo", "{}: Is a directory".format(path))
    if not os.access(path, os.R_OK):
        raise ConfigError("--repo", "{}: Permission denied".format(path))


def resolve_repo(repo, test_mode):
    """Проверить репозиторий и подставить значение по умолчанию.

    :param repo: значение ``--repo`` или None.
    :param test_mode: True - режим тестового репозитория.
    :return: итоговый URL или путь к файлу.
    :raises ConfigError: при неверном или отсутствующем значении.
    """
    if repo is None:
        if test_mode:
            raise ConfigError("--repo", "test mode requires a path to "
                              "the test repository file")
        return DEFAULT_REPO_URL
    if not repo.strip():
        raise ConfigError("--repo", "value must not be empty")
    if test_mode:
        validate_repo_file(repo)
    else:
        validate_repo_url(repo)
    return repo


def package_id(name):
    """Вернуть имя пакета без версии.

    :param name: ``groupId:artifactId[:version]`` или имя тестового
        пакета.
    :return: ``groupId:artifactId`` или имя тестового пакета.
    """
    parts = name.split(COORDINATE_SEPARATOR)
    return COORDINATE_SEPARATOR.join(parts[:PACKAGE_ID_PARTS])


def validate_filter(substring, package):
    """Проверить подстроку для фильтрации пакетов.

    :param substring: значение ``--filter`` или None.
    :param package: имя анализируемого пакета (уже проверенное).
    :raises ConfigError: если подстрока пустая, содержит пробелы или
        исключает сам анализируемый пакет.
    """
    if substring is None:
        return
    if not substring:
        raise ConfigError("--filter", "substring must not be empty")
    if WHITESPACE.search(substring):
        raise ConfigError("--filter", "'{}': substring must not contain "
                          "whitespace".format(substring))
    if substring in package_id(package):
        raise ConfigError("--filter", "'{}' excludes the analyzed "
                          "package '{}' itself".format(substring, package))


def validate_config(config):
    """Проверить все параметры и подставить значения по умолчанию.

    :param config: экземпляр Config (поле repo может быть изменено).
    :raises ConfigError: при первой найденной ошибке.
    """
    validate_package(config.package, config.test_mode)
    config.repo = resolve_repo(config.repo, config.test_mode)
    validate_filter(config.name_filter, config.package)
