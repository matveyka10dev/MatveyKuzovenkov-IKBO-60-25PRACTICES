"""Тесты точки входа: параметры, отладочный вывод, стартовый скрипт."""

import contextlib
import io
import os
import tempfile
import unittest
import unittest.mock

from shell_emu.app import main


def run_main(args, stdin_text=""):
    """Запустить main с подменой stdin, stdout и stderr.

    :param args: параметры командной строки.
    :param stdin_text: текст, который эмулятор прочитает как ввод.
    :return: кортеж (код завершения, stdout, stderr).
    """
    out = io.StringIO()
    err = io.StringIO()
    stdin = io.StringIO(stdin_text)
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        with unittest.mock.patch("sys.stdin", stdin):
            code = main(args)
    return code, out.getvalue(), err.getvalue()


def write_script(directory, text):
    """Записать стартовый скрипт во временный каталог.

    :param directory: временный каталог.
    :param text: содержимое скрипта.
    :return: путь к файлу.
    """
    path = os.path.join(directory, "start.txt")
    with open(path, "w", encoding="utf-8") as file:
        file.write(text)
    return path


class MainTest(unittest.TestCase):
    """Проверка функции main."""

    def test_debug_output_without_params(self):
        """Без параметров выводятся оба параметра как <not set>."""
        code, out, _ = run_main([])
        self.assertEqual(code, 0)
        self.assertIn("[debug]   vfs_path    = <not set>", out)
        self.assertIn("[debug]   script_path = <not set>", out)

    def test_debug_output_with_params(self):
        """Заданные параметры попадают в отладочный вывод."""
        with tempfile.TemporaryDirectory() as tmp:
            script = write_script(tmp, "ls\n")
            _, out, _ = run_main(["--vfs", "fs.csv", "--script", script])
        self.assertIn("vfs_path    = fs.csv", out)
        self.assertIn("script_path = " + script, out)

    def test_script_then_interactive(self):
        """После успешного скрипта эмулятор читает команды с клавиатуры."""
        with tempfile.TemporaryDirectory() as tmp:
            script = write_script(tmp, "ls a\n")
            code, out, _ = run_main(["--script", script], "cd b\nexit 4\n")
        self.assertEqual(code, 4)
        self.assertIn("ls: [stub] args=['a']", out)
        self.assertIn("cd: [stub] args=['b']", out)

    def test_script_error_stops_emulator(self):
        """Ошибка в скрипте завершает эмулятор с её кодом."""
        with tempfile.TemporaryDirectory() as tmp:
            script = write_script(tmp, "ls\nfoo\nls never\n")
            code, out, err = run_main(["--script", script], "ls typed\n")
        self.assertEqual(code, 127)
        self.assertIn("stopped", err)
        self.assertNotIn("never", out)
        self.assertNotIn("typed", out)

    def test_exit_in_script(self):
        """Команда exit в скрипте завершает эмулятор сразу."""
        with tempfile.TemporaryDirectory() as tmp:
            script = write_script(tmp, "exit 7\nls never\n")
            code, out, _ = run_main(["--script", script], "ls typed\n")
        self.assertEqual(code, 7)
        self.assertNotIn("never", out)
        self.assertNotIn("typed", out)

    def test_missing_script(self):
        """Отсутствующий файл скрипта - код 1."""
        code, _, err = run_main(["--script", "/no/such/script.txt"])
        self.assertEqual(code, 1)
        self.assertIn("cannot read script", err)


if __name__ == "__main__":
    unittest.main()
