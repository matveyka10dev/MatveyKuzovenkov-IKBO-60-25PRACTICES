"""Тесты модели пакетов Maven."""

import unittest

from depviz.maven import (UNKNOWN_VERSION, Coordinate, Dependency,
                          metadata_url, pom_url)

REPO = "https://repo.example.com/maven2/"


class CoordinateTest(unittest.TestCase):
    """Проверка Coordinate."""

    def test_parse_with_version(self):
        """Разбор координат с версией."""
        coordinate = Coordinate.parse("org.junit:junit:4.13")
        self.assertEqual(coordinate.group_id, "org.junit")
        self.assertEqual(coordinate.artifact_id, "junit")
        self.assertEqual(coordinate.version, "4.13")
        self.assertEqual(str(coordinate), "org.junit:junit:4.13")

    def test_parse_without_version(self):
        """Без версии строка не содержит третьей части."""
        coordinate = Coordinate.parse("org.junit:junit")
        self.assertIsNone(coordinate.version)
        self.assertEqual(str(coordinate), "org.junit:junit")
        self.assertEqual(coordinate.key, "org.junit:junit")


class UrlTest(unittest.TestCase):
    """Проверка построения адресов файлов в репозитории."""

    def test_pom_url(self):
        """Точки в groupId заменяются на /, лишний / в конце убирается."""
        url = pom_url(REPO, Coordinate("org.junit", "junit", "4.13"))
        self.assertEqual(url, "https://repo.example.com/maven2/org/junit/"
                              "junit/4.13/junit-4.13.pom")

    def test_metadata_url(self):
        """Адрес maven-metadata.xml не зависит от версии."""
        url = metadata_url(REPO, Coordinate("a.b", "c", "1"))
        self.assertEqual(url, "https://repo.example.com/maven2/a/b/c/"
                              "maven-metadata.xml")


class DependencyTest(unittest.TestCase):
    """Проверка Dependency."""

    def test_interpolate(self):
        """Свойства подставляются во все поля."""
        dependency = Dependency(Coordinate("${g}", "a", "${v}"), "${s}")
        values = {"${g}": "org", "${v}": "1.0", "${s}": "test"}
        result = dependency.interpolate(
            lambda value: values.get(value, value))
        self.assertEqual(str(result.coordinate), "org:a:1.0")
        self.assertEqual(result.scope, "test")

    def test_managed_version_and_scope(self):
        """Версия и scope берутся из dependencyManagement."""
        managed = Dependency(Coordinate("g", "a", "2.0"), "test")
        dependency = Dependency(Coordinate("g", "a"))
        result = dependency.managed_by({managed.key: managed})
        self.assertEqual(result.coordinate.version, "2.0")
        self.assertEqual(result.scope, "test")

    def test_own_values_win(self):
        """Явные версия и scope важнее управляемых."""
        managed = Dependency(Coordinate("g", "a", "2.0"), "test")
        dependency = Dependency(Coordinate("g", "a", "1.0"), "runtime")
        result = dependency.managed_by({managed.key: managed})
        self.assertEqual(result.coordinate.version, "1.0")
        self.assertEqual(result.scope, "runtime")

    def test_default_scope(self):
        """Без scope и управления - compile."""
        result = Dependency(Coordinate("g", "a", "1")).managed_by({})
        self.assertEqual(result.scope, "compile")

    def test_is_import(self):
        """Импорт BOM - scope import и type pom."""
        self.assertTrue(Dependency(Coordinate("g", "b", "1"), "import",
                                   dep_type="pom").is_import)
        self.assertFalse(Dependency(Coordinate("g", "b", "1"),
                                    "import").is_import)

    def test_describe(self):
        """Описание содержит координаты, scope и optional."""
        dependency = Dependency(Coordinate("g", "a", "1"), "test", True)
        self.assertEqual(dependency.describe(), "g:a:1 [test, optional]")
        unknown = Dependency(Coordinate("g", "a")).describe()
        self.assertEqual(unknown, "g:a:{} [compile]".format(UNKNOWN_VERSION))


if __name__ == "__main__":
    unittest.main()
