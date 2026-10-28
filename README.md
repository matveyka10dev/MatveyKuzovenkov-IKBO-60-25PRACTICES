# Эмулятор командной оболочки (вариант 17)

Эмулятор языка оболочки UNIX-подобной ОС с консольным интерфейсом (CLI).
Работа эмулятора максимально похожа на работу в командной строке:
приглашение к вводу строится из реальных данных ОС
(`username@hostname:/$`), аргументы разбираются с учётом кавычек,
ошибки выводятся в стиле bash. Файлы и каталоги берутся из виртуальной
файловой системы (VFS), которая загружается из CSV-файла в память.

Язык реализации: Python 3.8+ (только стандартная библиотека).

## Структура репозитория

```
src/shell_emu/      исходный код эмулятора
  __main__.py       запуск через python -m shell_emu
  app.py            точка входа: параметры, VFS, скрипт, REPL
  shell.py          ядро: выполнение команд и цикл REPL
  lexer.py          разбор командной строки (кавычки, экранирование)
  commands.py       встроенные команды
  osinfo.py         данные ОС для приглашения к вводу
  config.py         параметры командной строки, отладочный вывод
  script.py         выполнение стартового скрипта
  vfs.py            виртуальная файловая система из CSV
tests/              модульные тесты (unittest)
examples/vfs/       примеры VFS (broken/ - некорректные файлы)
examples/scripts/   стартовые скрипты эмулятора (errors/ - ошибки)
scripts/            скрипты ОС для тестирования (.bat и .sh)
run.sh, run.bat     скрипты запуска эмулятора
Makefile            цели run и test
```

## Функции и настройки

### Параметры командной строки

| Параметр        | Описание                                    |
|-----------------|---------------------------------------------|
| `--vfs PATH`    | путь к физическому расположению VFS (CSV)   |
| `--script PATH` | путь к стартовому скрипту                   |
| `-h`, `--help`  | справка по параметрам                       |

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

### Виртуальная файловая система (VFS)

Источник VFS - CSV-файл, путь к которому задаётся параметром `--vfs`.
Файл только читается: дерево каталогов и файлов строится в памяти, все
операции выполняются над ним, сам CSV-файл не изменяется. Без
параметра `--vfs` используется пустая VFS (только корень `/`).

Формат - CSV с заголовком из четырёх столбцов:

```csv
path,type,encoding,content
/etc/hostname,file,text,vfs-host
/etc/os-release,file,text,"NAME=""EmuOS""
VERSION=""1.0"""
/bin/ls,file,base64,f0VMRgIBAQ==
/home/user/docs/projects/emulator/main.py,file,text,"print(""hello"")"
/home/guest,dir,,
```

| Столбец    | Значение                                                   |
|------------|------------------------------------------------------------|
| `path`     | абсолютный путь элемента (без `.` и `..`)                  |
| `type`     | `file` - файл, `dir` - каталог                             |
| `encoding` | для файлов: `text` (или пусто) - текст UTF-8, `base64` - двоичные данные; для каталогов пусто |
| `content`  | содержимое файла; для каталогов пусто                      |

**Вложенность** задаётся полным путём: строка
`/home/user/docs/report.txt` означает файл `report.txt` в каталоге
`docs`, который лежит в `user`, который лежит в `home`. Промежуточные
каталоги создаются автоматически, поэтому явно объявлять нужно только
пустые каталоги (`/home/guest,dir,,`). Текст с запятыми, кавычками и
переводами строк записывается по правилам CSV (в двойных кавычках,
кавычка внутри удваивается).

Файл читается в кодировке UTF-8 с BOM или без него. Разделитель полей -
запятая; поддерживается и точка с запятой (так сохраняет «CSV UTF-8»
русская версия Excel) - он определяется по строке заголовка.

Ошибки формата выводятся с номером строки, после чего эмулятор
завершается с кодом 1:

| Ошибка                     | Сообщение                                          |
|----------------------------|----------------------------------------------------|
| файл не найден             | `cannot open '...': No such file or directory`     |
| неверный заголовок         | `f.csv:1: header must be 'path,type,encoding,content'` |
| неверное число столбцов    | `f.csv:N: expected 4 fields, got 3`                |
| неизвестный тип            | `f.csv:N: unknown type 'symlink'`                  |
| неизвестная кодировка      | `f.csv:N: unknown encoding 'utf-16'`               |
| неверный base64            | `f.csv:N: invalid base64 content`                  |
| относительный путь         | `f.csv:N: path 'a/b' must be absolute`             |
| файл на месте каталога     | `f.csv:N: '/etc/hostname' is not a directory`      |
| повторный путь             | `f.csv:N: duplicate entry '/a.txt'`                |
| содержимое у каталога      | `f.csv:N: directory '/docs' cannot have content`   |
| незакрытая кавычка, не UTF-8 | `'f.csv' is not a valid UTF-8 CSV file: ...`     |

