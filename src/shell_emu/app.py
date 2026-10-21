"""Точка входа приложения-эмулятора."""

from shell_emu.shell import Shell, run_interactive

WELCOME = "Shell emulator. Type 'exit' to quit."


def main():
    """Запустить эмулятор в интерактивном режиме.

    :return: код завершения процесса.
    """
    shell = Shell()
    shell.write(WELCOME)
    return run_interactive(shell)
