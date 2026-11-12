"""Тесты текстовых представлений графа."""

import unittest

from depviz.graph import DependencyGraph
from depviz.report import dot_id, format_dot, format_tree


def make_graph(root, edges, errors=None):
    """Создать граф с заданными рёбрами.

    :param root: корневой пакет.
    :param edges: словарь ``пакет -> зависимости`` в порядке обхода.
    :param errors: словарь неразрешённых пакетов или None.
    :return: экземпляр DependencyGraph.
    """
    graph = DependencyGraph(root)
    graph.edges = edges
    graph.errors = errors or {}
    return graph


class FormatDotTest(unittest.TestCase):
    """Проверка описания графа на языке Graphviz."""

    def test_graph(self):
        """Узлы, стили корня и неразрешённых пакетов, рёбра."""
        graph = make_graph("A", {"A": ["B", "X"], "B": ["A"], "X": []},
                           {"X": "no X"})
        self.assertEqual(format_dot(graph), [
            "digraph dependencies {",
            "    rankdir=LR;",
            "    node [shape=box];",
            '    "A" [style=bold];',
            '    "B";',
            '    "X" [style=dashed];',
            '    "A" -> "B";',
            '    "A" -> "X";',
            '    "B" -> "A";',
            "}",
        ])

    def test_escaping(self):
        """Кавычки и обратная косая черта экранируются."""
        self.assertEqual(dot_id('a"b\\c'), '"a\\"b\\\\c"')


class FormatTreeTest(unittest.TestCase):
    """Проверка ASCII-дерева."""

    def test_tree(self):
        """Ветви, повторы (*) и последний элемент уровня."""
        graph = make_graph("A", {"A": ["B", "C"], "B": ["D"],
                                 "D": [], "C": ["D", "E"], "E": []})
        self.assertEqual(format_tree(graph), [
            "A",
            "+- B",
            "|  \\- D",
            "\\- C",
            "   +- D (*)",
            "   \\- E",
        ])

    def test_cycle_and_not_resolved(self):
        """Цикл и неразрешённый пакет отмечаются и не раскрываются."""
        graph = make_graph("A", {"A": ["B", "X"], "B": ["A"], "X": []},
                           {"X": "no X"})
        self.assertEqual(format_tree(graph), [
            "A",
            "+- B",
            "|  \\- A (cycle)",
            "\\- X (not resolved)",
        ])

    def test_single_node(self):
        """Пакет без зависимостей - одна строка."""
        self.assertEqual(format_tree(make_graph("A", {"A": []})), ["A"])


if __name__ == "__main__":
    unittest.main()
