"""Тесты построения и показа изображения графа."""

import os
import shutil
import subprocess
import unittest
import unittest.mock

from depviz.image import ImageError, open_image, render_image

DOT_TEXT = "digraph g { A -> B; }\n"
PNG_SIGNATURE = b"\x89PNG"


class RenderImageTest(unittest.TestCase):
    """Проверка render_image."""

    @unittest.skipIf(shutil.which("dot") is None, "Graphviz not installed")
    def test_png(self):
        """Graphviz создаёт файл PNG."""
        path = render_image(DOT_TEXT)
        try:
            with open(path, "rb") as file:
                self.assertEqual(file.read(len(PNG_SIGNATURE)),
                                 PNG_SIGNATURE)
        finally:
            os.remove(path)

    def test_no_graphviz(self):
        """Без Graphviz - понятная ошибка."""
        with unittest.mock.patch("shutil.which", return_value=None):
            with self.assertRaisesRegex(ImageError, "not installed"):
                render_image(DOT_TEXT)

    @unittest.skipIf(shutil.which("dot") is None, "Graphviz not installed")
    def test_bad_dot(self):
        """Ошибка в тексте DOT - ошибка dot."""
        with self.assertRaisesRegex(ImageError, "dot failed"):
            render_image("not a graph")


class OpenImageTest(unittest.TestCase):
    """Проверка open_image."""

    def test_linux_command(self):
        """В Linux изображение открывается командой xdg-open."""
        with unittest.mock.patch("sys.platform", "linux"), \
                unittest.mock.patch("subprocess.run") as run:
            open_image("g.png")
        self.assertEqual(run.call_args[0][0], ["xdg-open", "g.png"])

    def test_viewer_error(self):
        """Ошибка программы просмотра - ImageError."""
        error = subprocess.CalledProcessError(3, "xdg-open")
        with unittest.mock.patch("sys.platform", "linux"), \
                unittest.mock.patch("subprocess.run", side_effect=error):
            with self.assertRaisesRegex(ImageError, "cannot open image"):
                open_image("g.png")


if __name__ == "__main__":
    unittest.main()
