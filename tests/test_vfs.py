"""Тесты виртуальной файловой системы."""

import io
import os
import tempfile
import unittest

from shell_emu.shell import Shell
from shell_emu.vfs import (Vfs, VfsError, decode_content, load_vfs,
                           normalize_path)

HEADER = "path,type,encoding,content\n"


def write_csv(directory, text):
    """Записать CSV-файл VFS во временный каталог.

    :param directory: временный каталог.
    :param text: содержимое файла.
    :return: путь к файлу.
    """
    path = os.path.join(directory, "vfs.csv")
    with open(path, "w", encoding="utf-8", newline="") as file:
        file.write(text)
    return path


class NormalizePathTest(unittest.TestCase):
    """Проверка normalize_path."""

    def test_absolute(self):
        """Абсолютный путь очищается от лишних /."""
        self.assertEqual(normalize_path("//a///b/"), "/a/b")

    def test_relative(self):
        """Относительный путь отсчитывается от текущего каталога."""
        self.assertEqual(normalize_path("c", "/a/b"), "/a/b/c")

    def test_dots(self):
        """Компоненты . и .. обрабатываются, .. в корне - корень."""
        self.assertEqual(normalize_path("../../../x/./y", "/a"), "/x/y")


class VfsTreeTest(unittest.TestCase):
    """Проверка построения дерева в памяти."""

    def test_make_file_creates_parents(self):
        """Промежуточные каталоги создаются автоматически."""
        vfs = Vfs()
        vfs.make_file("/a/b/c.txt", b"hi")
        self.assertTrue(vfs.lookup("/a/b").is_dir)
        self.assertEqual(vfs.lookup("/a/b/c.txt").data, b"hi")

    def test_file_in_place_of_dir(self):
        """Файл нельзя использовать как каталог."""
        vfs = Vfs()
        vfs.make_file("/a", b"")
        with self.assertRaises(VfsError):
            vfs.make_file("/a/b", b"")

    def test_lookup_missing(self):
        """Поиск несуществующего пути - ошибка."""
        with self.assertRaises(VfsError):
            Vfs().lookup("/nope")

    def test_stats(self):
        """Статистика считает каталоги, файлы, размер и глубину."""
        vfs = Vfs()
        vfs.make_file("/a/b/c.txt", b"abc")
        vfs.make_dir("/d")
        stats = vfs.stats()
        self.assertEqual(stats, {"dirs": 3, "files": 1, "size": 3,
                                 "depth": 3})


class DecodeContentTest(unittest.TestCase):
    """Проверка decode_content."""

    def test_text(self):
        """Текст кодируется в UTF-8."""
        self.assertEqual(decode_content("", "привет"),
                         "привет".encode("utf-8"))

    def test_base64(self):
        """base64 декодируется в байты."""
        self.assertEqual(decode_content("base64", "AAEC"), b"\x00\x01\x02")

    def test_bad_base64(self):
        """Неверный base64 - ошибка."""
        with self.assertRaises(VfsError):
            decode_content("base64", "**")

    def test_unknown_encoding(self):
        """Неизвестная кодировка - ошибка."""
        with self.assertRaises(VfsError):
            decode_content("hex", "00")


