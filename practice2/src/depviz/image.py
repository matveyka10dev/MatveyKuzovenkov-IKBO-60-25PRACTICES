"""Вывод изображения графа на экран.

Изображение строится программой ``dot`` из пакета Graphviz
(https://graphviz.org), сохраняется во временный файл PNG и
открывается программой просмотра изображений, назначенной в системе.
"""

import os
import shutil
import subprocess
import sys
import tempfile

DOT_PROGRAM = "dot"
IMAGE_FORMAT = "png"
IMAGE_PREFIX = "depviz-"
TEXT_ENCODING = "utf-8"
OPEN_COMMANDS = {"darwin": "open"}
DEFAULT_OPEN_COMMAND = "xdg-open"
WINDOWS_PREFIX = "win"
EXIT_SUCCESS = 0


class ImageError(Exception):
    """Ошибка построения или показа изображения."""


def render_image(dot_text):
    """Построить изображение графа программой Graphviz dot.

    :param dot_text: описание графа на языке DOT.
    :return: путь к созданному файлу PNG.
    :raises ImageError: если Graphviz не установлен или dot завершился
        с ошибкой.
    """
    program = shutil.which(DOT_PROGRAM)
    if program is None:
        raise ImageError("Graphviz is not installed: '{}' not found in "
                         "PATH".format(DOT_PROGRAM))
    handle, path = tempfile.mkstemp(prefix=IMAGE_PREFIX,
                                    suffix="." + IMAGE_FORMAT)
    os.close(handle)
    result = subprocess.run(
        [program, "-T" + IMAGE_FORMAT, "-o", path],
        input=dot_text.encode(TEXT_ENCODING), stderr=subprocess.PIPE,
        check=False)
    if result.returncode != EXIT_SUCCESS:
        raise ImageError("dot failed: {}".format(
            result.stderr.decode(TEXT_ENCODING, "replace").strip()))
    return path


def open_image(path):
    """Открыть файл изображения в программе просмотра системы.

    :param path: путь к файлу.
    :raises ImageError: если программу просмотра запустить не удалось.
    """
    try:
        if sys.platform.startswith(WINDOWS_PREFIX):
            os.startfile(path)
            return
        command = OPEN_COMMANDS.get(sys.platform, DEFAULT_OPEN_COMMAND)
        subprocess.run([command, path], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ImageError("cannot open image {}: {}".format(
            path, exc)) from None


def show_image(dot_text):
    """Построить изображение графа и вывести его на экран.

    :param dot_text: описание графа на языке DOT.
    :return: путь к файлу изображения.
    :raises ImageError: при ошибке построения или показа.
    """
    path = render_image(dot_text)
    open_image(path)
    return path
