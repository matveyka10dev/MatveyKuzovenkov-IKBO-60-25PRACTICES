"""Тесты формирования приглашения к вводу."""

import unittest

from shell_emu.osinfo import (build_prompt, get_hostname, get_username,
                              shorten_home)


class PromptTest(unittest.TestCase):
    """Проверка функций модуля osinfo."""

    def test_shorten_home_exact(self):
        """Домашний каталог заменяется на ~."""
        self.assertEqual(shorten_home("/home/ivan", "/home/ivan"), "~")

    def test_shorten_home_subdir(self):
        """Подкаталог домашнего каталога начинается с ~/."""
        self.assertEqual(shorten_home("/home/ivan/src", "/home/ivan"),
                         "~/src")

    def test_shorten_home_other(self):
        """Путь вне домашнего каталога не меняется."""
        self.assertEqual(shorten_home("/home/ivanov", "/home/ivan"),
                         "/home/ivanov")

    def test_prompt_uses_real_data(self):
        """Приглашение содержит имя пользователя и хоста ОС."""
        prompt = build_prompt("~")
        expected = "{}@{}:~$ ".format(get_username(), get_hostname())
        self.assertEqual(prompt, expected)


if __name__ == "__main__":
    unittest.main()
