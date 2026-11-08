"""Построение графа зависимостей алгоритмом DFS без рекурсии.

Граф строится обходом в глубину с явным стеком: каждый элемент стека -
пара (пакет, итератор по его зависимостям). Поэтому глубина графа не
ограничена глубиной стека вызовов Python.

Состояния пакета при обходе:

* не встречался - пакет ещё не обработан;
* VISITING - пакет лежит в стеке, его зависимости обходятся;
* DONE - все зависимости пакета обработаны.

Ребро в пакет со статусом VISITING означает цикл: путь от этого пакета
до вершины стека и обратно. Такой пакет повторно не обходится, поэтому
циклические зависимости не приводят к зацикливанию. Ребро в пакет со
статусом DONE - обычное повторное использование (ромб), обход тоже не
повторяется.

Источник данных (репозиторий Maven или тестовый репозиторий) должен
иметь методы ``root(name)``, ``dependencies(name)`` и
``package_name(name)``; об ошибках он сообщает исключением SourceError.
"""

VISITING = "visiting"
DONE = "done"


class SourceError(Exception):
    """Ошибка получения зависимостей пакета из источника данных."""


class DependencyGraph:
    """Граф зависимостей с результатами обхода."""

    def __init__(self, root):
        """Создать пустой граф.

        :param root: имя корневого (анализируемого) пакета.
        """
        self.root = root
        self.edges = {}
        self.cycles = []
        self.filtered = []
        self.errors = {}

    @property
    def nodes(self):
        """Список пакетов в порядке обнаружения при обходе."""
        return list(self.edges)

    @property
    def edge_count(self):
        """Число рёбер (зависимостей) в графе."""
        return sum(len(children) for children in self.edges.values())


class GraphBuilder:
    """Построение графа зависимостей обходом в глубину без рекурсии."""

    def __init__(self, source, name_filter=None):
        """Создать построитель графа.

        :param source: источник данных о зависимостях.
        :param name_filter: подстрока: пакеты, имя которых её содержит,
            не учитываются (None - без фильтрации).
        """
        self.source = source
        self.name_filter = name_filter
        self.graph = None
        self.state = {}

    def build(self, root_name):
        """Построить граф зависимостей пакета.

        :param root_name: имя анализируемого пакета.
        :return: экземпляр DependencyGraph.
        :raises SourceError: если не удалось получить сам пакет.
        """
        self.graph = DependencyGraph(self.source.root(root_name))
        self.state = {}
        stack = [self._enter(self.graph.root)]
        while stack:
            node, children = stack[-1]
            child = next(children, None)
            if child is None:
                self.state[node] = DONE
                stack.pop()
            elif child not in self.state:
                stack.append(self._enter(child))
            elif self.state[child] == VISITING:
                self.graph.cycles.append(cycle_path(stack, child))
        return self.graph

    def _enter(self, node):
        """Начать обработку пакета: получить его зависимости.

        :param node: имя пакета.
        :return: элемент стека (пакет, итератор по зависимостям).
        """
        self.state[node] = VISITING
        children = self._children(node)
        self.graph.edges[node] = children
        return node, iter(children)

    def _children(self, node):
        """Получить зависимости пакета с учётом фильтра.

        Ошибка получения зависимостей корня прерывает построение графа,
        ошибка для остальных пакетов запоминается в графе.

        :param node: имя пакета.
        :return: список имён зависимостей без повторов.
        :raises SourceError: если не удалось получить корневой пакет.
        """
        try:
            names = self.source.dependencies(node)
        except SourceError as exc:
            if node == self.graph.root:
                raise
            self.graph.errors[node] = str(exc)
            return []
        children = []
        for name in names:
            if name in children:
                continue
            if self._is_filtered(name):
                if name not in self.graph.filtered:
                    self.graph.filtered.append(name)
                continue
            children.append(name)
        return children

    def _is_filtered(self, name):
        """Проверить, исключается ли пакет фильтром.

        :param name: имя пакета.
        :return: True, если имя пакета содержит подстроку фильтра.
        """
        return (self.name_filter is not None
                and self.name_filter in self.source.package_name(name))


def cycle_path(stack, node):
    """Вернуть путь цикла, замыкающегося на пакете из стека.

    :param stack: стек обхода (пары пакет, итератор).
    :param node: пакет из стека, в который ведёт обратное ребро.
    :return: список имён вида ``[A, B, C, A]``.
    """
    names = [name for name, _ in stack]
    return names[names.index(node):] + [node]


def build_graph(source, root_name, name_filter=None):
    """Построить граф зависимостей пакета.

    :param source: источник данных о зависимостях.
    :param root_name: имя анализируемого пакета.
    :param name_filter: подстрока для исключения пакетов или None.
    :return: экземпляр DependencyGraph.
    :raises SourceError: если не удалось получить сам пакет.
    """
    return GraphBuilder(source, name_filter).build(root_name)
