"""Тесты выполнения команд эмулятором."""

import io
import unittest

from shell_emu.commands import STATUS_NOT_FOUND, STATUS_OK, STATUS_USAGE
from shell_emu.shell import Shell, run_interactive


def make_shell():
    """Создать эмулятор с выводом в строковые буферы.

    :return: кортеж (shell, out, err).
    """
    out = io.StringIO()
    err = io.StringIO()
    return Shell(out=out, err=err), out, err


class ExecuteTest(unittest.TestCase):
    """Проверка Shell.execute."""

    def test_ls_stub_prints_args(self):
        """Заглушка ls выводит имя и аргументы."""
        shell, out, _ = make_shell()
        status = shell.execute('ls -la "my dir"')
        self.assertEqual(status, STATUS_OK)
        self.assertEqual(out.getvalue(),
                         "ls: [stub] args=['-la', 'my dir']\n")

    def test_ls_invalid_option(self):
        """Неизвестная опция ls - ошибка с кодом 2."""
        shell, _, err = make_shell()
        self.assertEqual(shell.execute("ls -z"), STATUS_USAGE)
        self.assertIn("invalid option -- 'z'", err.getvalue())

    def test_ls_long_option(self):
        """Длинные опции ls не поддерживаются."""
        shell, _, err = make_shell()
        self.assertEqual(shell.execute("ls --all"), STATUS_USAGE)
        self.assertIn("unrecognized option '--all'", err.getvalue())

    def test_cd_stub(self):
        """Заглушка cd выводит имя и аргументы."""
        shell, out, _ = make_shell()
        self.assertEqual(shell.execute("cd /tmp"), STATUS_OK)
        self.assertEqual(out.getvalue(), "cd: [stub] args=['/tmp']\n")

    def test_cd_too_many_args(self):
        """cd с двумя аргументами - ошибка."""
        shell, _, err = make_shell()
        self.assertNotEqual(shell.execute("cd a b"), STATUS_OK)
        self.assertEqual(err.getvalue(), "cd: too many arguments\n")

    def test_unknown_command(self):
        """Неизвестная команда - код 127."""
        shell, _, err = make_shell()
        self.assertEqual(shell.execute("foo bar"), STATUS_NOT_FOUND)
        self.assertEqual(err.getvalue(), "foo: command not found\n")

    def test_syntax_error(self):
        """Незакрытая кавычка - синтаксическая ошибка."""
        shell, _, err = make_shell()
        self.assertEqual(shell.execute('ls "abc'), STATUS_USAGE)
        self.assertIn("syntax error", err.getvalue())

    def test_empty_line_keeps_status(self):
        """Пустая строка не меняет код последней команды."""
        shell, _, _ = make_shell()
        shell.execute("foo")
        self.assertEqual(shell.execute(""), STATUS_NOT_FOUND)


class ExitTest(unittest.TestCase):
    """Проверка команды exit."""

    def test_exit_without_args(self):
        """exit без аргументов завершает работу с кодом 0."""
        shell, _, _ = make_shell()
        shell.execute("exit")
        self.assertFalse(shell.running)
        self.assertEqual(shell.exit_code, STATUS_OK)

    def test_exit_with_code(self):
        """exit 3 завершает работу с кодом 3."""
        shell, _, _ = make_shell()
        shell.execute("exit 3")
        self.assertEqual(shell.exit_code, 3)

    def test_exit_code_wraps(self):
        """Код выхода берётся по модулю 256, как в bash."""
        shell, _, _ = make_shell()
        shell.execute("exit 257")
        self.assertEqual(shell.exit_code, 1)

    def test_exit_not_numeric(self):
        """Нечисловой аргумент - ошибка, работа продолжается."""
        shell, _, err = make_shell()
        self.assertEqual(shell.execute("exit abc"), STATUS_USAGE)
        self.assertTrue(shell.running)
        self.assertIn("numeric argument required", err.getvalue())

    def test_exit_too_many_args(self):
        """Лишние аргументы exit - ошибка, работа продолжается."""
        shell, _, _ = make_shell()
        shell.execute("exit 1 2")
        self.assertTrue(shell.running)


class InteractiveTest(unittest.TestCase):
    """Проверка интерактивного цикла."""

    def test_loop_until_exit(self):
        """Цикл выполняет команды до exit."""
        shell, out, _ = make_shell()
        lines = iter(["ls", "exit 5", "cd never"])
        code = run_interactive(shell, lambda _prompt: next(lines))
        self.assertEqual(code, 5)
        self.assertNotIn("never", out.getvalue())

    def test_loop_until_eof(self):
        """Конец ввода завершает цикл."""
        shell, out, _ = make_shell()

        def read_line(_prompt):
            """Имитировать нажатие Ctrl+D."""
            raise EOFError

        self.assertEqual(run_interactive(shell, read_line), STATUS_OK)
        self.assertEqual(out.getvalue(), "exit\n")


if __name__ == "__main__":
    unittest.main()
