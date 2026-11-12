"""Тесты получения прямых зависимостей (без сети)."""

import unittest

from depviz.maven import Coordinate
from depviz.repository import NotFoundError, RepositoryError
from depviz.resolver import ResolveError, Resolver, make_interpolator

REPO = "http://repo"


def pom(body):
    """Сформировать файл POM.

    :param body: XML внутри элемента project.
    :return: содержимое файла (bytes).
    """
    return "<project>{}</project>".format(body).encode("utf-8")


def gav(group_id, artifact_id, version):
    """Сформировать элементы groupId, artifactId и version.

    :param group_id: идентификатор группы.
    :param artifact_id: идентификатор артефакта.
    :param version: версия.
    :return: фрагмент XML.
    """
    return ("<groupId>{}</groupId><artifactId>{}</artifactId>"
            "<version>{}</version>".format(group_id, artifact_id, version))


def dependency(group_id, artifact_id, extra=""):
    """Сформировать элемент dependency.

    :param group_id: идентификатор группы.
    :param artifact_id: идентификатор артефакта.
    :param extra: дополнительные элементы (version, scope и т.п.).
    :return: фрагмент XML.
    """
    return ("<dependency><groupId>{}</groupId><artifactId>{}</artifactId>"
            "{}</dependency>".format(group_id, artifact_id, extra))


FILES = {
    "http://repo/g/app/maven-metadata.xml":
        b"<metadata><versioning><release>2.0</release></versioning>"
        b"</metadata>",
    "http://repo/g/app/2.0/app-2.0.pom": pom(
        "<parent>" + gav("g", "parent", "1") + "</parent>"
        "<artifactId>app</artifactId><version>2.0</version>"
        "<properties><lib.version>1.5</lib.version></properties>"
        "<dependencies>"
        + dependency("g", "lib", "<version>${lib.version}</version>")
        + dependency("g", "managed")
        + dependency("g", "from-bom")
        + dependency("${project.groupId}", "core",
                     "<version>${project.version}</version>")
        + "</dependencies>"),
    "http://repo/g/parent/1/parent-1.pom": pom(
        gav("g", "parent", "1")
        + "<properties><lib.version>1.0</lib.version>"
        "<managed.version>3.0</managed.version></properties>"
        "<dependencyManagement><dependencies>"
        + dependency("g", "managed",
                     "<version>${managed.version}</version>"
                     "<scope>runtime</scope>")
        + dependency("g", "bom", "<version>1</version><type>pom</type>"
                                 "<scope>import</scope>")
        + "</dependencies></dependencyManagement>"
        "<dependencies>"
        + dependency("g", "inherited", "<version>9</version>"
                                       "<scope>test</scope>")
        + "</dependencies>"),
    "http://repo/g/bom/1/bom-1.pom": pom(
        gav("g", "bom", "1")
        + "<dependencyManagement><dependencies>"
        + dependency("g", "from-bom", "<version>7.0</version>")
        + dependency("g", "managed", "<version>0.1</version>")
        + "</dependencies></dependencyManagement>"),
    "http://repo/g/loop-a/1/loop-a-1.pom": pom(
        "<parent>" + gav("g", "loop-b", "1") + "</parent>"
        "<artifactId>loop-a</artifactId>"),
    "http://repo/g/loop-b/1/loop-b-1.pom": pom(
        "<parent>" + gav("g", "loop-a", "1") + "</parent>"
        "<artifactId>loop-b</artifactId>"),
    "http://repo/g/orphan/1/orphan-1.pom": pom(
        "<parent>" + gav("g", "missing", "1") + "</parent>"
        "<artifactId>orphan</artifactId>"),
    "http://repo/g/bad/1/bad-1.pom": b"<project>",
}


def fake_fetch(url):
    """Вернуть файл из словаря FILES вместо загрузки по сети.

    :param url: адрес файла.
    :return: содержимое файла.
    :raises NotFoundError: если файла нет в словаре.
    """
    if url not in FILES:
        raise NotFoundError(url + ": HTTP 404 Not Found")
    return FILES[url]


def describe(resolver, text):
    """Получить зависимости и вернуть их описания.

    :param resolver: экземпляр Resolver.
    :param text: координаты пакета.
    :return: кортеж (координаты с версией, список описаний).
    """
    coordinate, dependencies = resolver.direct_dependencies(
        Coordinate.parse(text))
    return str(coordinate), [item.describe() for item in dependencies]


class ResolverTest(unittest.TestCase):
    """Проверка Resolver на поддельном репозитории."""

    @property
    def resolver(self):
        """Resolver с поддельной загрузкой файлов (новый для каждого теста)."""
        return Resolver(REPO, fetch=fake_fetch)

    def test_effective_dependencies(self):
        """Наследование, свойства, управление версиями и импорт BOM."""
        coordinate, lines = describe(self.resolver, "g:app:2.0")
        self.assertEqual(coordinate, "g:app:2.0")
        self.assertEqual(lines, [
            "g:lib:1.5 [compile]",
            "g:managed:3.0 [runtime]",
            "g:from-bom:7.0 [compile]",
            "g:core:2.0 [compile]",
            "g:inherited:9 [test]",
        ])

    def test_latest_version(self):
        """Без версии используется release из maven-metadata.xml."""
        coordinate, _ = describe(self.resolver, "g:app")
        self.assertEqual(coordinate, "g:app:2.0")

    def test_not_found(self):
        """Нет POM или метаданных - ошибка с именем пакета."""
        for text in ("g:none:1", "g:none"):
            with self.subTest(text=text):
                with self.assertRaisesRegex(ResolveError, "g:none"):
                    describe(self.resolver, text)

    def test_parent_errors(self):
        """Цикл родителей и отсутствующий родитель - ошибки."""
        with self.assertRaisesRegex(ResolveError, "cyclic parent"):
            describe(self.resolver, "g:loop-a:1")
        with self.assertRaisesRegex(ResolveError, "parent of g:orphan:1"):
            describe(self.resolver, "g:orphan:1")

    def test_bad_pom(self):
        """Некорректный XML - ошибка."""
        with self.assertRaisesRegex(ResolveError, "invalid XML"):
            describe(self.resolver, "g:bad:1")

    def test_network_error(self):
        """Ошибка сети превращается в ResolveError."""
        def failing_fetch(url):
            """Имитировать отказ соединения."""
            raise RepositoryError(url + ": cannot connect")

        resolver = Resolver(REPO, fetch=failing_fetch)
        with self.assertRaisesRegex(ResolveError, "cannot connect"):
            describe(resolver, "g:app:2.0")

    def test_pom_is_downloaded_once(self):
        """Файлы POM кэшируются."""
        calls = []

        def counting_fetch(url):
            """Посчитать обращения к репозиторию."""
            calls.append(url)
            return fake_fetch(url)

        resolver = Resolver(REPO, fetch=counting_fetch)
        describe(resolver, "g:app:2.0")
        describe(resolver, "g:app:2.0")
        self.assertEqual(len(calls), len(set(calls)))


class InterpolatorTest(unittest.TestCase):
    """Проверка подстановки свойств."""

    def test_nested_and_unknown(self):
        """Вложенные ссылки раскрываются, неизвестные остаются."""
        resolve = make_interpolator({"a": "${b}", "b": "1"})
        self.assertEqual(resolve("v${a}-${x}"), "v1-${x}")
        self.assertIsNone(resolve(None))

    def test_self_reference(self):
        """Циклическая ссылка не приводит к зависанию."""
        resolve = make_interpolator({"a": "${a}x"})
        self.assertTrue(resolve("${a}").startswith("${a}"))


if __name__ == "__main__":
    unittest.main()
