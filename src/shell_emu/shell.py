"""Ядро эмулятора: выполнение команд и интерактивный цикл (REPL)."""

import sys

from shell_emu.commands import (
    BUILTIN_COMMANDS,
    STATUS_NOT_FOUND,
    STATUS_OK,
    STATUS_USAGE,
    CommandError,
    ShellExit,
)
from shell_emu.lexer import ParseError, tokenize
from shell_emu.osinfo import build_prompt, current_dir_display

SHELL_NAME = "emulator"


class Shell:
    """Эмулятор командной оболочки UNIX-подобной ОС."""

    def __init__(self, out=None, err=None):
        """Создать эмулятор.

        :param out: поток для обычного вывода (по умолчанию stdout).
        :param err: поток для сообщений об ошибках (по умолчанию stderr).
        """
        self.out = out if out is not None else sys.stdout
        self.err = err if err is not None else sys.stderr
        self.commands = dict(BUILTIN_COMMANDS)
        self.last_status = STATUS_OK
        self.running = True
        self.exit_code = STATUS_OK

    def write(self, text):
        """Вывести строку в поток обычного вывода.

        :param text: выводимый текст.
        """
        self.out.write(text + "\n")
        self.out.flush()

    def error(self, text):
        """Вывести строку в поток ошибок.

        :param text: текст ошибки.
        """
        self.out.flush()
        self.err.write(text + "\n")
        self.err.flush()

    def prompt(self):
        """Вернуть строку приглашения к вводу.

        :return: приглашение вида ``username@hostname:~$``.
        """
        return build_prompt(current_dir_display())

    def execute(self, line):
        """Разобрать и выполнить одну строку ввода.

        :param line: строка, введённая пользователем.
        :return: код завершения команды.
        """
        try:
            args = tokenize(line)
        except ParseError as exc:
            self.error("{}: syntax error: {}".format(SHELL_NAME, exc))
            self.last_status = STATUS_USAGE
            return self.last_status
        if not args:
            return self.last_status
        self.last_status = self._run_command(args[0], args[1:])
        return self.last_status

    def _run_command(self, name, args):
        """Найти и вызвать обработчик команды.

        :param name: имя команды.
        :param args: аргументы команды.
        :return: код завершения команды.
        """
        handler = self.commands.get(name)
        if handler is None:
            self.error("{}: command not found".format(name))
            return STATUS_NOT_FOUND
        try:
            return handler(self, args)
        except CommandError as exc:
            self.error("{}: {}".format(name, exc))
            return exc.status
        except ShellExit as exc:
            self.running = False
            self.exit_code = exc.code
            return exc.code


def run_interactive(shell, read_line=input):
    """Запустить интерактивный цикл чтения и выполнения команд.

    Цикл завершается командой ``exit`` или концом ввода (Ctrl+D).
    Ctrl+C прерывает только текущую строку ввода.

    :param shell: экземпляр эмулятора.
    :param read_line: функция чтения строки с приглашением.
    :return: код завершения эмулятора.
    """
    while shell.running:
        try:
            line = read_line(shell.prompt())
        except EOFError:
            shell.write("exit")
            return shell.last_status
        except KeyboardInterrupt:
            shell.write("")
            continue
        shell.execute(line)
    return shell.exit_code
