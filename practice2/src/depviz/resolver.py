"""Получение прямых зависимостей пакета из репозитория Maven.

Чтобы получить итоговый (эффективный) список прямых зависимостей,
повторяется часть логики Maven:

1. если версия пакета не задана, она берётся из maven-metadata.xml;
2. загружается цепочка родительских POM (``parent``);
3. свойства, ``dependencyManagement`` и ``dependencies`` сливаются
   по цепочке: значения потомка важнее значений родителя;
4. подставляются свойства ``${...}``, включая ``project.version`` и
   ``project.groupId``;
5. импортируются BOM (``scope=import``, ``type=pom``) из
   ``dependencyManagement``;
6. недостающие версии и области видимости зависимостей берутся из
   ``dependencyManagement``.
"""

import re

from depviz.maven import metadata_url, pom_url
from depviz.pom import PomError, parse_latest_version, parse_pom
from depviz.repository import NotFoundError, RepositoryError, fetch_url

MAX_PARENT_DEPTH = 20
MAX_IMPORT_DEPTH = 10
MAX_INTERPOLATION_STEPS = 10
PROPERTY_PATTERN = re.compile(r"\$\{([^}]+)\}")


class ResolveError(Exception):
    """Ошибка получения зависимостей пакета."""


class EffectivePom:
    """POM с учётом наследования, свойств и импорта BOM."""

    def __init__(self, coordinate, managed, dependencies):
        """Создать эффективный POM.

        :param coordinate: координаты пакета.
        :param managed: словарь ``ключ -> Dependency``
            из dependencyManagement.
        :param dependencies: список прямых зависимостей.
        """
        self.coordinate = coordinate
        self.managed = managed
        self.dependencies = dependencies


def builtin_properties(pom):
    """Вернуть встроенные свойства ``project.*`` для POM.

    :param pom: экземпляр RawPom.
    :return: словарь свойств (без значений None).
    """
    values = {
        "project.groupId": pom.coordinate.group_id,
        "project.artifactId": pom.coordinate.artifact_id,
        "project.version": pom.coordinate.version,
    }
    if pom.parent is not None:
        values["project.parent.groupId"] = pom.parent.group_id
        values["project.parent.version"] = pom.parent.version
    for name in list(values):
        values[name.replace("project.", "pom.", 1)] = values[name]
    return {name: value for name, value in values.items()
            if value is not None}


def merge_chain(chain):
    """Слить свойства и зависимости по цепочке родительских POM.

    :param chain: список RawPom от пакета к самому дальнему родителю.
    :return: кортеж (свойства, управляемые зависимости, зависимости);
        управляемые зависимости и зависимости - словари по ключу.
    """
    properties = {}
    managed = {}
    dependencies = {}
    for pom in chain:
        for name, value in pom.properties.items():
            properties.setdefault(name, value)
        for dependency in pom.managed:
            managed.setdefault(dependency.key, dependency)
        for dependency in pom.dependencies:
            dependencies.setdefault(dependency.key, dependency)
    properties.update(builtin_properties(chain[0]))
    return properties, managed, dependencies


def make_interpolator(properties):
    """Создать функцию подстановки свойств ``${name}`` в строку.

    Подстановка повторяется, пока в значениях есть ссылки на другие
    свойства (не более MAX_INTERPOLATION_STEPS раз). Неизвестные
    свойства остаются как есть.

    :param properties: словарь свойств.
    :return: функция ``resolve(value) -> value``.
    """
    def replace(match):
        """Вернуть значение свойства или исходный текст ссылки."""
        return properties.get(match.group(1), match.group(0))

    def resolve(value):
        """Подставить свойства в строку (None остаётся None)."""
        if value is None:
            return None
        for _ in range(MAX_INTERPOLATION_STEPS):
            result = PROPERTY_PATTERN.sub(replace, value)
            if result == value:
                break
            value = result
        return value

    return resolve


