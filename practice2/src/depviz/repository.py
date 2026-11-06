"""Загрузка файлов из репозитория Maven по HTTP(S).

Используется только стандартный модуль urllib. Менеджеры пакетов и
сторонние библиотеки для получения зависимостей не применяются.
"""

import urllib.error
import urllib.request

TIMEOUT_SECONDS = 20
USER_AGENT = "depviz/0.3"
HTTP_NOT_FOUND = 404


class RepositoryError(Exception):
    """Ошибка загрузки файла из репозитория."""


class NotFoundError(RepositoryError):
    """Файл отсутствует в репозитории (HTTP 404)."""


def fetch_url(url):
    """Скачать файл по URL.

    :param url: адрес файла.
    :return: содержимое файла (bytes).
    :raises NotFoundError: если сервер ответил 404.
    :raises RepositoryError: при любой другой ошибке сети или HTTP.
    """
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request,
                                    timeout=TIMEOUT_SECONDS) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        if exc.code == HTTP_NOT_FOUND:
            raise NotFoundError("{}: HTTP 404 Not Found".format(
                url)) from None
        raise RepositoryError("{}: HTTP {} {}".format(
            url, exc.code, exc.reason)) from None
    except urllib.error.URLError as exc:
        raise RepositoryError("{}: cannot connect: {}".format(
            url, exc.reason)) from None
    except OSError as exc:
        raise RepositoryError("{}: {}".format(url, exc)) from None
