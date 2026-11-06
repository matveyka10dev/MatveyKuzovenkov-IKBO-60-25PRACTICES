"""Тесты источников данных для графа."""

import os
import unittest

from depviz.graph import SourceError, build_graph
from depviz.repository import NotFoundError
from depviz.resolver import Resolver
from depviz.sources import MavenSource, TestRepoSource

LOCAL_REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                          "examples", "maven-repo")
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


def maven_graph(name, name_filter=None):
    """Построить граф пакета из локального репозитория Maven.

    :param name: координаты пакета.
    :param name_filter: подстрока фильтра или None.
    :return: экземпляр DependencyGraph.
    """
    source = MavenSource(Resolver(REPO_URL, fetch=read_example))
    return build_graph(source, name, name_filter)


class TestRepoSourceTest(unittest.TestCase):
    """Проверка TestRepoSource."""

    def test_dependencies(self):
        """Зависимости возвращаются копией списка."""
        source = TestRepoSource({"A": ["B"]})
        self.assertEqual(source.root("A"), "A")
        self.assertEqual(source.dependencies("A"), ["B"])
        self.assertIsNot(source.dependencies("A"), source.packages["A"])

    def test_missing(self):
        """Отсутствующий пакет - ошибка."""
        with self.assertRaisesRegex(SourceError, "Z not found"):
            TestRepoSource({}).root("Z")


class MavenSourceTest(unittest.TestCase):
    """Проверка MavenSource на examples/maven-repo."""

    def test_transitive_graph(self):
        """Граф junit: версия из метаданных, транзитивная зависимость."""
        graph = maven_graph("junit:junit")
        self.assertEqual(graph.root, "junit:junit:4.13.2")
        self.assertEqual(graph.edges["org.hamcrest:hamcrest-library:1.3"],
                         ["org.hamcrest:hamcrest-core:1.3"])

    def test_scopes(self):
        """У корня - все зависимости, глубже - compile и runtime."""
        graph = maven_graph("org.example:demo-app:1.1.0")
        root_children = graph.edges[graph.root]
        self.assertIn("junit:junit:4.13.2", root_children)
        self.assertIn("org.apache.commons:commons-lang3:3.14.0",
                      root_children)
        self.assertEqual(graph.edges["org.example:demo-core:1.1.0"],
                         ["org.example:no-deps:1.0",
                          "org.example:runtime-lib:1.0"])
        self.assertEqual(graph.edges["org.apache.commons:commons-lang3:"
                                     "3.14.0"], [])
        self.assertEqual(graph.errors, {})

    def test_cycle(self):
        """Циклическая зависимость пакетов Maven."""
        graph = maven_graph("org.example:cycle-x:1.0")
        self.assertEqual(len(graph.cycles), 1)
        self.assertEqual(graph.cycles[0][0], graph.cycles[0][-1])

    def test_filter_by_group_and_artifact(self):
        """Фильтр сравнивается с groupId:artifactId."""
        graph = maven_graph("org.example:demo-app:1.1.0", "google")
        self.assertEqual(graph.filtered, ["com.google.guava:guava:"
                                          "33.0.0-jre"])
        self.assertFalse(any("google" in node for node in graph.nodes))

    def test_not_resolved(self):
        """Отсутствующий POM и диапазон версий - не разрешены."""
        graph = maven_graph("org.example:missing-dep:1.0")
        self.assertEqual(sorted(graph.errors), [
            "org.example:ghost:1.0", "org.example:ranged:[1.0,2.0)"])

    def test_missing_root(self):
        """Отсутствующий корневой пакет - ошибка."""
        for name in ("org.example:ghost:1.0", "org.example:ghost"):
            with self.subTest(name=name):
                with self.assertRaisesRegex(SourceError, "not found"):
                    maven_graph(name)


if __name__ == "__main__":
    unittest.main()
