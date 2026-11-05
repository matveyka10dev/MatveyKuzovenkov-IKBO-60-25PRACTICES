"""Тесты точки входа приложения."""

import contextlib
import io
import os
import unittest

from depviz.app import STATUS_CONFIG_ERROR, STATUS_OK, main

EXAMPLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                        "examples")
SIMPLE_REPO = os.path.join(EXAMPLES, "repos", "simple.txt")


def run_main(args):
    """Запустить main с перехватом stdout и stderr.

    :param args: опции командной строки.
    :return: кортеж (код завершения, stdout, stderr).
    """
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(args)
    return code, out.getvalue(), err.getvalue()


class MainTest(unittest.TestCase):
    """Проверка функции main."""

    def test_prints_key_value(self):
        """При корректных опциях выводятся все параметры."""
        code, out, err = run_main(["-p", "org.junit:junit:4.13.2", "-a"])
        self.assertEqual(code, STATUS_OK)
        self.assertEqual(err, "")
        self.assertIn("package    = org.junit:junit:4.13.2\n", out)
        self.assertIn("repo       = https://repo1.maven.org/maven2\n", out)
        self.assertIn("ascii-tree = true\n", out)

    def test_test_mode(self):
        """Тестовый режим с файлом из examples."""
        code, out, _ = run_main(["-t", "-r", SIMPLE_REPO, "-p", "A"])
        self.assertEqual(code, STATUS_OK)
        self.assertIn("test-mode  = true\n", out)

    def test_config_error(self):
        """Ошибка в значении - сообщение в stderr, код 2, без вывода."""
        code, out, err = run_main(["-p", "junit"])
        self.assertEqual(code, STATUS_CONFIG_ERROR)
        self.assertEqual(out, "")
        self.assertTrue(err.startswith("depviz: error: --package: "))


if __name__ == "__main__":
    unittest.main()
