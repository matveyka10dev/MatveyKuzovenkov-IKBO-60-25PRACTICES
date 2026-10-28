"""Получение сведений о реальной ОС для приглашения к вводу."""

import getpass
import platform
import socket

DEFAULT_USER = "user"
DEFAULT_HOST = "localhost"


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


def build_prompt(location):
    """Сформировать приглашение вида ``username@hostname:/path$``.

    :param location: текущий каталог для отображения.
    :return: строка приглашения с завершающим пробелом.
    """
    return "{}@{}:{}$ ".format(get_username(), get_hostname(), location)
