"""Тесты проверки значений параметров."""

import os
import tempfile
import unittest

from depviz.config import Config
from depviz.validation import (DEFAULT_REPO_URL, ConfigError, package_id,
                               resolve_repo, validate_config,
                               validate_filter, validate_package)


class ValidatePackageTest(unittest.TestCase):
    """Проверка validate_package."""

    def test_maven_coordinates(self):
        """Координаты Maven с версией и без неё допустимы."""
        for name in ("org.junit:junit", "com.google.guava:guava:33.0-jre",
                     "org.slf4j:slf4j-api:2.0.9"):
            with self.subTest(name=name):
                validate_package(name, test_mode=False)

    def test_bad_maven_coordinates(self):
        """Неверные координаты Maven - ошибка."""
        for name in ("junit", "a:b:c:d", ":junit", "org.junit:", "a b:c"):
            with self.subTest(name=name):
                with self.assertRaises(ConfigError):
                    validate_package(name, test_mode=False)

    def test_empty(self):
        """Пустое имя - ошибка в любом режиме."""
        for test_mode in (False, True):
            with self.subTest(test_mode=test_mode):
                with self.assertRaisesRegex(ConfigError, "empty"):
                    validate_package("  ", test_mode)

    def test_test_mode_names(self):
        """В тестовом режиме имя - только заглавные латинские буквы."""
        validate_package("ABC", test_mode=True)
        for name in ("a", "A1", "Б", "org.junit:junit"):
            with self.subTest(name=name):
                with self.assertRaises(ConfigError):
                    validate_package(name, test_mode=True)


class ResolveRepoTest(unittest.TestCase):
    """Проверка resolve_repo."""

    @property
    def tmp(self):
        """Временный каталог теста, удаляется после теста."""
        if "_tmp" not in self.__dict__:
            self._tmp = tempfile.TemporaryDirectory()
            self.addCleanup(self._tmp.cleanup)
        return self._tmp

    @property
    def file(self):
        """Файл тестового репозитория во временном каталоге."""
        path = os.path.join(self.tmp.name, "repo.txt")
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as file:
                file.write("A: B\n")
        return path

    def test_default_url(self):
        """Без --repo используется Maven Central."""
        self.assertEqual(resolve_repo(None, False), DEFAULT_REPO_URL)

    def test_valid_urls(self):
        """URL HTTP и HTTPS допустимы."""
        for url in ("https://repo.example.com/maven2",
                    "http://localhost:8081/repository"):
            with self.subTest(url=url):
                self.assertEqual(resolve_repo(url, False), url)

    def test_bad_urls(self):
        """Неверные URL - ошибка."""
        for url in ("ftp://host/x", "https:///x", "host/maven2",
                    "https://host/a b", ""):
            with self.subTest(url=url):
                with self.assertRaises(ConfigError):
                    resolve_repo(url, False)

    def test_file_in_remote_mode(self):
        """Файл вместо URL без тестового режима - ошибка с подсказкой."""
        with self.assertRaisesRegex(ConfigError, "--test-mode"):
            resolve_repo(self.file, False)

    def test_test_file(self):
        """В тестовом режиме принимается существующий файл."""
        self.assertEqual(resolve_repo(self.file, True), self.file)

    def test_test_mode_errors(self):
        """Нет пути, URL, нет файла, каталог - ошибки тестового режима."""
        cases = [
            (None, "requires a path"),
            ("https://host/maven2", "not a URL"),
            (os.path.join(self.tmp.name, "no.txt"), "No such file"),
            (self.tmp.name, "Is a directory"),
        ]
        for repo, message in cases:
            with self.subTest(repo=repo):
                with self.assertRaisesRegex(ConfigError, message):
                    resolve_repo(repo, True)


class ValidateFilterTest(unittest.TestCase):
    """Проверка validate_filter."""

    def test_not_set(self):
        """Фильтр не задан - проверка проходит."""
        validate_filter(None, "org.junit:junit")

    def test_valid(self):
        """Подстрока, не входящая в имя пакета, допустима."""
        validate_filter("hamcrest", "org.junit:junit:4.13")
        validate_filter("D", "ABC")

    def test_version_is_ignored(self):
        """Версия пакета не учитывается при сравнении с фильтром."""
        validate_filter("4.13", "org.junit:junit:4.13")

    def test_errors(self):
        """Пустая строка, пробелы, совпадение с пакетом - ошибки."""
        for substring in ("", "a b", "junit", "org.j"):
            with self.subTest(substring=substring):
                with self.assertRaises(ConfigError):
                    validate_filter(substring, "org.junit:junit")

    def test_package_id(self):
        """package_id отбрасывает версию."""
        self.assertEqual(package_id("g:a:1.0"), "g:a")
        self.assertEqual(package_id("ABC"), "ABC")


class ValidateConfigTest(unittest.TestCase):
    """Проверка validate_config."""

    def test_sets_default_repo(self):
        """Корректная конфигурация получает URL по умолчанию."""
        config = Config("org.junit:junit")
        validate_config(config)
        self.assertEqual(config.repo, DEFAULT_REPO_URL)

    def test_error_names_option(self):
        """Сообщение об ошибке начинается с имени опции."""
        with self.assertRaises(ConfigError) as ctx:
            validate_config(Config("org.junit:junit", name_filter=""))
        self.assertEqual(ctx.exception.option, "--filter")
        self.assertTrue(str(ctx.exception).startswith("--filter: "))


if __name__ == "__main__":
    unittest.main()
