"""Текстовые представления графа: язык Graphviz и ASCII-дерево."""

DOT_INDENT = "    "
DOT_HEADER = ["digraph dependencies {",
              DOT_INDENT + "rankdir=LR;",
              DOT_INDENT + "node [shape=box];"]
DOT_FOOTER = "}"
ROOT_STYLE = " [style=bold]"
NOT_RESOLVED_STYLE = " [style=dashed]"
BRANCH = "+- "
LAST_BRANCH = "\\- "
PIPE = "|  "
SPACE = "   "
REPEATED_MARK = " (*)"
CYCLE_MARK = " (cycle)"
NOT_RESOLVED_MARK = " (not resolved)"


def dot_id(name):
    """Записать имя пакета как идентификатор Graphviz в кавычках.

    :param name: имя пакета.
    :return: строка вида ``"name"`` с экранированными символами.
    """
    return '"{}"'.format(name.replace("\\", "\\\\").replace('"', '\\"'))


def format_dot(graph):
    """Сформировать описание графа на языке Graphviz (DOT).

    Анализируемый пакет выделяется жирной рамкой, пакеты, данные о
    которых не удалось получить, - пунктирной.

    :param graph: экземпляр DependencyGraph.
    :return: список строк описания.
    """
    lines = list(DOT_HEADER)
    for node in graph.nodes:
        style = ""
        if node == graph.root:
            style = ROOT_STYLE
        elif node in graph.errors:
            style = NOT_RESOLVED_STYLE
        lines.append("{}{}{};".format(DOT_INDENT, dot_id(node), style))
    for node in graph.nodes:
        for child in graph.edges[node]:
            lines.append("{}{} -> {};".format(DOT_INDENT, dot_id(node),
                                              dot_id(child)))
    lines.append(DOT_FOOTER)
    return lines


def tree_mark(graph, node, path, expanded):
    """Вернуть отметку пакета в ASCII-дереве.

    :param graph: экземпляр DependencyGraph.
    :param node: имя пакета.
    :param path: пакеты на пути от корня до родителя узла.
    :param expanded: пакеты, поддерево которых уже выведено.
    :return: отметка или пустая строка, если поддерево нужно вывести.
    """
    if node in path:
        return CYCLE_MARK
    if node in expanded:
        return REPEATED_MARK
    if node in graph.errors:
        return NOT_RESOLVED_MARK
    return ""


def format_tree(graph):
    """Сформировать ASCII-дерево зависимостей (обход без рекурсии).

    Поддерево каждого пакета выводится один раз: повторное появление
    отмечается ``(*)``, зависимость, замыкающая цикл, - ``(cycle)``.

    :param graph: экземпляр DependencyGraph.
    :return: список строк дерева.
    """
    lines = [graph.root]
    expanded = {graph.root}
    stack = children_entries(graph, graph.root, "", (graph.root,))
    while stack:
        node, prefix, is_last, path = stack.pop()
        mark = tree_mark(graph, node, path, expanded)
        lines.append(prefix + (LAST_BRANCH if is_last else BRANCH)
                     + node + mark)
        if not mark:
            expanded.add(node)
            stack.extend(children_entries(
                graph, node, prefix + (SPACE if is_last else PIPE),
                path + (node,)))
    return lines


def children_entries(graph, node, prefix, path):
    """Подготовить элементы стека для зависимостей пакета.

    Элементы возвращаются в обратном порядке, чтобы при извлечении из
    стека зависимости выводились в исходном порядке.

    :param graph: экземпляр DependencyGraph.
    :param node: имя пакета.
    :param prefix: отступ строк зависимостей.
    :param path: пакеты на пути от корня до пакета включительно.
    :return: список кортежей (пакет, отступ, последний ли, путь).
    """
    children = graph.edges[node]
    entries = [(child, prefix, index == len(children) - 1, path)
               for index, child in enumerate(children)]
    entries.reverse()
    return entries
