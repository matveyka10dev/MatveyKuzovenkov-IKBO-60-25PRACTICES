"""Тесты разбора параметров командной строки."""

import contextlib
import io
import unittest

from shell_emu.config import NOT_SET, Config, format_debug, parse_args


class ParseArgsTest(unittest.TestCase):
    """Проверка parse_args."""

    def test_no_params(self):
        """Без параметров оба значения не заданы."""
        config = parse_args([])
        self.assertIsNone(config.vfs_path)
        self.assertIsNone(config.script_path)

    def test_all_params(self):
        """Оба параметра разбираются в любом порядке."""
        config = parse_args(["--script", "s.txt", "--vfs=fs.csv"])
        self.assertEqual(config.vfs_path, "fs.csv")
        self.assertEqual(config.script_path, "s.txt")

    def test_unknown_param(self):
        """Неизвестный параметр - выход с кодом 2."""
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                parse_args(["--bad"])
        self.assertEqual(ctx.exception.code, 2)

    def test_missing_value(self):
        """Параметр без значения - выход с кодом 2."""
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                parse_args(["--vfs"])
        self.assertEqual(ctx.exception.code, 2)


class DebugOutputTest(unittest.TestCase):
    """Проверка отладочного вывода параметров."""

    def test_debug_lists_all_params(self):
        """Выводятся все параметры, незаданные отмечены <not set>."""
        lines = format_debug(Config(vfs_path="fs.csv"))
        self.assertEqual(len(lines), 3)
        self.assertIn("vfs_path    = fs.csv", lines[1])
        self.assertIn("script_path = " + NOT_SET, lines[2])


if __name__ == "__main__":
    unittest.main()
