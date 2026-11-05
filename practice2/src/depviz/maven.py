"""Модель пакетов Maven: координаты, зависимости, адреса файлов.

Файлы в репозитории Maven располагаются по схеме::

    <repo>/<groupId с / вместо .>/<artifactId>/maven-metadata.xml
    <repo>/<groupId с / вместо .>/<artifactId>/<version>/
        <artifactId>-<version>.pom
"""

COORDINATE_SEPARATOR = ":"
GROUP_SEPARATOR = "."
URL_SEPARATOR = "/"
VERSION_SEPARATOR = "-"
POM_EXTENSION = ".pom"
METADATA_FILE = "maven-metadata.xml"
SCOPE_COMPILE = "compile"
SCOPE_IMPORT = "import"
TYPE_JAR = "jar"
TYPE_POM = "pom"
UNKNOWN_VERSION = "<unknown version>"
OPTIONAL_MARK = "optional"


class Coordinate:
    """Координаты пакета Maven ``groupId:artifactId[:version]``."""

    def __init__(self, group_id, artifact_id, version=None):
        """Создать координаты.

        :param group_id: идентификатор группы.
        :param artifact_id: идентификатор артефакта.
        :param version: версия или None, если не задана.
        """
        self.group_id = group_id
        self.artifact_id = artifact_id
        self.version = version

    @classmethod
    def parse(cls, text):
        """Разобрать строку ``groupId:artifactId[:version]``.

        Строка должна быть заранее проверена (см. validation).

        :param text: координаты в виде строки.
        :return: экземпляр Coordinate.
        """
        return cls(*text.split(COORDINATE_SEPARATOR))

    @property
    def key(self):
        """Имя пакета без версии: ``groupId:artifactId``."""
        return self.group_id + COORDINATE_SEPARATOR + self.artifact_id

    def with_version(self, version):
        """Вернуть те же координаты с другой версией.

        :param version: новая версия.
        :return: новый экземпляр Coordinate.
        """
        return Coordinate(self.group_id, self.artifact_id, version)

    def __str__(self):
        """Вернуть координаты в виде ``groupId:artifactId[:version]``."""
        if self.version is None:
            return self.key
        return self.key + COORDINATE_SEPARATOR + self.version


class Dependency:
    """Зависимость из раздела ``dependencies`` файла POM."""

    def __init__(self, coordinate, scope=None, optional=False,
                 dep_type=TYPE_JAR):
        """Создать зависимость.

        :param coordinate: координаты пакета (версия может быть None).
        :param scope: область видимости (None - не указана в POM).
        :param optional: True для необязательной зависимости.
        :param dep_type: тип артефакта (``jar``, ``pom`` и т.п.).
        """
        self.coordinate = coordinate
        self.scope = scope
        self.optional = optional
        self.dep_type = dep_type

    @property
    def key(self):
        """Ключ для слияния: ``groupId:artifactId:type``."""
        return (self.coordinate.key + COORDINATE_SEPARATOR
                + self.dep_type)

    @property
    def is_import(self):
        """True для импорта BOM (``scope=import``, ``type=pom``)."""
        return self.scope == SCOPE_IMPORT and self.dep_type == TYPE_POM

    def interpolate(self, resolve):
        """Подставить значения свойств ``${...}`` во все поля.

        :param resolve: функция подстановки свойств в строку.
        :return: новая зависимость с подставленными значениями.
        """
        coordinate = Coordinate(resolve(self.coordinate.group_id),
                                resolve(self.coordinate.artifact_id),
                                resolve(self.coordinate.version))
        return Dependency(coordinate, resolve(self.scope), self.optional,
                          resolve(self.dep_type))

    def managed_by(self, managed):
        """Дополнить версию и область видимости из dependencyManagement.

        :param managed: словарь ``ключ -> Dependency`` из раздела
            dependencyManagement.
        :return: новая зависимость; область видимости по умолчанию
            ``compile``.
        """
        entry = managed.get(self.key)
        version = self.coordinate.version
        scope = self.scope
        if entry is not None:
            version = version or entry.coordinate.version
            scope = scope or entry.scope
        return Dependency(self.coordinate.with_version(version),
                          scope or SCOPE_COMPILE, self.optional,
                          self.dep_type)

    def describe(self):
        """Вернуть описание вида ``g:a:v [compile, optional]``.

        :return: строка для вывода на экран.
        """
        version = self.coordinate.version or UNKNOWN_VERSION
        marks = [self.scope or SCOPE_COMPILE]
        if self.optional:
            marks.append(OPTIONAL_MARK)
        return "{}{}{} [{}]".format(self.coordinate.key,
                                    COORDINATE_SEPARATOR, version,
                                    ", ".join(marks))


def artifact_url(base_url, coordinate):
    """Вернуть URL каталога артефакта в репозитории.

    :param base_url: URL репозитория.
    :param coordinate: координаты пакета.
    :return: URL вида ``<repo>/org/junit/junit``.
    """
    group_path = coordinate.group_id.replace(GROUP_SEPARATOR, URL_SEPARATOR)
    return URL_SEPARATOR.join([base_url.rstrip(URL_SEPARATOR), group_path,
                               coordinate.artifact_id])


def metadata_url(base_url, coordinate):
    """Вернуть URL файла maven-metadata.xml со списком версий.

    :param base_url: URL репозитория.
    :param coordinate: координаты пакета (версия не используется).
    :return: URL файла метаданных.
    """
    return artifact_url(base_url, coordinate) + URL_SEPARATOR + METADATA_FILE


def pom_url(base_url, coordinate):
    """Вернуть URL файла POM заданной версии пакета.

    :param base_url: URL репозитория.
    :param coordinate: координаты пакета с версией.
    :return: URL вида ``<repo>/junit/junit/4.13.2/junit-4.13.2.pom``.
    """
    file_name = (coordinate.artifact_id + VERSION_SEPARATOR
                 + coordinate.version + POM_EXTENSION)
    return URL_SEPARATOR.join([artifact_url(base_url, coordinate),
                               coordinate.version, file_name])
