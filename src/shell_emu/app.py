"""Точка входа приложения-эмулятора."""

from shell_emu.commands import STATUS_ERROR, STATUS_OK
from shell_emu.config import format_debug, parse_args
from shell_emu.script import run_script
from shell_emu.shell import SHELL_NAME, Shell, run_interactive
from shell_emu.vfs import Vfs, VfsError, load_vfs

WELCOME = "Shell emulator. Type 'exit' to quit."


def setup_vfs(shell, vfs_path):
    """Загрузить VFS в эмулятор.

    Если путь не задан, используется пустая VFS (только корень).

    :param shell: экземпляр эмулятора.
    :param vfs_path: путь к CSV-файлу VFS или None.
    :return: True при успешной загрузке, False при ошибке.
    """
    if vfs_path is None:
        shell.vfs = Vfs()
        shell.write("[vfs] no VFS file given, using empty VFS")
        return True
    try:
        shell.vfs = load_vfs(vfs_path)
    except VfsError as exc:
        shell.error("{}: vfs: {}".format(SHELL_NAME, exc))
        return False
    stats = shell.vfs.stats()
    shell.write("[vfs] loaded '{}': {} directories, {} files".format(
        vfs_path, stats["dirs"], stats["files"]))
    return True


def main(argv=None):
    """Запустить эмулятор.

    Порядок работы: разбор параметров, отладочный вывод параметров,
    загрузка VFS, выполнение стартового скрипта (если задан),
    интерактивный режим. При ошибке загрузки VFS эмулятор завершается
    с кодом 1, при ошибке стартового скрипта - с кодом этой ошибки.

    :param argv: параметры командной строки (по умолчанию sys.argv[1:]).
    :return: код завершения процесса.
    """
    config = parse_args(argv)
    shell = Shell()
    for line in format_debug(config):
        shell.write(line)
    if not setup_vfs(shell, config.vfs_path):
        return STATUS_ERROR
    shell.write(WELCOME)
    if config.script_path is not None:
        status = run_script(shell, config.script_path)
        if status != STATUS_OK:
            return status
    if not shell.running:
        return shell.exit_code
    return run_interactive(shell)