class Resolver:
    """Получение POM и зависимостей пакетов из репозитория Maven."""

    def __init__(self, base_url, fetch=fetch_url):
        """Создать объект для работы с репозиторием.

        :param base_url: URL репозитория Maven.
        :param fetch: функция загрузки файла по URL (для тестов).
        """
        self.base_url = base_url
        self.fetch = fetch
        self._raw_cache = {}
        self._effective_cache = {}

    def direct_dependencies(self, coordinate):
        """Получить прямые зависимости пакета.

        :param coordinate: координаты пакета (версия может быть None).
        :return: кортеж (координаты с версией, список Dependency).
        :raises ResolveError: при любой ошибке загрузки или разбора.
        """
        if coordinate.version is None:
            coordinate = self.resolve_version(coordinate)
        return coordinate, self.effective(coordinate).dependencies

    def resolve_version(self, coordinate):
        """Подставить последнюю версию пакета из maven-metadata.xml.

        :param coordinate: координаты пакета без версии.
        :return: координаты с версией.
        :raises ResolveError: если пакет или его версии не найдены.
        """
        url = metadata_url(self.base_url, coordinate)
        data = self._download(url, coordinate)
        try:
            version = parse_latest_version(data, url)
        except PomError as exc:
            raise ResolveError(str(exc)) from None
        return coordinate.with_version(version)

    def load_raw(self, coordinate):
        """Загрузить и разобрать файл POM (с кэшированием).

        :param coordinate: координаты пакета с версией.
        :return: экземпляр RawPom.
        :raises ResolveError: если файл не найден или некорректен.
        """
        if coordinate.version is None:
            raise ResolveError("cannot load POM of {}: version is not "
                               "specified".format(coordinate))
        name = str(coordinate)
        if name not in self._raw_cache:
            url = pom_url(self.base_url, coordinate)
            data = self._download(url, coordinate)
            try:
                self._raw_cache[name] = parse_pom(data, url)
            except PomError as exc:
                raise ResolveError(str(exc)) from None
        return self._raw_cache[name]

    def parent_chain(self, coordinate):
        """Загрузить цепочку POM от пакета до самого дальнего родителя.

        :param coordinate: координаты пакета с версией.
        :return: список RawPom, первый элемент - сам пакет.
        :raises ResolveError: при циклической или слишком длинной
            цепочке родителей.
        """
        chain = []
        seen = set()
        current = coordinate
        while current is not None:
            if str(current) in seen:
                raise ResolveError("cyclic parent reference: {}".format(
                    " -> ".join(str(pom.coordinate) for pom in chain)
                    + " -> " + str(current)))
            if len(chain) >= MAX_PARENT_DEPTH:
                raise ResolveError("parent chain of {} is longer than "
                                   "{}".format(coordinate, MAX_PARENT_DEPTH))
            seen.add(str(current))
            chain.append(self._load_chain_item(chain, current))
            current = chain[-1].parent
        return chain

    def _load_chain_item(self, chain, coordinate):
        """Загрузить очередной POM цепочки родителей.

        :param chain: уже загруженная часть цепочки.
        :param coordinate: координаты загружаемого POM.
        :return: экземпляр RawPom.
        :raises ResolveError: с указанием потомка, если не загрузился
            родительский POM.
        """
        try:
            return self.load_raw(coordinate)
        except ResolveError as exc:
            if not chain:
                raise
            raise ResolveError("cannot load parent of {}: {}".format(
                chain[-1].coordinate, exc)) from None

    def effective(self, coordinate, depth=0):
        """Построить эффективный POM пакета.

        :param coordinate: координаты пакета с версией.
        :param depth: глубина вложенности импорта BOM.
        :return: экземпляр EffectivePom.
        :raises ResolveError: при ошибке загрузки или слишком глубоком
            импорте BOM.
        """
        name = str(coordinate)
        if name in self._effective_cache:
            return self._effective_cache[name]
        if depth > MAX_IMPORT_DEPTH:
            raise ResolveError("BOM imports are nested deeper than {} "
                               "at {}".format(MAX_IMPORT_DEPTH, name))
        chain = self.parent_chain(coordinate)
        properties, managed, dependencies = merge_chain(chain)
        resolve = make_interpolator(properties)
        managed = {key: entry.interpolate(resolve)
                   for key, entry in managed.items()}
        managed = self._import_boms(managed, depth)
        result = EffectivePom(
            coordinate, managed,
            [dependency.interpolate(resolve).managed_by(managed)
             for dependency in dependencies.values()])
        self._effective_cache[name] = result
        return result

    def _import_boms(self, managed, depth):
        """Заменить импорты BOM их управляемыми зависимостями.

        Явно объявленные записи важнее импортированных, из нескольких
        BOM побеждает объявленный раньше.

        :param managed: словарь управляемых зависимостей.
        :param depth: текущая глубина вложенности импорта.
        :return: новый словарь без записей-импортов.
        """
        result = {key: entry for key, entry in managed.items()
                  if not entry.is_import}
        for entry in managed.values():
            if entry.is_import:
                bom = self.effective(entry.coordinate, depth + 1)
                for key, imported in bom.managed.items():
                    result.setdefault(key, imported)
        return result

    def _download(self, url, coordinate):
        """Скачать файл, преобразовав ошибки в ResolveError.

        :param url: адрес файла.
        :param coordinate: координаты пакета для сообщения об ошибке.
        :return: содержимое файла (bytes).
        :raises ResolveError: при любой ошибке загрузки.
        """
        try:
            return self.fetch(url)
        except NotFoundError as exc:
            raise ResolveError("package {} not found in repository ({})"
                               .format(coordinate, exc)) from None
        except RepositoryError as exc:
            raise ResolveError(str(exc)) from None
