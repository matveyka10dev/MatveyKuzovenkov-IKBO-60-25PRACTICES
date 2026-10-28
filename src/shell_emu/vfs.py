"""Виртуальная файловая система (VFS), загружаемая из CSV-файла.

Формат CSV (первая строка - заголовок)::

    path,type,encoding,content
    /home/user/readme.txt,file,text,Hello
    /home/user/empty,dir,,
    /bin/tool,file,base64,f0VMRgIBAQ==

* ``path`` - абсолютный путь элемента. Вложенность задаётся самим путём:
  ``/a/b/c.txt`` лежит в каталоге ``b``, который лежит в ``a``.
  Промежуточные каталоги создаются автоматически, явно объявлять
  каталог нужно только если он пустой.
* ``type`` - ``dir`` (каталог) или ``file`` (файл).
* ``encoding`` - для файлов ``text`` (по умолчанию, UTF-8) или
  ``base64`` (двоичные данные); для каталогов пусто.
* ``content`` - содержимое файла; для каталогов пусто.

Файл читается в кодировке UTF-8 (с BOM или без). Разделитель полей -
запятая; поддерживается и точка с запятой, как сохраняет CSV русская
версия Excel (определяется по строке заголовка).

Файл VFS только читается: все операции выполняются в памяти.
"""

import base64
import binascii
import csv
import io

SEPARATOR = "/"
ROOT_PATH = "/"
CURRENT_DIR = "."
PARENT_DIR = ".."
CSV_HEADER = ["path", "type", "encoding", "content"]
CSV_ENCODING = "utf-8-sig"
COMMA = ","
SEMICOLON = ";"
TYPE_DIR = "dir"
TYPE_FILE = "file"
ENCODING_TEXT = "text"
ENCODING_BASE64 = "base64"
TEXT_ENCODINGS = ("", ENCODING_TEXT)
EMPTY_SOURCE = "<empty>"


class VfsError(Exception):
    """Ошибка загрузки VFS или обращения к её элементам."""


class VfsNode:
    """Элемент VFS: каталог или файл."""

    def __init__(self, name, is_dir, data=b""):
        """Создать элемент.

        :param name: имя элемента (пустая строка для корня).
        :param is_dir: True для каталога, False для файла.
        :param data: содержимое файла (bytes).
        """
        self.name = name
        self.is_dir = is_dir
        self.data = data
        self.children = {} if is_dir else None

    @property
    def size(self):
        """Размер содержимого файла в байтах (для каталога 0)."""
        return len(self.data)


def split_path(path):
    """Разбить путь на компоненты, отбросив пустые.

    :param path: путь вида ``/a/b`` или ``a/b``.
    :return: список компонентов пути.
    """
    return [part for part in path.split(SEPARATOR) if part]


def normalize_path(path, cwd=ROOT_PATH):
    """Привести путь к абсолютному виду с учётом ``.`` и ``..``.

    :param path: абсолютный или относительный путь.
    :param cwd: текущий каталог для относительных путей.
    :return: нормализованный абсолютный путь.
    """
    base = [] if path.startswith(SEPARATOR) else split_path(cwd)
    parts = list(base)
    for part in split_path(path):
        if part == PARENT_DIR:
            if parts:
                parts.pop()
        elif part != CURRENT_DIR:
            parts.append(part)
    return SEPARATOR + SEPARATOR.join(parts)


class Vfs:
    """Дерево VFS, хранящееся в памяти."""

    def __init__(self, source=EMPTY_SOURCE):
        """Создать пустую VFS, содержащую только корневой каталог.

        :param source: описание источника (путь к CSV-файлу).
        """
        self.source = source
        self.root = VfsNode("", is_dir=True)

    def make_dir(self, path):
        """Создать каталог (и все недостающие родительские).

        :param path: абсолютный путь каталога.
        :return: узел созданного или существующего каталога.
        :raises VfsError: если на пути встретился файл.
        """
        return self._ensure_dirs(_absolute_parts(path))

    def make_file(self, path, data):
        """Создать файл, при необходимости создав родительские каталоги.

        :param path: абсолютный путь файла.
        :param data: содержимое файла (bytes).
        :return: узел созданного файла.
        :raises VfsError: если путь занят или указывает на корень.
        """
        parts = _absolute_parts(path)
        if not parts:
            raise VfsError("root directory cannot be a file")
        parent = self._ensure_dirs(parts[:-1])
        name = parts[-1]
        if name in parent.children:
            raise VfsError("'{}' already exists".format(path))
        node = VfsNode(name, is_dir=False, data=data)
        parent.children[name] = node
        return node

    def lookup(self, path, cwd=ROOT_PATH):
        """Найти элемент VFS по пути.

        :param path: абсолютный или относительный путь.
        :param cwd: текущий каталог для относительных путей.
        :return: найденный узел.
        :raises VfsError: если элемент не найден.
        """
        node = self.root
        for part in split_path(normalize_path(path, cwd)):
            if not node.is_dir:
                raise VfsError("{}: Not a directory".format(path))
            node = node.children.get(part)
            if node is None:
                raise VfsError("{}: No such file or directory".format(path))
        return node

    def stats(self):
        """Посчитать статистику VFS.

        :return: словарь с ключами dirs, files, size, depth
            (корневой каталог не учитывается).
        """
        result = {"dirs": 0, "files": 0, "size": 0, "depth": 0}
        _collect_stats(self.root, 0, result)
        return result

    def _ensure_dirs(self, parts):
        """Пройти по компонентам пути, создавая недостающие каталоги.

        :param parts: компоненты абсолютного пути.
        :return: узел последнего каталога.
        :raises VfsError: если один из компонентов - файл.
        """
        node = self.root
        for index, part in enumerate(parts):
            child = node.children.get(part)
            if child is None:
                child = VfsNode(part, is_dir=True)
                node.children[part] = child
            elif not child.is_dir:
                prefix = SEPARATOR + SEPARATOR.join(parts[:index + 1])
                raise VfsError("'{}' is not a directory".format(prefix))
            node = child
        return node


