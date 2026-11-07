"""Параметры инструмента, задаваемые опциями командной строки."""

import argparse

PROG_NAME = "depviz"
UNSET_VALUES = (None, False)


class Config:
    """Набор параметров, настраиваемых пользователем."""

    def __init__(self, package=None, repo=None, test_mode=False,
                 ascii_tree=False, name_filter=None, load_order=False):
        """Создать конфигурацию.

        :param package: имя анализируемого пакета.
        :param repo: URL репозитория или путь к файлу тестового
            репозитория (None - значение по умолчанию).
        :param test_mode: True - режим работы с тестовым репозиторием.
        :param ascii_tree: True - вывод зависимостей ASCII-деревом.
        :param name_filter: подстрока для фильтрации пакетов или None.
        :param load_order: True - вывод порядка загрузки зависимостей.
        """
        self.package = package
        self.repo = repo
        self.test_mode = test_mode
        self.ascii_tree = ascii_tree
        self.name_filter = name_filter
        self.load_order = load_order


class StoreOnce(argparse.Action):
    """Действие argparse: сохранить значение, запретив повтор опции."""

    def __call__(self, parser, namespace, values, option_string=None):
        """Сохранить значение опции.

        :param parser: парсер, вызвавший действие.
        :param namespace: пространство имён с результатами разбора.
        :param values: значение опции.
        :param option_string: имя опции в командной строке.
        """
        if getattr(namespace, self.dest) not in UNSET_VALUES:
            parser.error("argument {}: specified more than once".format(
                option_string))
        setattr(namespace, self.dest, self.convert(values))

    def convert(self, values):
        """Преобразовать значение опции перед сохранением.

        :param values: значение из командной строки.
        :return: сохраняемое значение.
        """
        return values


class FlagOnce(StoreOnce):
    """Действие argparse: флаг без значения, повтор запрещён."""

    def __init__(self, option_strings, dest, **kwargs):
        """Создать действие-флаг.

        :param option_strings: имена опции.
        :param dest: имя атрибута в результатах разбора.
        :param kwargs: прочие параметры argparse.Action.
        """
        kwargs.setdefault("default", False)
        super().__init__(option_strings, dest, nargs=0, **kwargs)

    def convert(self, values):
        """Вернуть значение флага.

        :param values: пустой список (у флага нет значения).
        :return: True.
        """
        return True


def build_arg_parser():
    """Создать парсер опций командной строки.

    :return: экземпляр argparse.ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        prog=PROG_NAME,
        description="Визуализация графа зависимостей пакетов Maven.")
    parser.add_argument(
        "--package", "-p", required=True, action=StoreOnce, metavar="NAME",
        help="имя анализируемого пакета: groupId:artifactId[:version], "
             "в тестовом режиме - заглавные латинские буквы")
    parser.add_argument(
        "--repo", "-r", action=StoreOnce, metavar="URL|PATH",
        help="URL репозитория Maven или путь к файлу тестового "
             "репозитория")
    parser.add_argument(
        "--test-mode", "-t", dest="test_mode", action=FlagOnce,
        help="режим работы с тестовым репозиторием")
    parser.add_argument(
        "--ascii-tree", "-a", dest="ascii_tree", action=FlagOnce,
        help="вывод зависимостей в формате ASCII-дерева")
    parser.add_argument(
        "--filter", "-f", dest="name_filter", action=StoreOnce,
        metavar="SUBSTRING",
        help="не учитывать пакеты, имя которых содержит подстроку")
    parser.add_argument(
        "--load-order", "-l", dest="load_order", action=FlagOnce,
        help="вывод порядка загрузки зависимостей")
    return parser


def parse_args(argv=None):
    """Разобрать опции командной строки.

    При синтаксической ошибке argparse выводит сообщение и завершает
    процесс с кодом 2.

    :param argv: список аргументов (по умолчанию sys.argv[1:]).
    :return: экземпляр Config.
    """
    namespace = build_arg_parser().parse_args(argv)
    return Config(namespace.package, namespace.repo, namespace.test_mode,
                  namespace.ascii_tree, namespace.name_filter,
                  namespace.load_order)
