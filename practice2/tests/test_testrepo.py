"""Тесты чтения файла тестового репозитория."""

import os
import tempfile
import unittest

from depviz.testrepo import TestRepoError, load_test_repo

EXAMPLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                        "examples", "repos")


class LoadTestRepoTest(unittest.TestCase):
    """Проверка load_test_repo."""

    @property
    def tmp(self):
        """Временный каталог теста, удаляется после теста."""
        if "_tmp" not in self.__dict__:
            self._tmp = tempfile.TemporaryDirectory()
            self.addCleanup(self._tmp.cleanup)
        return self._tmp

    def load_text(self, text, encoding="utf-8"):
        """Записать текст во временный файл и загрузить его.

        :param text: содержимое файла.
        :param encoding: кодировка файла.
        :return: словарь пакетов.
        """
        path = os.path.join(self.tmp.name, "repo.txt")
        with open(path, "w", encoding=encoding) as file:
            file.write(text)
        return load_test_repo(path)

    def test_format(self):
        """Комментарии, пустые строки и BOM пропускаются."""
        packages = self.load_text("# header\n\nA: B  C # comment\nB:\n",
                                  encoding="utf-8-sig")
        self.assertEqual(packages, {"A": ["B", "C"], "B": []})

    def test_examples(self):
        """Все примеры из examples/repos загружаются без ошибок."""
        for name in os.listdir(EXAMPLES):
            path = os.path.join(EXAMPLES, name)
            if os.path.isfile(path):
                with self.subTest(name=name):
                    self.assertTrue(load_test_repo(path))

    def test_errors(self):
        """Ошибки формата сообщаются с номером строки."""
        cases = [
            ("A: B\nB C\n", ":2: expected 'PACKAGE: DEPENDENCIES'"),
            ("A: b\n", ":1: invalid package name 'b'"),
            ("a: B\n", ":1: invalid package name 'a'"),
            (": B\n", ":1: invalid package name ''"),
            ("A:\nA: B\n", ":2: duplicate package 'A'"),
            ("A: B C B\n", ":1: duplicate dependency 'B' of A"),
        ]
        for text, message in cases:
            with self.subTest(text=text):
                with self.assertRaisesRegex(TestRepoError, message):
                    self.load_text(text)

    def test_not_utf8(self):
        """Файл не в UTF-8 - ошибка."""
        path = os.path.join(self.tmp.name, "bad.txt")
        with open(path, "wb") as file:
            file.write(b"A: \xff\n")
        with self.assertRaisesRegex(TestRepoError, "not a UTF-8"):
            load_test_repo(path)

    def test_missing_file(self):
        """Отсутствующий файл - ошибка."""
        with self.assertRaisesRegex(TestRepoError, "cannot read"):
            load_test_repo(os.path.join(self.tmp.name, "none.txt"))


if __name__ == "__main__":
    unittest.main()
