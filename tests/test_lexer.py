"""Тесты разбора командной строки."""

import unittest

from shell_emu.lexer import ParseError, tokenize


class TokenizeTest(unittest.TestCase):
    """Проверка функции tokenize."""

    def test_empty_line(self):
        """Пустая строка и пробелы дают пустой список."""
        self.assertEqual(tokenize(""), [])
        self.assertEqual(tokenize("   \t "), [])

    def test_simple_words(self):
        """Слова разделяются любым количеством пробелов."""
        self.assertEqual(tokenize("ls  -l   /home"), ["ls", "-l", "/home"])

    def test_double_quotes(self):
        """Пробелы внутри двойных кавычек сохраняются."""
        self.assertEqual(tokenize('cd "My Documents"'),
                         ["cd", "My Documents"])

    def test_single_quotes_literal(self):
        """В одинарных кавычках обратная косая черта не работает."""
        self.assertEqual(tokenize(r"ls 'a\"b'"), ["ls", 'a\\"b'])

    def test_escape_in_double_quotes(self):
        """В двойных кавычках экранируются кавычка и косая черта."""
        self.assertEqual(tokenize(r'ls "say \"hi\" \\ \n"'),
                         ["ls", 'say "hi" \\ \\n'])

    def test_escape_outside_quotes(self):
        """Вне кавычек \\ экранирует пробел."""
        self.assertEqual(tokenize(r"cd my\ dir"), ["cd", "my dir"])

    def test_glued_quotes(self):
        """Кавычки склеиваются с соседним текстом в один аргумент."""
        self.assertEqual(tokenize('a"b c"\'d e\'f'), ["ab cd ef"])

    def test_empty_quoted_argument(self):
        """Пустые кавычки дают пустой аргумент."""
        self.assertEqual(tokenize('ls "" \'\''), ["ls", "", ""])

    def test_unclosed_double_quote(self):
        """Незакрытая двойная кавычка - ошибка."""
        with self.assertRaises(ParseError):
            tokenize('cd "abc')

    def test_unclosed_single_quote(self):
        """Незакрытая одинарная кавычка - ошибка."""
        with self.assertRaises(ParseError):
            tokenize("cd 'abc")

    def test_trailing_backslash(self):
        """Обратная косая черта в конце строки - ошибка."""
        with self.assertRaises(ParseError):
            tokenize("ls abc\\")


if __name__ == "__main__":
    unittest.main()
