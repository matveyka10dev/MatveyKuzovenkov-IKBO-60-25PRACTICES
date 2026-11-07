"""Тесты точки входа приложения."""

import contextlib
import io
import os
import unittest
import unittest.mock

from depviz.app import STATUS_CONFIG_ERROR, STATUS_ERROR, STATUS_OK, main
from depviz.resolver import Resolver
from tests.test_sources import read_example

EXAMPLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                        "examples")
REPOS = os.path.join(EXAMPLES, "repos")
REPO_URL = "http://repo.test"


def run_main(args):
    """Запустить main с локальным репозиторием и перехватом вывода.

    :param args: опции командной строки.
    :return: кортеж (код завершения, stdout, stderr).
    """
    out = io.StringIO()
    err = io.StringIO()

    def make_resolver(base_url):
        """Создать Resolver, читающий файлы из examples."""
        return Resolver(base_url, fetch=read_example)

    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        with unittest.mock.patch("depviz.app.Resolver", make_resolver):
            code = main(args)
    return code, out.getvalue(), err.getvalue()


def example_repo(name):
    """Вернуть путь к примеру тестового репозитория.

    :param name: имя файла в examples/repos.
    :return: путь к файлу.
    """
    return os.path.join(REPOS, name)


class MainTest(unittest.TestCase):
    """Проверка функции main."""

    def test_test_mode_graph(self):
        """Граф тестового репозитория с циклом."""
        code, out, err = run_main(["-t", "-r", example_repo("cycle.txt"),
                                   "-p", "A"])
        self.assertEqual(code, STATUS_OK)
        self.assertEqual(err, "")
        self.assertEqual(out, "Dependency graph of A (packages: 4, "
                              "dependencies: 4):\n"
                              "  A -> B\n"
                              "  B -> C\n"
                              "  C -> A, D\n"
                              "  D\n"
                              "Cycles (1):\n"
                              "  A -> B -> C -> A\n")

    def test_test_mode_filter(self):
        """Фильтр в тестовом режиме."""
        _, out, _ = run_main(["-t", "-r", example_repo("names.txt"),
                              "-p", "APP", "-f", "LO"])
        self.assertIn("Filtered out by 'LO' (1):\n  LOG\n", out)
        self.assertNotIn("APP -> WEB, LOG", out)

    def test_load_order(self):
        """Режим вывода порядка загрузки."""
        code, out, _ = run_main(["-t", "-r", example_repo("simple.txt"),
                                 "-p", "A", "--load-order"])
        self.assertEqual(code, STATUS_OK)
        self.assertTrue(out.startswith("Load order of A (packages: 5):\n"
                                       "  1. D\n  2. B\n"))

    def test_maven_graph(self):
        """Граф пакета из репозитория Maven."""
        code, out, _ = run_main(["-p", "junit:junit", "-r", REPO_URL])
        self.assertEqual(code, STATUS_OK)
        self.assertIn("  org.hamcrest:hamcrest-library:1.3 -> "
                      "org.hamcrest:hamcrest-core:1.3\n", out)

    def test_bad_test_repo(self):
        """Некорректный файл тестового репозитория - код 1."""
        code, out, err = run_main([
            "-t", "-r", os.path.join(REPOS, "broken", "no_colon.txt"),
            "-p", "A"])
        self.assertEqual(code, STATUS_ERROR)
        self.assertEqual(out, "")
        self.assertIn("no_colon.txt:2:", err)

    def test_missing_root(self):
        """Корневого пакета нет - код 1."""
        for args in (["-t", "-r", example_repo("simple.txt"), "-p", "Q"],
                     ["-p", "org.example:ghost:1.0", "-r", REPO_URL]):
            with self.subTest(args=args):
                code, _, err = run_main(args)
                self.assertEqual(code, STATUS_ERROR)
                self.assertIn("not found", err)

    def test_config_error(self):
        """Ошибка в значении опции - код 2, без вывода."""
        code, out, err = run_main(["-p", "junit"])
        self.assertEqual(code, STATUS_CONFIG_ERROR)
        self.assertEqual(out, "")
        self.assertTrue(err.startswith("depviz: error: --package: "))


if __name__ == "__main__":
    unittest.main()
