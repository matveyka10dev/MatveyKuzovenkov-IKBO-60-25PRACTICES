"""Тесты разбора опций командной строки и вывода параметров."""

import contextlib
import io
import unittest

from depviz.config import NOT_SET, Config, format_config, parse_args

STATUS_USAGE = 2


def parse_error(argv):
    """Разобрать ошибочные опции и вернуть код и текст ошибки.

    :param argv: список аргументов.
    :return: кортеж (код завершения, вывод в stderr).
    """
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        with unittest.TestCase().assertRaises(SystemExit) as ctx:
            parse_args(argv)
    return ctx.exception.code, err.getvalue()


class ParseArgsTest(unittest.TestCase):
    """Проверка parse_args на корректных опциях."""

    def test_only_package(self):
        """Задан только пакет: остальные параметры по умолчанию."""
        config = parse_args(["--package", "org.junit:junit"])
        self.assertEqual(config.package, "org.junit:junit")
        self.assertIsNone(config.repo)
        self.assertFalse(config.test_mode)
        self.assertFalse(config.ascii_tree)
        self.assertIsNone(config.name_filter)

    def test_all_options_long(self):
        """Все длинные опции, включая форму --opt=value."""
        config = parse_args([
            "--package=A", "--repo", "r.txt", "--test-mode",
            "--ascii-tree", "--filter=B"])
        self.assertEqual((config.package, config.repo), ("A", "r.txt"))
        self.assertTrue(config.test_mode)
        self.assertTrue(config.ascii_tree)
        self.assertEqual(config.name_filter, "B")

    def test_short_options_any_order(self):
        """Короткие опции в произвольном порядке, флаги слитно."""
        config = parse_args(["-f", "B", "-ta", "-r", "r.txt", "-p", "A"])
        self.assertEqual(config.package, "A")
        self.assertTrue(config.test_mode and config.ascii_tree)
        self.assertEqual(config.name_filter, "B")


class ParseArgsErrorTest(unittest.TestCase):
    """Проверка синтаксических ошибок опций."""

    def test_package_required(self):
        """Без --package - ошибка с кодом 2."""
        code, err = parse_error([])
        self.assertEqual(code, STATUS_USAGE)
        self.assertIn("required: --package", err)

    def test_missing_value(self):
        """Опция без значения - ошибка."""
        for option in ("--package", "--repo", "--filter"):
            with self.subTest(option=option):
                code, err = parse_error(["-p", "A", option])
                self.assertEqual(code, STATUS_USAGE)
                self.assertIn("expected one argument", err)

    def test_repeated_option(self):
        """Повтор опции со значением - ошибка."""
        code, err = parse_error(["-p", "A", "--package", "B"])
        self.assertEqual(code, STATUS_USAGE)
        self.assertIn("--package: specified more than once", err)

    def test_repeated_flag(self):
        """Повтор флага, в том числе слитно (-aa), - ошибка."""
        for argv in (["-p", "A", "-t", "--test-mode"], ["-p", "A", "-aa"]):
            with self.subTest(argv=argv):
                code, err = parse_error(argv)
                self.assertEqual(code, STATUS_USAGE)
                self.assertIn("specified more than once", err)

    def test_flag_with_value(self):
        """Флаг со значением - ошибка."""
        code, err = parse_error(["-p", "A", "--ascii-tree=on"])
        self.assertEqual(code, STATUS_USAGE)
        self.assertIn("ignored explicit argument 'on'", err)

    def test_unknown_option(self):
        """Неизвестная опция и лишний аргумент - ошибка."""
        for extra in ("--unknown", "extra"):
            with self.subTest(extra=extra):
                code, err = parse_error(["-p", "A", extra])
                self.assertEqual(code, STATUS_USAGE)
                self.assertIn("unrecognized arguments", err)


class FormatConfigTest(unittest.TestCase):
    """Проверка вывода параметров в формате ключ-значение."""

    def test_all_keys_in_order(self):
        """Выводятся все пять параметров, ключи выровнены."""
        lines = format_config(Config("A", "r.txt", True, False, "B"))
        self.assertEqual(lines, [
            "package    = A",
            "repo       = r.txt",
            "test-mode  = true",
            "ascii-tree = false",
            "filter     = B",
        ])

    def test_not_set(self):
        """Незаданные параметры отмечаются <not set>."""
        lines = format_config(Config("A"))
        self.assertEqual(lines[1], "repo       = " + NOT_SET)
        self.assertEqual(lines[4], "filter     = " + NOT_SET)


if __name__ == "__main__":
    unittest.main()
