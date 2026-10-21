# Эмулятор командной оболочки (вариант 17)

Эмулятор языка оболочки UNIX-подобной ОС с консольным интерфейсом (CLI).
Работа эмулятора максимально похожа на работу в командной строке:
приглашение к вводу строится из реальных данных ОС
(`username@hostname:~$`), аргументы разбираются с учётом кавычек,
ошибки выводятся в стиле bash.

Язык реализации: Python 3.8+ (только стандартная библиотека).

## Структура репозитория

```
src/shell_emu/      исходный код эмулятора
  __main__.py       запуск через python -m shell_emu
  app.py            точка входа
  shell.py          ядро: выполнение команд и цикл REPL
  lexer.py          разбор командной строки (кавычки, экранирование)
  commands.py       встроенные команды
  osinfo.py         данные ОС для приглашения к вводу
tests/              модульные тесты (unittest)
run.sh, run.bat     скрипты запуска эмулятора
Makefile            цели run и test
```

## Функции и настройки

### Приглашение к вводу

Формируется из реальных данных ОС: имя пользователя
(`getpass.getuser()`), короткое имя компьютера (`socket.gethostname()`)
и текущий каталог, в котором домашний каталог заменён на `~`:

```
ivan@laptop:~/projects$
```

### Разбор командной строки

| Конструкция          | Результат                          |
|----------------------|------------------------------------|
| `ls a   b`           | `['ls', 'a', 'b']`                 |
| `cd "My Documents"`  | `['cd', 'My Documents']`           |
| `cd 'a "b" c'`       | `['cd', 'a "b" c']`                |
| `ls "say \"hi\""`    | `['ls', 'say "hi"']`               |
| `cd my\ dir`         | `['cd', 'my dir']`                 |
| `ls a"b c"d`         | `['ls', 'ab cd']`                  |
| `ls ""`              | `['ls', '']`                       |
| `ls "abc`            | ошибка: незакрытая кавычка          |

### Команды

| Команда     | Описание                                                  |
|-------------|-----------------------------------------------------------|
| `ls [-la] [путь...]` | заглушка: проверяет опции, выводит имя и аргументы |
| `cd [путь]` | заглушка: выводит имя и аргументы, не более 1 аргумента   |
| `exit [n]`  | завершение работы с кодом `n` (по умолчанию - код последней команды) |

### Ошибки

| Ситуация                 | Сообщение                                       | Код |
|--------------------------|-------------------------------------------------|-----|
| Неизвестная команда      | `foo: command not found`                        | 127 |
| Незакрытая кавычка       | `emulator: syntax error: unexpected EOF ...`    | 2   |
| Неизвестная опция ls     | `ls: invalid option -- 'z'`                     | 2   |
| Лишние аргументы cd      | `cd: too many arguments`                        | 1   |
| Нечисловой аргумент exit | `exit: abc: numeric argument required`          | 2   |
| Лишние аргументы exit    | `exit: too many arguments`                      | 1   |

После ошибки эмулятор продолжает работу. Ctrl+C прерывает текущую
строку, Ctrl+D (конец ввода) завершает работу.

## Сборка и запуск

Сборка не требуется, нужен только Python 3.8+.

```sh
./run.sh              # Linux / macOS
run.bat               # Windows
make run              # через make
```

Запуск тестов:

```sh
python3 -m unittest discover -s tests -t . -v
# или
make test
```

## Примеры использования

```
$ ./run.sh
Shell emulator. Type 'exit' to quit.
ivan@laptop:~/shell-emulator$ ls -l "my dir" other
ls: [stub] args=['-l', 'my dir', 'other']
ivan@laptop:~/shell-emulator$ cd 'Program Files'
cd: [stub] args=['Program Files']
ivan@laptop:~/shell-emulator$ cd a b
cd: too many arguments
ivan@laptop:~/shell-emulator$ ls -z
ls: invalid option -- 'z'
ivan@laptop:~/shell-emulator$ foo
foo: command not found
ivan@laptop:~/shell-emulator$ ls "abc
emulator: syntax error: unexpected EOF while looking for matching `"'
ivan@laptop:~/shell-emulator$ exit abc
exit: abc: numeric argument required
ivan@laptop:~/shell-emulator$ exit 3
$ echo $?
3
```
