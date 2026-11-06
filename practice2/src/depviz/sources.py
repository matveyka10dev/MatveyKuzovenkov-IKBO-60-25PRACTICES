"""Источники данных о зависимостях для построения графа.

У обоих источников одинаковый набор методов:

* ``root(name)`` - проверить корневой пакет и вернуть его имя в графе;
* ``dependencies(name)`` - вернуть имена зависимостей пакета;
* ``package_name(name)`` - вернуть имя пакета для сравнения с фильтром.

Об ошибках источники сообщают исключением SourceError.
"""

from depviz.graph import SourceError
from depviz.maven import Coordinate, is_concrete_version
from depviz.resolver import ResolveError
from depviz.validation import package_id


class TestRepoSource:
    """Тестовый репозиторий, загруженный из файла описания графа."""

    def __init__(self, packages):
        """Создать источник.

        :param packages: словарь ``пакет -> список зависимостей``.
        """
        self.packages = packages

    def root(self, name):
        """Проверить, что анализируемый пакет есть в репозитории.

        :param name: имя пакета.
        :return: то же имя.
        :raises SourceError: если пакета нет.
        """
        self.dependencies(name)
        return name

    def dependencies(self, name):
        """Вернуть прямые зависимости пакета.

        :param name: имя пакета.
        :return: список имён зависимостей.
        :raises SourceError: если пакета нет в репозитории.
        """
        if name not in self.packages:
            raise SourceError("package {} not found in test "
                              "repository".format(name))
        return list(self.packages[name])

    def package_name(self, name):
        """Вернуть имя пакета для сравнения с фильтром.

        :param name: имя пакета.
        :return: то же имя.
        """
        return name


class MavenSource:
    """Репозиторий Maven, доступный по URL.

    Узлы графа - координаты ``groupId:artifactId:version``. Как и в
    ``mvn dependency:tree``, у анализируемого пакета учитываются все
    прямые зависимости, а у остальных пакетов - только транзитивные
    (``compile`` и ``runtime``, кроме ``optional``).
    """

    def __init__(self, resolver):
        """Создать источник.

        :param resolver: экземпляр Resolver для нужного репозитория.
        """
        self.resolver = resolver
        self.root_name = None

    def root(self, name):
        """Определить версию анализируемого пакета.

        :param name: координаты ``groupId:artifactId[:version]``.
        :return: координаты с версией.
        :raises SourceError: если версию не удалось определить.
        """
        coordinate = Coordinate.parse(name)
        if coordinate.version is None:
            try:
                coordinate = self.resolver.resolve_version(coordinate)
            except ResolveError as exc:
                raise SourceError(str(exc)) from None
        self.root_name = str(coordinate)
        return self.root_name

    def dependencies(self, name):
        """Вернуть зависимости пакета, которые входят в граф.

        :param name: координаты пакета с версией.
        :return: список координат зависимостей.
        :raises SourceError: если версия не точная или POM не получен.
        """
        coordinate = Coordinate.parse(name)
        if not is_concrete_version(coordinate.version):
            raise SourceError("version '{}' cannot be resolved".format(
                coordinate.version or ""))
        try:
            _, dependencies = self.resolver.direct_dependencies(coordinate)
        except ResolveError as exc:
            raise SourceError(str(exc)) from None
        if name != self.root_name:
            dependencies = [item for item in dependencies
                            if item.is_transitive]
        return [str(item.coordinate) for item in dependencies]

    def package_name(self, name):
        """Вернуть имя пакета без версии для сравнения с фильтром.

        :param name: координаты пакета.
        :return: ``groupId:artifactId``.
        """
        return package_id(name)
