"""Тесты формирования приглашения к вводу."""

import unittest

from shell_emu.osinfo import build_prompt, get_hostname, get_username


class PromptTest(unittest.TestCase):
    """Проверка функций модуля osinfo."""

    def test_prompt_uses_real_data(self):
        """Приглашение содержит имя пользователя и хоста ОС."""
        prompt = build_prompt("/home")
        expected = "{}@{}:/home$ ".format(get_username(), get_hostname())
        self.assertEqual(prompt, expected)


if __name__ == "__main__":
    unittest.main()
