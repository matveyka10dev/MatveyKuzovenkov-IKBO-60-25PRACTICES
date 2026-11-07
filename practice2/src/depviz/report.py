"""Текстовый вывод графа зависимостей."""

INDENT = "  "
ARROW = " -> "
LIST_SEPARATOR = ", "
NONE = "none"
NOT_RESOLVED_MARK = " (not resolved)"


def format_node(graph, node):
    """Сформировать строку списка смежности для пакета.

    :param graph: экземпляр DependencyGraph.
    :param node: имя пакета.
    :return: строка вида ``A -> B, C``, ``D`` или ``F (not resolved)``.
    """
    if node in graph.errors:
        return node + NOT_RESOLVED_MARK
    children = graph.edges[node]
    if not children:
        return node
    return node + ARROW + LIST_SEPARATOR.join(children)


def format_section(title, items):
    """Сформировать раздел вывода со списком.

    :param title: заголовок раздела.
    :param items: строки раздела.
    :return: список строк; для пустого списка - ``title: none``.
    """
    if not items:
        return ["{}: {}".format(title, NONE)]
    return (["{} ({}):".format(title, len(items))]
            + [INDENT + item for item in items])


def format_load_order(graph):
    """Сформировать вывод порядка загрузки зависимостей.

    Каждый пакет выводится после всех своих зависимостей. Внутри цикла
    строгого порядка нет, поэтому найденные циклы выводятся отдельно.

    :param graph: экземпляр DependencyGraph.
    :return: список строк для вывода.
    """
    lines = ["Load order of {} (packages: {}):".format(
        graph.root, len(graph.load_order))]
    for number, node in enumerate(graph.load_order, start=1):
        mark = NOT_RESOLVED_MARK if node in graph.errors else ""
        lines.append("{}{}. {}{}".format(INDENT, number, node, mark))
    lines.extend(format_section(
        "Cycles", [ARROW.join(cycle) for cycle in graph.cycles]))
    return lines


def format_graph(graph, name_filter=None):
    """Сформировать вывод графа зависимостей.

    Выводятся: список смежности в порядке обхода DFS, найденные циклы,
    отфильтрованные пакеты (если задан фильтр) и пакеты, зависимости
    которых не удалось получить.

    :param graph: экземпляр DependencyGraph.
    :param name_filter: подстрока фильтра или None.
    :return: список строк для вывода.
    """
    lines = ["Dependency graph of {} (packages: {}, dependencies: {}):"
             .format(graph.root, len(graph.nodes), graph.edge_count)]
    lines.extend(INDENT + format_node(graph, node) for node in graph.nodes)
    lines.extend(format_section(
        "Cycles", [ARROW.join(cycle) for cycle in graph.cycles]))
    if name_filter is not None:
        lines.extend(format_section(
            "Filtered out by '{}'".format(name_filter), graph.filtered))
    if graph.errors:
        lines.extend(format_section(
            "Not resolved", ["{}: {}".format(node, message)
                             for node, message in graph.errors.items()]))
    return lines
