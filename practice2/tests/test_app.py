"""Тесты точки входа приложения."""

import contextlib
import io
import os
import unittest
import unittest.mock

from depviz.app import (STATUS_CONFIG_ERROR, STATUS_ERROR, STATUS_OK,
                        TEST_MODE_NOTE, main)
from depviz.repository import NotFoundError
from depviz.resolver import Resolver

EXAMPLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                        "examples")
SIMPLE_REPO = os.path.join(EXAMPLES, "repos", "simple.txt")
LOCAL_REPO = os.path.join(EXAMPLES, "maven-repo")
REPO_URL = "http://repo.test"


def read_example(url):
    """Прочитать файл из examples/maven-repo вместо загрузки по сети.

    :param url: адрес файла в репозитории REPO_URL.
    :return: содержимое файла.
    :raises NotFoundError: если файла нет.
    """
    path = os.path.join(LOCAL_REPO, *url[len(REPO_URL):].split("/"))
    if not os.path.isfile(path):
        raise NotFoundError(url + ": HTTP 404 Not Found")
    with open(path, "rb") as file:
        return file.read()


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


class MainTest(unittest.TestCase):
    """Проверка функции main."""

    def test_prints_direct_dependencies(self):
        """Выводятся прямые зависимости пакета."""
        code, out, err = run_main(["-p", "junit:junit", "-r", REPO_URL])
        self.assertEqual(code, STATUS_OK)
        self.assertEqual(err, "")
        self.assertEqual(out, "Direct dependencies of junit:junit:4.13.2 "
                              "(2):\n"
                              "  org.hamcrest:hamcrest-core:1.3 [compile]\n"
                              "  org.hamcrest:hamcrest-library:1.3 [test]\n")

    def test_demo_app(self):
        """Пример с родителем, BOM и optional из examples/maven-repo."""
        code, out, _ = run_main(["-p", "org.example:demo-app",
                                 "-r", REPO_URL])
        self.assertEqual(code, STATUS_OK)
        self.assertIn("(7):", out)
        self.assertIn("com.google.guava:guava:33.0.0-jre [compile]", out)
        self.assertIn("jackson-databind:2.16.1 [compile]", out)
        self.assertIn("commons-lang3:3.14.0 [compile, optional]", out)
        self.assertIn("junit:junit:4.13.2 [test]", out)
        self.assertNotIn("plugin-only", out)

    def test_no_dependencies(self):
        """Пакет без зависимостей."""
        _, out, _ = run_main(["-p", "org.example:no-deps:1.0",
                              "-r", REPO_URL])
        self.assertIn("(no dependencies)", out)

    def test_resolve_error(self):
        """Ошибка получения зависимостей - код 1."""
        code, out, err = run_main(["-p", "org.example:ghost:1.0",
                                   "-r", REPO_URL])
        self.assertEqual(code, STATUS_ERROR)
        self.assertEqual(out, "")
        self.assertIn("org.example:ghost:1.0 not found", err)

    def test_test_mode(self):
        """Тестовый режим пока не поддерживается - сообщение, код 0."""
        code, out, _ = run_main(["-t", "-r", SIMPLE_REPO, "-p", "A"])
        self.assertEqual(code, STATUS_OK)
        self.assertEqual(out.strip(), TEST_MODE_NOTE)

    def test_config_error(self):
        """Ошибка в значении опции - код 2, без вывода."""
        code, out, err = run_main(["-p", "junit"])
        self.assertEqual(code, STATUS_CONFIG_ERROR)
        self.assertEqual(out, "")
        self.assertTrue(err.startswith("depviz: error: --package: "))


if __name__ == "__main__":
    unittest.main()
