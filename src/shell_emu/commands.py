"""Встроенные команды эмулятора.

Каждая команда - функция ``handler(shell, args) -> int``, где ``shell`` -
экземпляр :class:`shell_emu.shell.Shell`, ``args`` - список аргументов
без имени команды, а результат - код завершения (0 - успех).
Об ошибках команда сообщает исключением :class:`CommandError`.
"""

STATUS_OK = 0
STATUS_ERROR = 1
STATUS_USAGE = 2
STATUS_NOT_FOUND = 127
EXIT_CODE_MODULO = 256

LS_SHORT_OPTIONS = "la"
CD_MAX_ARGS = 1
EXIT_MAX_ARGS = 1


class CommandError(Exception):
    """Ошибка выполнения команды с кодом завершения."""

    def __init__(self, message, status=STATUS_ERROR):
        """Создать ошибку.

        :param message: текст ошибки (без имени команды).
        :param status: код завершения команды.
        """
        super().__init__(message)
        self.status = status


class ShellExit(Exception):
    """Запрос на завершение работы эмулятора."""

    def __init__(self, code):
        """Создать запрос на выход.

        :param code: код завершения эмулятора.
        """
        super().__init__(code)
        self.code = code


def stub_message(name, args):
    """Сформировать сообщение команды-заглушки.

    :param name: имя команды.
    :param args: список аргументов.
    :return: строка вида ``ls: [stub] args=['-l', 'my dir']``.
    """
    return "{}: [stub] args={!r}".format(name, args)


def check_short_options(arg, allowed):
    """Проверить аргумент-опцию вида ``-la`` на допустимость.

    :param arg: аргумент, начинающийся с ``-``.
    :param allowed: строка допустимых однобуквенных опций.
    :raises CommandError: при неизвестной опции.
    """
    if arg.startswith("--"):
        raise CommandError(
            "unrecognized option '{}'".format(arg), STATUS_USAGE)
    for flag in arg[1:]:
        if flag not in allowed:
            raise CommandError(
                "invalid option -- '{}'".format(flag), STATUS_USAGE)


def is_option(arg):
    """Проверить, является ли аргумент опцией (``-x``, но не ``-``).

    :param arg: аргумент командной строки.
    :return: True, если аргумент - опция.
    """
    return arg.startswith("-") and arg != "-"


def cmd_ls(shell, args):
    """Команда ls (заглушка): проверяет опции и выводит аргументы.

    Допустимые опции: ``-l``, ``-a`` и их комбинации.

    :param shell: экземпляр эмулятора.
    :param args: аргументы команды.
    :return: код завершения.
    """
    for arg in args:
        if is_option(arg):
            check_short_options(arg, LS_SHORT_OPTIONS)
    shell.write(stub_message("ls", args))
    return STATUS_OK


def cmd_cd(shell, args):
    """Команда cd (заглушка): принимает не более одного аргумента.

    :param shell: экземпляр эмулятора.
    :param args: аргументы команды.
    :return: код завершения.
    :raises CommandError: если аргументов больше одного.
    """
    if len(args) > CD_MAX_ARGS:
        raise CommandError("too many arguments")
    shell.write(stub_message("cd", args))
    return STATUS_OK


def cmd_exit(shell, args):
    """Команда exit [n]: завершить работу эмулятора с кодом n.

    Без аргумента используется код последней выполненной команды.

    :param shell: экземпляр эмулятора.
    :param args: аргументы команды.
    :raises CommandError: при лишних или нечисловых аргументах.
    :raises ShellExit: всегда при корректных аргументах.
    """
    if len(args) > EXIT_MAX_ARGS:
        raise CommandError("too many arguments")
    code = shell.last_status
    if args:
        try:
            code = int(args[0])
        except ValueError:
            raise CommandError(
                "{}: numeric argument required".format(args[0]),
                STATUS_USAGE) from None
    raise ShellExit(code % EXIT_CODE_MODULO)


BUILTIN_COMMANDS = {
    "ls": cmd_ls,
    "cd": cmd_cd,
    "exit": cmd_exit,
}
