"""Тесты точки входа приложения."""

import contextlib
import io
import os
import unittest
import unittest.mock

from depviz.app import STATUS_CONFIG_ERROR, STATUS_ERROR, STATUS_OK, main
from depviz.image import ImageError
from depviz.resolver import Resolver
from tests.test_sources import read_example

EXAMPLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                        "examples")
REPOS = os.path.join(EXAMPLES, "repos")
REPO_URL = "http://repo.test"


def run_main(args, show_image=None):
    """Запустить main с локальным репозиторием и перехватом вывода.

    Показ изображения заменяется заглушкой, которая запоминает
    переданное описание графа.

    :param args: опции командной строки.
    :param show_image: заглушка показа изображения или None.
    :return: кортеж (код завершения, stdout, stderr).
    """
    show_image = show_image or unittest.mock.Mock()
    out = io.StringIO()
    err = io.StringIO()

    def make_resolver(base_url):
        """Создать Resolver, читающий файлы из examples."""
        return Resolver(base_url, fetch=read_example)

    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        with unittest.mock.patch("depviz.app.Resolver", make_resolver), \
                unittest.mock.patch("depviz.app.show_image", show_image):
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

    def test_dot_and_image(self):
        """Выводится описание на языке Graphviz, оно же - для картинки."""
        show_image = unittest.mock.Mock()
        code, out, err = run_main(["-t", "-r", example_repo("cycle.txt"),
                                   "-p", "A"], show_image)
        self.assertEqual(code, STATUS_OK)
        self.assertEqual(err, "")
        self.assertTrue(out.startswith("digraph dependencies {\n"))
        self.assertIn('    "C" -> "A";\n', out)
        show_image.assert_called_once_with(out)

    def test_ascii_tree(self):
        """С флагом --ascii-tree выводится дерево, картинка - тоже."""
        show_image = unittest.mock.Mock()
        code, out, _ = run_main(["-t", "-r", example_repo("names.txt"),
                                 "-p", "APP", "-f", "LO", "-a"], show_image)
        self.assertEqual(code, STATUS_OK)
        self.assertTrue(out.startswith("APP\n+- WEB\n"))
        self.assertIn("\\- TEST\n   +- APP (cycle)\n", out)
        self.assertNotIn("LOG", out)
        show_image.assert_called_once()

    def test_image_error(self):
        """Ошибка показа изображения - код 1 после вывода текста."""
        failing = unittest.mock.Mock(side_effect=ImageError("no dot"))
        code, out, err = run_main(["-t", "-r", example_repo("simple.txt"),
                                   "-p", "A"], failing)
        self.assertEqual(code, STATUS_ERROR)
        self.assertTrue(out.startswith("digraph"))
        self.assertEqual(err, "depviz: error: no dot\n")

    def test_maven_graph(self):
        """Граф пакета из репозитория Maven."""
        code, out, _ = run_main(["-p", "junit:junit", "-r", REPO_URL, "-a"])
        self.assertEqual(code, STATUS_OK)
        self.assertEqual(out, "junit:junit:4.13.2\n"
                              "+- org.hamcrest:hamcrest-core:1.3\n"
                              "\\- org.hamcrest:hamcrest-library:1.3\n"
                              "   \\- org.hamcrest:hamcrest-core:1.3 (*)\n")

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