Примеры VFS в `examples/vfs/`:

| Файл           | Содержимое                                               |
|----------------|----------------------------------------------------------|
| `minimal.csv`  | минимальная VFS: только заголовок (пустой корень)        |
| `files.csv`    | несколько файлов: текст, многострочный текст, имя с пробелом, пустой файл, PNG в base64 |
| `excel.csv`    | VFS в формате Excel: BOM, концы строк CRLF, разделитель `;` |
| `deep.csv`     | 12 каталогов, 9 файлов, вложенность до 6 уровней          |
| `broken/*.csv` | некорректные файлы для проверки обработки ошибок         |

### Приглашение к вводу

Формируется из реальных данных ОС - имени пользователя
(`getpass.getuser()`) и короткого имени компьютера
(`socket.gethostname()`) - и текущего каталога в VFS:

```
ivan@laptop:/$
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
| `ls "abc`            | ошибка: незакрытая кавычка         |

### Команды

| Команда              | Описание                                         |
|----------------------|--------------------------------------------------|
| `ls [-la] [путь...]` | заглушка: проверяет опции, выводит имя и аргументы |
| `cd [путь]`          | заглушка: выводит имя и аргументы, не более 1 аргумента |
| `exit [n]`           | завершение работы с кодом `n` (по умолчанию - код последней команды) |
| `vfs-info [путь]`    | служебная: сводка о VFS или сведения об элементе |

Команда `vfs-info` без аргумента выводит источник VFS, число каталогов
и файлов, общий размер и максимальную глубину вложенности. С аргументом
выводит тип элемента и его размер (для файла) или число элементов (для
каталога). Путь может быть абсолютным или относительным, допускаются
`.` и `..`.

### Ошибки команд

| Ситуация                 | Сообщение                                       | Код |
|--------------------------|-------------------------------------------------|-----|
| Неизвестная команда      | `foo: command not found`                        | 127 |
| Незакрытая кавычка       | `emulator: syntax error: unexpected EOF ...`    | 2   |
| Неизвестная опция ls     | `ls: invalid option -- 'z'`                     | 2   |
| Лишние аргументы cd      | `cd: too many arguments`                        | 1   |
| Нечисловой аргумент exit | `exit: abc: numeric argument required`          | 2   |
| Лишние аргументы exit    | `exit: too many arguments`                      | 1   |
| Нет пути в VFS           | `vfs-info: /x: No such file or directory`       | 1   |
| Файл как каталог в VFS   | `vfs-info: /etc/hostname/x: Not a directory`    | 1   |
| Лишние аргументы vfs-info | `vfs-info: too many arguments`                 | 1   |

В интерактивном режиме после ошибки эмулятор продолжает работу.
Ctrl+C прерывает текущую строку, Ctrl+D (в Windows Ctrl+Z, Enter)
завершает работу.

## Сборка и запуск

Сборка не требуется, нужен только Python 3.8+.

```sh
./run.sh              # Linux / macOS
run.bat               # Windows
make run              # через make
```

Запуск с параметрами:

```sh
./run.sh --vfs examples/vfs/deep.csv --script examples/scripts/stage3_all.txt
```

```bat
run.bat --vfs examples\vfs\deep.csv --script examples\scripts\stage3_all.txt
```

Запуск модульных тестов:

```sh
python3 -m unittest discover -s tests -t . -v     # Linux / macOS
python -m unittest discover -s tests -t . -v      # Windows
make test                                         # через make
```

### Скрипты ОС для тестирования

Каждый скрипт запускает эмулятор (иногда несколько раз), печатает
команду запуска, весь вывод эмулятора и код завершения. Ввод эмулятора
подключается к пустому устройству (`/dev/null` в Linux, `NUL` в
Windows), поэтому после стартового скрипта интерактивный режим сразу
получает конец ввода и эмулятор завершается сам. Для каждого скрипта
есть версия для Windows (`.bat`) и для Linux / macOS (`.sh`).

Параметры командной строки (этап 2):

| Скрипт                    | Что проверяет                           |
|---------------------------|-----------------------------------------|
| `scripts/test_no_params`  | запуск без параметров                   |
| `scripts/test_vfs_param`  | параметр `--vfs`                        |
| `scripts/test_script_param` | `--script`: успех, ошибка, `exit`     |
| `scripts/test_all_params` | оба параметра в разном порядке          |
| `scripts/test_bad_params` | `--help`, неверные параметры, нет файла |

Работа с VFS и все команды (этап 3):