def _absolute_parts(path):
    """Проверить путь из CSV и разбить его на компоненты.

    :param path: путь из CSV-файла.
    :return: список компонентов.
    :raises VfsError: если путь не абсолютный или содержит . или ..
    """
    if not path.startswith(SEPARATOR):
        raise VfsError("path '{}' must be absolute".format(path))
    parts = split_path(path)
    if CURRENT_DIR in parts or PARENT_DIR in parts:
        raise VfsError("path '{}' must not contain . or ..".format(path))
    return parts


def _collect_stats(node, depth, result):
    """Рекурсивно накопить статистику поддерева.

    :param node: текущий каталог.
    :param depth: глубина вложенности текущего каталога.
    :param result: словарь статистики (изменяется).
    """
    for child in node.children.values():
        result["depth"] = max(result["depth"], depth + 1)
        if child.is_dir:
            result["dirs"] += 1
            _collect_stats(child, depth + 1, result)
        else:
            result["files"] += 1
            result["size"] += child.size


def decode_content(encoding, content):
    """Преобразовать содержимое файла из CSV в байты.

    :param encoding: ``text``, ``base64`` или пустая строка.
    :param content: содержимое из CSV.
    :return: содержимое файла (bytes).
    :raises VfsError: при неизвестной кодировке или неверном base64.
    """
    if encoding in TEXT_ENCODINGS:
        return content.encode("utf-8")
    if encoding != ENCODING_BASE64:
        raise VfsError("unknown encoding '{}'".format(encoding))
    try:
        return base64.b64decode(content, validate=True)
    except (binascii.Error, ValueError):
        raise VfsError("invalid base64 content") from None


def add_csv_row(vfs, row):
    """Добавить в VFS элемент, описанный строкой CSV.

    :param vfs: заполняемая VFS.
    :param row: список полей строки CSV.
    :raises VfsError: при некорректной строке.
    """
    if len(row) != len(CSV_HEADER):
        raise VfsError("expected {} fields, got {}".format(
            len(CSV_HEADER), len(row)))
    path, kind, encoding, content = row
    if kind == TYPE_FILE:
        vfs.make_file(path, decode_content(encoding, content))
    elif kind == TYPE_DIR:
        if encoding or content:
            raise VfsError("directory '{}' cannot have content".format(path))
        vfs.make_dir(path)
    else:
        raise VfsError("unknown type '{}'".format(kind))


def read_csv_rows(path):
    """Прочитать все строки CSV-файла.

    :param path: путь к CSV-файлу.
    :return: список строк, каждая - список полей.
    :raises VfsError: если файл нельзя прочитать или разобрать.
    """
    try:
        with open(path, encoding=CSV_ENCODING, newline="") as file:
            text = file.read()
        reader = csv.reader(io.StringIO(text, newline=""),
                            delimiter=detect_delimiter(text), strict=True)
        return list(reader)
    except OSError as exc:
        raise VfsError("cannot open '{}': {}".format(
            path, exc.strerror)) from exc
    except (UnicodeDecodeError, csv.Error) as exc:
        raise VfsError("'{}' is not a valid UTF-8 CSV file: {}".format(
            path, exc)) from exc


def detect_delimiter(text):
    """Определить разделитель полей по строке заголовка.

    :param text: содержимое CSV-файла.
    :return: ``;``, если заголовок записан через точку с запятой,
        иначе ``,``.
    """
    first_line = text.split("\n", 1)[0].strip()
    if first_line == SEMICOLON.join(CSV_HEADER):
        return SEMICOLON
    return COMMA


def load_vfs(path):
    """Загрузить VFS из CSV-файла в память.

    :param path: путь к CSV-файлу (физическое расположение VFS).
    :return: экземпляр Vfs.
    :raises VfsError: при любой ошибке формата с номером строки.
    """
    rows = read_csv_rows(path)
    if not rows or rows[0] != CSV_HEADER:
        raise VfsError("{}:1: header must be '{}'".format(
            path, ",".join(CSV_HEADER)))
    vfs = Vfs(source=path)
    seen = set()
    for number, row in enumerate(rows[1:], start=2):
        if not any(field.strip() for field in row):
            continue
        key = normalize_path(row[0])
        try:
            if key in seen:
                raise VfsError("duplicate entry '{}'".format(row[0]))
            add_csv_row(vfs, row)
        except VfsError as exc:
            raise VfsError("{}:{}: {}".format(path, number, exc)) from None
        seen.add(key)
    return vfs
