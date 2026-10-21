"""Получение сведений о реальной ОС для приглашения к вводу."""

import getpass
import os
import platform
import socket

DEFAULT_USER = "user"
DEFAULT_HOST = "localhost"
HOME_SIGN = "~"


def get_username():
    """Вернуть имя текущего пользователя ОС.

    :return: имя пользователя или ``user``, если его не удалось узнать.
    """
    try:
        return getpass.getuser()
    except (KeyError, OSError):
        return DEFAULT_USER


def get_hostname():
    """Вернуть короткое имя компьютера (до первой точки).

    :return: имя хоста или ``localhost``, если его не удалось узнать.
    """
    name = socket.gethostname() or platform.node()
    return name.split(".")[0] or DEFAULT_HOST


def shorten_home(path, home):
    """Заменить домашний каталог в начале пути на ``~``.

    :param path: абсолютный путь.
    :param home: путь к домашнему каталогу.
    :return: путь, в котором домашний каталог заменён на ``~``.
    """
    if path == home:
        return HOME_SIGN
    prefix = home.rstrip(os.sep) + os.sep
    if home and path.startswith(prefix):
        return HOME_SIGN + os.sep + path[len(prefix):]
    return path


def current_dir_display():
    """Вернуть текущий каталог ОС в сокращённом виде (``~/...``).

    :return: строка с текущим каталогом.
    """
    return shorten_home(os.getcwd(), os.path.expanduser(HOME_SIGN))


def build_prompt(location):
    """Сформировать приглашение вида ``username@hostname:~$``.

    :param location: текущее расположение для отображения.
    :return: строка приглашения с завершающим пробелом.
    """
    return "{}@{}:{}$ ".format(get_username(), get_hostname(), location)
