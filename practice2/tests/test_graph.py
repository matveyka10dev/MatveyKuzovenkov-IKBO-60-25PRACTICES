"""Тесты построения графа зависимостей."""

import sys
import unittest

from depviz.graph import SourceError, build_graph


class DictSource:
    """Источник данных из словаря ``пакет -> зависимости``."""

    def __init__(self, packages):
        """Создать источник.

        :param packages: словарь зависимостей.
        """
        self.packages = packages
        self.requests = []

    def root(self, name):
        """Вернуть имя корневого пакета.

        :param name: имя пакета.
        :return: то же имя.
        """
        return name

    def dependencies(self, name):
        """Вернуть зависимости пакета.

        :param name: имя пакета.
        :return: список зависимостей.
        :raises SourceError: если пакета нет.
        """
        self.requests.append(name)
        if name not in self.packages:
            raise SourceError("no " + name)
        return self.packages[name]

    def package_name(self, name):
        """Вернуть имя пакета для фильтра.

        :param name: имя пакета.
        :return: то же имя.
        """
        return name


def graph_of(packages, root="A", name_filter=None):
    """Построить граф по словарю зависимостей.

    :param packages: словарь зависимостей.
    :param root: корневой пакет.
    :param name_filter: подстрока фильтра или None.
    :return: экземпляр DependencyGraph.
    """
    return build_graph(DictSource(packages), root, name_filter)


class BuildGraphTest(unittest.TestCase):
    """Проверка build_graph."""

    def test_dfs_order_and_diamond(self):
        """Пакеты обходятся в глубину, общий пакет - один раз."""
        source = DictSource({"A": ["B", "C"], "B": ["D"], "C": ["D"],
                             "D": []})
        graph = build_graph(source, "A")
        self.assertEqual(graph.nodes, ["A", "B", "D", "C"])
        self.assertEqual(graph.edge_count, 4)
        self.assertEqual(graph.cycles, [])
        self.assertEqual(source.requests, ["A", "B", "D", "C"])

    def test_cycle(self):
        """Цикл находится и не приводит к зацикливанию."""
        graph = graph_of({"A": ["B"], "B": ["C"], "C": ["A", "D"],
                          "D": []})
        self.assertEqual(graph.cycles, [["A", "B", "C", "A"]])
        self.assertEqual(graph.edges["C"], ["A", "D"])

    def test_self_cycle(self):
        """Зависимость пакета от самого себя - цикл из одного пакета."""
        graph = graph_of({"A": ["A"]})
        self.assertEqual(graph.cycles, [["A", "A"]])

    def test_several_cycles(self):
        """Находятся все циклы, в том числе вложенные."""
        graph = graph_of({"A": ["B"], "B": ["C", "D"], "C": ["A"],
                          "D": ["E"], "E": ["D", "B"]})
        self.assertEqual(graph.cycles, [["A", "B", "C", "A"],
                                        ["D", "E", "D"],
                                        ["B", "D", "E", "B"]])

    def test_diamond_is_not_cycle(self):
        """Повторный путь к обработанному пакету - не цикл."""
        graph = graph_of({"A": ["B", "C"], "B": ["C"], "C": []})
        self.assertEqual(graph.cycles, [])

    def test_deep_chain_without_recursion(self):
        """Глубина графа больше предела рекурсии Python."""
        depth = sys.getrecursionlimit() * 2
        packages = {str(index): [str(index + 1)] for index in range(depth)}
        packages[str(depth)] = []
        graph = graph_of(packages, root="0")
        self.assertEqual(len(graph.nodes), depth + 1)

    def test_filter(self):
        """Отфильтрованные пакеты и их поддеревья не учитываются."""
        graph = graph_of({"APP": ["LOG", "WEB"], "LOG": ["CORE"],
                          "WEB": ["CORE"], "CORE": []}, "APP", "LO")
        self.assertEqual(graph.nodes, ["APP", "WEB", "CORE"])
        self.assertEqual(graph.filtered, ["LOG"])

    def test_filter_breaks_cycle(self):
        """Фильтр может разорвать цикл."""
        graph = graph_of({"A": ["B"], "B": ["A"]}, name_filter="B")
        self.assertEqual(graph.cycles, [])
        self.assertEqual(graph.nodes, ["A"])

    def test_duplicate_dependencies(self):
        """Повторы в списке зависимостей учитываются один раз."""
        graph = graph_of({"A": ["B", "B"], "B": []})
        self.assertEqual(graph.edges["A"], ["B"])

    def test_missing_package(self):
        """Отсутствующий пакет запоминается, обход продолжается."""
        graph = graph_of({"A": ["X", "B"], "B": []})
        self.assertEqual(graph.nodes, ["A", "X", "B"])
        self.assertEqual(graph.errors, {"X": "no X"})

    def test_missing_root(self):
        """Отсутствие корневого пакета - ошибка."""
        with self.assertRaisesRegex(SourceError, "no A"):
            graph_of({})


if __name__ == "__main__":
    unittest.main()
