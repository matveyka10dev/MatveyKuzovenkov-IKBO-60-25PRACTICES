"""Выполнение стартового скрипта эмулятора.

Скрипт - текстовый файл в кодировке UTF-8 (с BOM или без него, как
сохраняет Блокнот Windows), одна команда на строку; концы строк
могут быть как LF (Linux), так и CRLF (Windows).
Пустые строки и строки, начинающиеся с ``#``, пропускаются.
Каждая команда выводится вместе с приглашением, а затем её результат,
так что на экране получается диалог, как при ручном вводе.
Выполнение останавливается при первой ошибке (код завершения не 0).
"""

from shell_emu.commands import STATUS_ERROR, STATUS_OK

COMMENT_PREFIX = "#"
SCRIPT_TAG = "[script]"
SCRIPT_ENCODING = "utf-8-sig"


class ScriptError(Exception):
    """Ошибка чтения стартового скрипта."""


def read_script(path):
    """Прочитать строки стартового скрипта.

    :param path: путь к файлу скрипта.
    :return: список строк без символов перевода строки.
    :raises ScriptError: если файл нельзя прочитать.
    """
    try:
        with open(path, encoding=SCRIPT_ENCODING) as file:
            return file.read().splitlines()
    except OSError as exc:
        raise ScriptError("cannot read script '{}': {}".format(
            path, exc.strerror)) from exc
    except UnicodeDecodeError as exc:
        raise ScriptError(
            "cannot read script '{}': not a UTF-8 text file".format(
                path)) from exc


def is_command_line(line):
    """Проверить, содержит ли строка скрипта команду.

    :param line: строка скрипта без пробелов по краям.
    :return: False для пустых строк и комментариев.
    """
    return bool(line) and not line.startswith(COMMENT_PREFIX)


def execute_lines(shell, lines, name):
    """Выполнить строки скрипта до конца, первой ошибки или exit.

    :param shell: экземпляр эмулятора.
    :param lines: строки скрипта.
    :param name: имя скрипта для сообщений об ошибках.
    :return: STATUS_OK или код завершения ошибочной команды.
    """
    for number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not is_command_line(line):
            continue
        shell.write(shell.prompt() + line)
        status = shell.execute(line)
        if not shell.running:
            return STATUS_OK
        if status != STATUS_OK:
            shell.error("{} {}:{}: stopped, '{}' exited with status {}"
                        .format(SCRIPT_TAG, name, number, line, status))
            return status
    return STATUS_OK


def run_script(shell, path):
    """Прочитать и выполнить стартовый скрипт.

    :param shell: экземпляр эмулятора.
    :param path: путь к файлу скрипта.
    :return: STATUS_OK при успехе, иначе код ошибки.
    """
    try:
        lines = read_script(path)
    except ScriptError as exc:
        shell.error("{} {}".format(SCRIPT_TAG, exc))
        return STATUS_ERROR
    return execute_lines(shell, lines, path)