| Скрипт                       | Что проверяет                          |
|------------------------------|----------------------------------------|
| `scripts/test_vfs_minimal`   | минимальная VFS и запуск без `--vfs`   |
| `scripts/test_vfs_files`     | VFS из нескольких файлов (и формат Excel) |
| `scripts/test_vfs_deep`      | VFS с 3+ уровнями вложенности          |
| `scripts/test_vfs_broken`    | все некорректные CSV и отсутствующий файл |
| `scripts/test_stage3_all`    | стартовый скрипт `stage3_all.txt` со всеми командами этапов 1-3 |
| `scripts/test_stage3_errors` | скрипты `examples/scripts/errors/*.txt`: каждая ошибка команд |

Запуск одного скрипта:

```sh
sh scripts/test_stage3_all.sh            # Linux / macOS
```

```bat
scripts\test_stage3_all.bat              :: Windows (cmd)
```

Все скрипты подряд:

```sh
for f in scripts/*.sh; do sh "$f"; done              # Linux / macOS
```

```bat
for %f in (scripts\*.bat) do call %f                 :: Windows (cmd)
```

Так как стартовый скрипт останавливается при первой ошибке, в
`stage3_all.txt` ошибка стоит последней, а остальные ошибки команд
вынесены в отдельные короткие скрипты `examples/scripts/errors/*.txt`.

Стартовые скрипты эмулятора в `examples/scripts/`:

| Файл               | Содержимое                                          |
|--------------------|-----------------------------------------------------|
| `stage2_ok.txt`    | команды без ошибок; затем интерактивный режим       |
| `stage2_error.txt` | ошибка в середине: выполнение останавливается на ней |
| `stage2_exit.txt`  | `exit 7` в середине: эмулятор завершается с кодом 7 |
| `vfs_*.txt`        | проверка разных вариантов VFS командой `vfs-info`   |
| `stage3_all.txt`   | все команды этапов 1-3, в конце - ошибка            |
| `errors/*.txt`     | по одной ошибке команд в каждом файле               |

## Примеры использования

Интерактивный режим:

```
$ ./run.sh
[debug] emulator parameters:
[debug]   vfs_path    = <not set>
[debug]   script_path = <not set>
[vfs] no VFS file given, using empty VFS
Shell emulator. Type 'exit' to quit.
ivan@laptop:/$ ls -l "my dir" other
ls: [stub] args=['-l', 'my dir', 'other']
ivan@laptop:/$ cd 'Program Files'
cd: [stub] args=['Program Files']
ivan@laptop:/$ cd a b
cd: too many arguments
ivan@laptop:/$ ls -z
ls: invalid option -- 'z'
ivan@laptop:/$ foo
foo: command not found
ivan@laptop:/$ ls "abc
emulator: syntax error: unexpected EOF while looking for matching `"'
ivan@laptop:/$ exit abc
exit: abc: numeric argument required
ivan@laptop:/$ exit 3
$ echo $?
3
```

Работа с VFS:

```
$ ./run.sh --vfs examples/vfs/deep.csv
[debug] emulator parameters:
[debug]   vfs_path    = examples/vfs/deep.csv
[debug]   script_path = <not set>
[vfs] loaded 'examples/vfs/deep.csv': 12 directories, 9 files
Shell emulator. Type 'exit' to quit.
ivan@laptop:/$ vfs-info
source:      examples/vfs/deep.csv
directories: 12
files:       9
total size:  116 bytes
max depth:   6
ivan@laptop:/$ vfs-info home/user/docs/../readme.txt
path:    /home/user/readme.txt
type:    file
size:    24 bytes
ivan@laptop:/$ vfs-info /home/guest
path:    /home/guest
type:    directory
entries: 0
ivan@laptop:/$ vfs-info /etc/passwd
vfs-info: /etc/passwd: No such file or directory
ivan@laptop:/$ exit
```

Стартовый скрипт с ошибкой (`examples/scripts/stage2_error.txt`):

```
$ ./run.sh --script examples/scripts/stage2_error.txt
[debug] emulator parameters:
[debug]   vfs_path    = <not set>
[debug]   script_path = examples/scripts/stage2_error.txt
[vfs] no VFS file given, using empty VFS
Shell emulator. Type 'exit' to quit.
ivan@laptop:/$ ls -l
ls: [stub] args=['-l']
ivan@laptop:/$ cd a b
cd: too many arguments
[script] examples/scripts/stage2_error.txt:5: stopped, 'cd a b' exited with status 1
$ echo $?
1
```

Некорректная VFS:

```
$ ./run.sh --vfs examples/vfs/broken/bad_base64.csv
[debug] emulator parameters:
[debug]   vfs_path    = examples/vfs/broken/bad_base64.csv
[debug]   script_path = <not set>
emulator: vfs: examples/vfs/broken/bad_base64.csv:2: invalid base64 content
$ echo $?
1
```
