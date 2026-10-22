"""Тесты выполнения стартового скрипта."""

import io
import os
import tempfile
import unittest

from shell_emu.commands import STATUS_ERROR, STATUS_NOT_FOUND, STATUS_OK
from shell_emu.script import execute_lines, run_script
from shell_emu.shell import Shell


def make_shell():
    """Создать эмулятор с выводом в строковые буферы.

    :return: кортеж (shell, out, err).
    """
    out = io.StringIO()
    err = io.StringIO()
    return Shell(out=out, err=err), out, err


class ExecuteLinesTest(unittest.TestCase):
    """Проверка execute_lines."""

    def test_echoes_input_and_output(self):
        """Выводится приглашение с командой, затем результат."""
        shell, out, _ = make_shell()
        status = execute_lines(shell, ["ls -l"], "s")
        self.assertEqual(status, STATUS_OK)
        self.assertEqual(out.getvalue().splitlines(), [
            shell.prompt() + "ls -l",
            "ls: [stub] args=['-l']",
        ])

    def test_skips_comments_and_blank_lines(self):
        """Комментарии и пустые строки не выполняются."""
        shell, out, _ = make_shell()
        execute_lines(shell, ["# comment", "", "   ", "cd"], "s")
        self.assertEqual(len(out.getvalue().splitlines()), 2)

    def test_stops_at_first_error(self):
        """Выполнение останавливается на первой ошибке."""
        shell, out, err = make_shell()
        lines = ["ls", "foo", "cd a b", "ls after"]
        status = execute_lines(shell, lines, "s")
        self.assertEqual(status, STATUS_NOT_FOUND)
        self.assertNotIn("after", out.getvalue())
        self.assertNotIn("too many", err.getvalue())
        self.assertIn("s:2: stopped", err.getvalue())

    def test_exit_stops_script(self):
        """Команда exit завершает скрипт и эмулятор."""
        shell, out, _ = make_shell()
        status = execute_lines(shell, ["exit 4", "ls"], "s")
        self.assertEqual(status, STATUS_OK)
        self.assertFalse(shell.running)
        self.assertEqual(shell.exit_code, 4)
        self.assertNotIn("[stub]", out.getvalue())


class RunScriptTest(unittest.TestCase):
    """Проверка run_script с реальными файлами."""

    def test_missing_file(self):
        """Отсутствующий файл скрипта - ошибка."""
        shell, _, err = make_shell()
        status = run_script(shell, "/no/such/file.txt")
        self.assertEqual(status, STATUS_ERROR)
        self.assertIn("cannot read script", err.getvalue())

    def test_file_is_executed(self):
        """Команды из файла выполняются."""
        shell, out, _ = make_shell()
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "start.txt")
            with open(path, "w", encoding="utf-8") as file:
                file.write("ls 'a b'\ncd\n")
            self.assertEqual(run_script(shell, path), STATUS_OK)
        self.assertIn("args=['a b']", out.getvalue())

    def test_windows_notepad_file(self):
        """Файл с BOM и концами строк CRLF (Блокнот Windows)."""
        shell, out, err = make_shell()
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "start.txt")
            with open(path, "wb") as file:
                file.write(b"\xef\xbb\xbfls -l\r\ncd x\r\n")
            self.assertEqual(run_script(shell, path), STATUS_OK)
        self.assertEqual(err.getvalue(), "")
        self.assertIn("ls: [stub] args=['-l']", out.getvalue())
        self.assertIn("cd: [stub] args=['x']", out.getvalue())

    def test_not_utf8_file(self):
        """Файл не в UTF-8 - понятная ошибка."""
        shell, _, err = make_shell()
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "start.txt")
            with open(path, "wb") as file:
                file.write("ls Привет\n".encode("cp1251"))
            self.assertEqual(run_script(shell, path), STATUS_ERROR)
        self.assertIn("not a UTF-8 text file", err.getvalue())

    def test_directory_instead_of_file(self):
        """Каталог вместо файла скрипта - ошибка."""
        shell, _, err = make_shell()
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(run_script(shell, tmp), STATUS_ERROR)
        self.assertIn("cannot read script", err.getvalue())


if __name__ == "__main__":
    unittest.main()
