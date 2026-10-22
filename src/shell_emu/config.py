"""Параметры эмулятора, задаваемые в командной строке ОС."""

import argparse

PROG_NAME = "shell_emu"
NOT_SET = "<not set>"
DEBUG_PREFIX = "[debug]"


class Config:
    """Набор параметров запуска эмулятора."""

    def __init__(self, vfs_path=None, script_path=None):
        """Создать конфигурацию.

        :param vfs_path: путь к физическому расположению VFS или None.
        :param script_path: путь к стартовому скрипту или None.
        """
        self.vfs_path = vfs_path
        self.script_path = script_path

    def items(self):
        """Вернуть параметры в виде пар (имя, значение).

        :return: список пар в порядке вывода.
        """
        return [
            ("vfs_path", self.vfs_path),
            ("script_path", self.script_path),
        ]


def build_arg_parser():
    """Создать парсер параметров командной строки.

    :return: экземпляр argparse.ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        prog=PROG_NAME,
        description="Эмулятор командной оболочки UNIX-подобной ОС.")
    parser.add_argument(
        "--vfs", dest="vfs_path", metavar="PATH",
        help="путь к физическому расположению VFS")
    parser.add_argument(
        "--script", dest="script_path", metavar="PATH",
        help="путь к стартовому скрипту")
    return parser


def parse_args(argv=None):
    """Разобрать параметры командной строки.

    При ошибке argparse выводит справку и завершает процесс с кодом 2.

    :param argv: список аргументов (по умолчанию sys.argv[1:]).
    :return: экземпляр Config.
    """
    namespace = build_arg_parser().parse_args(argv)
    return Config(namespace.vfs_path, namespace.script_path)


def format_debug(config):
    """Сформировать отладочный вывод всех параметров эмулятора.

    :param config: экземпляр Config.
    :return: список строк для вывода.
    """
    pairs = config.items()
    width = max(len(name) for name, _ in pairs)
    lines = ["{} emulator parameters:".format(DEBUG_PREFIX)]
    for name, value in pairs:
        shown = NOT_SET if value is None else value
        lines.append("{}   {} = {}".format(
            DEBUG_PREFIX, name.ljust(width), shown))
    return lines
