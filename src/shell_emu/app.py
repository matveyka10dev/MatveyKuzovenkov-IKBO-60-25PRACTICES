"""Точка входа приложения-эмулятора."""

from shell_emu.commands import STATUS_OK
from shell_emu.config import format_debug, parse_args
from shell_emu.script import run_script
from shell_emu.shell import Shell, run_interactive

WELCOME = "Shell emulator. Type 'exit' to quit."


def main(argv=None):
    """Запустить эмулятор.

    Порядок работы: разбор параметров, отладочный вывод параметров,
    выполнение стартового скрипта (если задан), интерактивный режим.
    Если стартовый скрипт завершился ошибкой, эмулятор завершается
    с кодом этой ошибки.

    :param argv: параметры командной строки (по умолчанию sys.argv[1:]).
    :return: код завершения процесса.
    """
    config = parse_args(argv)
    shell = Shell()
    for line in format_debug(config):
        shell.write(line)
    shell.write(WELCOME)
    if config.script_path is not None:
        status = run_script(shell, config.script_path)
        if status != STATUS_OK:
            return status
    if not shell.running:
        return shell.exit_code
    return run_interactive(shell)