class LoadVfsTest(unittest.TestCase):
    """Проверка загрузки VFS из CSV-файла."""

    def load_text(self, text):
        """Загрузить VFS из текста CSV.

        :param text: содержимое CSV-файла.
        :return: экземпляр Vfs.
        """
        with tempfile.TemporaryDirectory() as tmp:
            return load_vfs(write_csv(tmp, text))

    def test_minimal(self):
        """Файл из одного заголовка - пустая VFS."""
        stats = self.load_text(HEADER).stats()
        self.assertEqual(stats["dirs"] + stats["files"], 0)

    def test_nested_and_binary(self):
        """Вложенные элементы, многострочный текст и base64."""
        vfs = self.load_text(
            HEADER + '/a/b/c/d.txt,file,text,"x\ny"\n'
            "/bin/x,file,base64,f0VMRg==\n/empty,dir,,\n")
        self.assertEqual(vfs.lookup("/a/b/c/d.txt").data, b"x\ny")
        self.assertEqual(vfs.lookup("/bin/x").data, b"\x7fELF")
        self.assertEqual(vfs.lookup("/empty").children, {})

    def test_file_is_not_modified(self):
        """Загрузка не изменяет файл VFS."""
        with tempfile.TemporaryDirectory() as tmp:
            path = write_csv(tmp, HEADER + "/a,file,text,1\n")
            before = os.stat(path).st_mtime_ns
            load_vfs(path)
            self.assertEqual(os.stat(path).st_mtime_ns, before)

    def test_errors_have_line_numbers(self):
        """Ошибки формата содержат номер строки."""
        cases = [
            "bad,header\n",
            HEADER + "/a,link,,\n",
            HEADER + "a.txt,file,text,1\n",
            HEADER + "/a,file,text,1\n/a,file,text,2\n",
            HEADER + "/a,file,text\n",
            HEADER + "/d,dir,text,1\n",
            HEADER + "/../a,file,text,1\n",
            HEADER + "/,file,text,1\n",
        ]
        for text in cases:
            with self.subTest(text=text):
                with self.assertRaisesRegex(VfsError, r"vfs\.csv:\d+: "):
                    self.load_text(text)

    def test_excel_csv_with_bom_and_crlf(self):
        """CSV UTF-8 из Excel: BOM в начале и концы строк CRLF."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "vfs.csv")
            with open(path, "wb") as file:
                file.write(b"\xef\xbb\xbf" + HEADER.encode()
                           .replace(b"\n", b"\r\n")
                           + b'/a/b.txt,file,text,"x\r\ny"\r\n')
            vfs = load_vfs(path)
        self.assertEqual(vfs.lookup("/a/b.txt").data, b"x\r\ny")

    def test_semicolon_separator(self):
        """Разделитель ; (CSV русской версии Excel)."""
        vfs = self.load_text("path;type;encoding;content\n"
                             "/docs/a.txt;file;text;one, two\n"
                             "/empty;dir;;\n")
        self.assertEqual(vfs.lookup("/docs/a.txt").data, b"one, two")
        self.assertTrue(vfs.lookup("/empty").is_dir)

    def test_missing_file(self):
        """Отсутствующий файл - ошибка."""
        with self.assertRaisesRegex(VfsError, "cannot open"):
            load_vfs("/no/such/vfs.csv")


class VfsInfoCommandTest(unittest.TestCase):
    """Проверка служебной команды vfs-info."""

    def setUp(self):
        """Подготовить эмулятор с небольшой VFS."""
        vfs = Vfs(source="test.csv")
        vfs.make_file("/home/user/a.txt", b"12345")
        self.out = io.StringIO()
        self.err = io.StringIO()
        self.shell = Shell(out=self.out, err=self.err, vfs=vfs)

    def test_summary(self):
        """Без аргумента выводится сводка о VFS."""
        self.assertEqual(self.shell.execute("vfs-info"), 0)
        self.assertIn("source:      test.csv", self.out.getvalue())
        self.assertIn("files:       1", self.out.getvalue())

    def test_file_info(self):
        """Для файла выводится тип и размер."""
        self.shell.execute("vfs-info home/user/../user/a.txt")
        self.assertIn("path:    /home/user/a.txt", self.out.getvalue())
        self.assertIn("size:    5 bytes", self.out.getvalue())

    def test_dir_info(self):
        """Для каталога выводится число элементов."""
        self.shell.execute("vfs-info /home")
        self.assertIn("entries: 1", self.out.getvalue())

    def test_errors(self):
        """Несуществующий путь и лишние аргументы - ошибки."""
        self.assertNotEqual(self.shell.execute("vfs-info /x"), 0)
        self.assertNotEqual(self.shell.execute("vfs-info / /"), 0)
        self.assertIn("No such file", self.err.getvalue())
        self.assertIn("too many arguments", self.err.getvalue())

    def test_prompt_shows_vfs_dir(self):
        """Приглашение содержит текущий каталог VFS."""
        self.assertTrue(self.shell.prompt().endswith(":/$ "))


if __name__ == "__main__":
    unittest.main()
