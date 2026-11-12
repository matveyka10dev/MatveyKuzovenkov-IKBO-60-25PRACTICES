"""Разбор XML-файлов Maven: POM и maven-metadata.xml.

Используется только стандартный модуль xml.etree.ElementTree.
Пространство имён ``http://maven.apache.org/POM/4.0.0`` отбрасывается,
поэтому файлы с ним и без него разбираются одинаково.
"""

from xml.etree.ElementTree import ParseError, fromstring

from depviz.maven import TYPE_JAR, Coordinate, Dependency

NAMESPACE_END = "}"
POM_ROOT = "project"
METADATA_ROOT = "metadata"
OPTIONAL_TRUE = "true"


class PomError(Exception):
    """Ошибка разбора файла POM или метаданных."""


class RawPom:
    """Содержимое файла POM без учёта наследования и свойств."""

    def __init__(self, coordinate, parent, properties):
        """Создать описание POM.

        :param coordinate: координаты пакета (группа и версия могут
            быть унаследованы от родителя).
        :param parent: координаты родительского POM или None.
        :param properties: словарь свойств из раздела ``properties``.
        """
        self.coordinate = coordinate
        self.parent = parent
        self.properties = properties
        self.dependencies = []
        self.managed = []


def parse_xml(data, source):
    """Разобрать XML и убрать пространства имён из имён тегов.

    :param data: содержимое файла (bytes).
    :param source: URL файла для сообщений об ошибках.
    :return: корневой элемент.
    :raises PomError: если файл не является корректным XML.
    """
    try:
        root = fromstring(data)
    except ParseError as exc:
        raise PomError("{}: invalid XML: {}".format(source, exc)) from None
    for element in root.iter():
        if isinstance(element.tag, str) and NAMESPACE_END in element.tag:
            element.tag = element.tag.split(NAMESPACE_END, 1)[1]
    return root


def child_text(element, name):
    """Вернуть текст дочернего элемента без пробелов по краям.

    :param element: родительский элемент.
    :param name: имя дочернего элемента.
    :return: текст или None, если элемента нет или он пустой.
    """
    child = element.find(name)
    if child is None or child.text is None:
        return None
    return child.text.strip() or None


def parse_coordinate(element, source):
    """Прочитать groupId, artifactId и version элемента.

    :param element: элемент ``dependency`` или ``parent``.
    :param source: URL файла для сообщений об ошибках.
    :return: экземпляр Coordinate.
    :raises PomError: если нет groupId или artifactId.
    """
    group_id = child_text(element, "groupId")
    artifact_id = child_text(element, "artifactId")
    if group_id is None or artifact_id is None:
        raise PomError("{}: <{}> without groupId or artifactId".format(
            source, element.tag))
    return Coordinate(group_id, artifact_id, child_text(element, "version"))


def parse_dependencies(root, path, source):
    """Прочитать список зависимостей по пути внутри POM.

    :param root: корневой элемент POM.
    :param path: путь к контейнеру, например ``dependencies``.
    :param source: URL файла для сообщений об ошибках.
    :return: список Dependency (пустой, если раздела нет).
    """
    container = root.find(path)
    if container is None:
        return []
    return [Dependency(parse_coordinate(item, source),
                       child_text(item, "scope"),
                       child_text(item, "optional") == OPTIONAL_TRUE,
                       child_text(item, "type") or TYPE_JAR)
            for item in container.findall("dependency")]


def parse_properties(root):
    """Прочитать раздел ``properties``.

    :param root: корневой элемент POM.
    :return: словарь ``имя -> значение``.
    """
    container = root.find("properties")
    if container is None:
        return {}
    return {item.tag: (item.text or "").strip() for item in container
            if isinstance(item.tag, str)}


def parse_pom(data, source):
    """Разобрать файл POM.

    Учитываются только зависимости самого проекта (``dependencies``)
    и раздел ``dependencyManagement``; зависимости плагинов сборки и
    профилей не являются зависимостями пакета.

    :param data: содержимое файла (bytes).
    :param source: URL файла для сообщений об ошибках.
    :return: экземпляр RawPom.
    :raises PomError: при ошибке формата.
    """
    root = parse_xml(data, source)
    if root.tag != POM_ROOT:
        raise PomError("{}: root element is <{}>, expected <{}>".format(
            source, root.tag, POM_ROOT))
    parent_element = root.find("parent")
    parent = None
    if parent_element is not None:
        parent = parse_coordinate(parent_element, source)
    artifact_id = child_text(root, "artifactId")
    if artifact_id is None:
        raise PomError("{}: no <artifactId>".format(source))
    group_id = child_text(root, "groupId") or (parent and parent.group_id)
    version = child_text(root, "version") or (parent and parent.version)
    pom = RawPom(Coordinate(group_id, artifact_id, version), parent,
                 parse_properties(root))
    pom.dependencies = parse_dependencies(root, "dependencies", source)
    pom.managed = parse_dependencies(
        root, "dependencyManagement/dependencies", source)
    return pom


def parse_latest_version(data, source):
    """Найти последнюю версию пакета в maven-metadata.xml.

    Порядок поиска: ``release``, ``latest``, последний элемент списка
    ``versions``.

    :param data: содержимое файла (bytes).
    :param source: URL файла для сообщений об ошибках.
    :return: строка версии.
    :raises PomError: если версий нет или формат неверный.
    """
    root = parse_xml(data, source)
    if root.tag != METADATA_ROOT:
        raise PomError("{}: root element is <{}>, expected <{}>".format(
            source, root.tag, METADATA_ROOT))
    versioning = root.find("versioning")
    if versioning is not None:
        version = (child_text(versioning, "release")
                   or child_text(versioning, "latest"))
        versions = versioning.findall("versions/version")
        if version is None and versions:
            version = (versions[-1].text or "").strip() or None
        if version is not None:
            return version
    raise PomError("{}: no versions found".format(source))
