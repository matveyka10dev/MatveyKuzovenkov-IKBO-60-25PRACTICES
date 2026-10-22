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
  config.py         параметры командной строки, отладочный вывод
  script.py         выполнение стартового скрипта
tests/              модульные тесты (unittest)
examples/scripts/   стартовые скрипты эмулятора
scripts/            скрипты ОС для тестирования эмулятора
run.sh, run.bat     скрипты запуска эмулятора
Makefile            цели run и test
```

## Функции и настройки

### Параметры командной строки

| Параметр        | Описание                                    |
|-----------------|---------------------------------------------|
| `--vfs PATH`    | путь к физическому расположению VFS         |
| `--script PATH` | путь к стартовому скрипту                   |
| `-h`, `--help`  | справка по параметрам                       |

На этапе 2 путь к VFS только сохраняется и выводится в отладочной
информации: файл не открывается и может не существовать. Загрузка VFS
появится на этапе 3.

При запуске эмулятор выводит отладочную информацию обо всех
параметрах (незаданные отмечаются `<not set>`):

```
[debug] emulator parameters:
[debug]   vfs_path    = examples/vfs/minimal.csv
[debug]   script_path = <not set>
```

Неизвестный параметр или параметр без значения - ошибка, эмулятор
завершается с кодом 2.

### Стартовый скрипт

Текстовый файл в кодировке UTF-8 (с BOM или без, как сохраняет
Блокнот Windows), по одной команде на строку. Пустые строки и
строки, начинающиеся с `#`, пропускаются. Каждая команда выводится
вместе с приглашением, затем её результат - получается диалог, как при
ручном вводе.

Скрипт **останавливается при первой ошибке** (команда вернула
ненулевой код): выводится сообщение
`[script] <файл>:<строка>: stopped, '<команда>' exited with status N`,
и эмулятор завершается с этим кодом. Если скрипт выполнен полностью,
эмулятор переходит в интерактивный режим. Команда `exit` в скрипте
завершает эмулятор сразу. Если файл скрипта нельзя прочитать,
эмулятор завершается с кодом 1.

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

Запуск с параметрами:

```sh
./run.sh --vfs examples/vfs/minimal.csv --script examples/scripts/stage2_ok.txt
```

```bat
run.bat --vfs examples\vfs\minimal.csv --script examples\scripts\stage2_ok.txt
```

Запуск модульных тестов:

```sh
python3 -m unittest discover -s tests -t . -v     # Linux / macOS
python -m unittest discover -s tests -t . -v      # Windows
make test                                         # через make
```

### Скрипты ОС для тестирования параметров

Каждый скрипт запускает эмулятор (иногда несколько раз), печатает
команду запуска, весь вывод эмулятора и код завершения. Ввод эмулятора
подключается к пустому устройству (`/dev/null` в Linux, `NUL` в
Windows), поэтому после стартового скрипта интерактивный режим сразу
получает конец ввода и эмулятор завершается сам.

| Linux / macOS                   | Windows                          | Что проверяет                     |
|---------------------------------|----------------------------------|-----------------------------------|
| `scripts/test_no_params.sh`     | `scripts\test_no_params.bat`     | запуск без параметров             |
| `scripts/test_vfs_param.sh`     | `scripts\test_vfs_param.bat`     | параметр `--vfs`                  |
| `scripts/test_script_param.sh`  | `scripts\test_script_param.bat`  | `--script`: успех, ошибка, `exit` |
| `scripts/test_all_params.sh`    | `scripts\test_all_params.bat`    | оба параметра в разном порядке    |
| `scripts/test_bad_params.sh`    | `scripts\test_bad_params.bat`    | `--help`, неверные параметры, нет файла |

Запуск одного скрипта:

```sh
sh scripts/test_script_param.sh          # Linux / macOS
```

```bat
scripts\test_script_param.bat           :: Windows (cmd)
```

Все скрипты подряд в Windows (cmd):

```bat
for %f in (scripts\*.bat) do call %f
```

Стартовые скрипты эмулятора лежат в `examples/scripts/`:

| Файл              | Содержимое                                          |
|-------------------|-----------------------------------------------------|
| `stage2_ok.txt`   | команды без ошибок; затем интерактивный режим       |
| `stage2_error.txt`| ошибка в середине: выполнение останавливается на ней |
| `stage2_exit.txt` | `exit 7` в середине: эмулятор завершается с кодом 7 |

## Примеры использования

```
$ ./run.sh
[debug] emulator parameters:
[debug]   vfs_path    = <not set>
[debug]   script_path = <not set>
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

Стартовый скрипт с ошибкой (`examples/scripts/stage2_error.txt`):

```
$ ./run.sh --script examples/scripts/stage2_error.txt
[debug] emulator parameters:
[debug]   vfs_path    = <not set>
[debug]   script_path = examples/scripts/stage2_error.txt
Shell emulator. Type 'exit' to quit.
ivan@laptop:~/shell-emulator$ ls -l
ls: [stub] args=['-l']
ivan@laptop:~/shell-emulator$ cd a b
cd: too many arguments
[script] examples/scripts/stage2_error.txt:5: stopped, 'cd a b' exited with status 1
$ echo $?
1
```

Стартовый скрипт с командой `exit` (`examples/scripts/stage2_exit.txt`):

```
$ ./run.sh --script examples/scripts/stage2_exit.txt
[debug] emulator parameters:
[debug]   vfs_path    = <not set>
[debug]   script_path = examples/scripts/stage2_exit.txt
Shell emulator. Type 'exit' to quit.
ivan@laptop:~/shell-emulator$ ls -a
ls: [stub] args=['-a']
ivan@laptop:~/shell-emulator$ exit 7
$ echo $?
7
```
