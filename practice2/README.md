# Визуализатор графа зависимостей (вариант 17)

Инструмент командной строки (CLI) для визуализации графа зависимостей
пакетов Java (Maven). Готовые менеджеры пакетов и библиотеки для
получения зависимостей не используются.

**Этап 1. Минимальный прототип с конфигурацией.** Приложение принимает
пять параметров в виде опций командной строки, проверяет каждый из них
и выводит все параметры в формате ключ-значение. Для любого параметра
выводится понятное сообщение об ошибке.

Язык реализации: Python 3.8+ (только стандартная библиотека).

## Структура репозитория

```
src/depviz/         исходный код
  __main__.py       запуск через python -m depviz
  app.py            точка входа: опции, проверка, вывод параметров
  config.py         опции командной строки, вывод ключ-значение
  validation.py     проверка значений параметров
tests/              модульные тесты (unittest)
examples/repos/     пример файла тестового репозитория
scripts/            скрипты ОС для демонстрации (.sh и .bat)
run.sh, run.bat     скрипты запуска
Makefile            цели run и test
```

## Функции и настройки

### Параметры командной строки

| Опция                    | Параметр                                         | По умолчанию   |
|--------------------------|--------------------------------------------------|----------------|
| `--package`, `-p NAME`   | имя анализируемого пакета (обязательный)         | -              |
| `--repo`, `-r URL\|PATH` | URL репозитория или путь к файлу тестового репозитория | Maven Central |
| `--test-mode`, `-t`      | режим работы с тестовым репозиторием             | выключен       |
| `--ascii-tree`, `-a`     | режим вывода зависимостей в формате ASCII-дерева | выключен       |
| `--filter`, `-f SUBSTRING` | подстрока для фильтрации пакетов               | не задана      |
| `-h`, `--help`           | справка по опциям                                | -              |

Опции можно задавать в любом порядке, значение указывается через
пробел или `=` (`--package=A`), короткие флаги можно писать слитно
(`-ta`).

Формат значений:

* **`--package`** - координаты Maven `groupId:artifactId[:version]`,
  например `org.junit:junit:4.13.2`. Если версия не указана, на
  следующих этапах будет использоваться последняя. В тестовом режиме
  пакеты называются заглавными латинскими буквами: `A`, `B`, `ABC`.
* **`--repo`** - URL репозитория Maven со схемой `http` или `https`.
  Без опции используется Maven Central `https://repo1.maven.org/maven2`.
  В тестовом режиме опция обязательна и задаёт путь к существующему
  файлу описания графа.
* **`--test-mode`** - флаг без значения: пакеты и зависимости берутся
  из файла тестового репозитория, а не из сети.
* **`--ascii-tree`** - флаг без значения: зависимости будут выведены
  ASCII-деревом.
* **`--filter`** - пакеты, имя которых содержит эту подстроку, не
  учитываются при анализе. Подстрока не может быть пустой, не может
  содержать пробелы и не может входить в имя анализируемого пакета
  (без версии), иначе анализировать было бы нечего.

### Вывод параметров

При успешном запуске все параметры выводятся в формате ключ-значение
(незаданные отмечаются `<not set>`), код завершения 0:

```
package    = org.junit:junit:4.13.2
repo       = https://repo1.maven.org/maven2
test-mode  = false
ascii-tree = false
filter     = <not set>
```

### Обработка ошибок

При любой ошибке сообщение выводится в поток ошибок, параметры не
выводятся, код завершения 2.

Синтаксические ошибки обрабатывает `argparse` (перед сообщением
выводится строка `usage`):

| Ситуация                      | Сообщение                                                 |
|-------------------------------|-----------------------------------------------------------|
| не задан `--package`          | `the following arguments are required: --package/-p`      |
| опция без значения            | `argument --repo/-r: expected one argument`               |
| опция задана дважды           | `argument --filter: specified more than once`             |
| флаг со значением             | `argument --test-mode/-t: ignored explicit argument 'yes'` |
| неизвестная опция, лишний аргумент | `unrecognized arguments: --unknown`                  |

Ошибки в значениях (`depviz: error: <опция>: <сообщение>`):

| Опция         | Ситуация                                  | Сообщение                                                   |
|---------------|-------------------------------------------|-------------------------------------------------------------|
| `--package`   | пустое имя                                | `package name must not be empty`                            |
| `--package`   | не координаты Maven                       | `'junit' is not a Maven coordinate groupId:artifactId[:version]` |
| `--package`   | в тестовом режиме не заглавные буквы      | `'a': in test mode package name must consist of capital Latin letters` |
| `--repo`      | пустое значение                           | `value must not be empty`                                   |
| `--repo`      | схема не http/https                       | `'ftp://...' is not an HTTP(S) URL`                         |
| `--repo`      | файл без `--test-mode`                    | `'...' is not an HTTP(S) URL (use --test-mode for a test repository file)` |
| `--repo`      | URL без имени сервера                     | `'https:///maven2': URL has no host`                        |
| `--repo`      | пробел в URL                              | `'...': URL must not contain whitespace`                    |
| `--repo`      | тестовый режим без `--repo`               | `test mode requires a path to the test repository file`     |
| `--repo`      | URL в тестовом режиме                     | `'https://...': test mode requires a file path, not a URL`  |
| `--repo`      | файл не существует                        | `no/such/file.txt: No such file or directory`               |
| `--repo`      | каталог вместо файла                      | `examples/repos: Is a directory`                            |
| `--repo`      | нет прав на чтение                        | `...: Permission denied`                                    |
| `--filter`    | пустая подстрока                          | `substring must not be empty`                               |
| `--filter`    | пробелы в подстроке                       | `'ham crest': substring must not contain whitespace`        |
| `--filter`    | подстрока входит в имя пакета             | `'junit' excludes the analyzed package 'org.junit:junit' itself` |

Ошибки флагов `--test-mode` и `--ascii-tree` - значение и повтор
флага - перечислены в таблице синтаксических ошибок. Кроме того,
`--test-mode` меняет требования к `--package` и `--repo`, поэтому их
несогласованность с режимом тоже является ошибкой.

## Сборка и запуск

Сборка не требуется, нужен только Python 3.8+.

```sh
./run.sh --package org.junit:junit:4.13.2       # Linux / macOS
run.bat --package org.junit:junit:4.13.2        # Windows
make run ARGS="--package org.junit:junit"       # через make (без ARGS - справка)
```

Запуск модульных тестов:

```sh
python3 -m unittest discover -s tests -t . -v     # Linux / macOS
python -m unittest discover -s tests -t . -v      # Windows
make test                                         # через make
```

### Скрипты ОС для демонстрации

Каждый скрипт несколько раз запускает инструмент и печатает команду
запуска, весь вывод и код завершения. Для каждого скрипта есть версия
для Windows (`.bat`) и для Linux / macOS (`.sh`).

| Скрипт                        | Что проверяет                                   |
|-------------------------------|-------------------------------------------------|
| `scripts/test_valid_params`   | корректные параметры: все опции, короткие формы, `=`, любой порядок |
| `scripts/test_package_errors` | ошибки `--package`                              |
| `scripts/test_repo_errors`    | ошибки `--repo` в обоих режимах                 |
| `scripts/test_mode_errors`    | ошибки флагов `--test-mode` и `--ascii-tree`    |
| `scripts/test_filter_errors`  | ошибки `--filter`                               |
| `scripts/test_bad_usage`      | справка, запуск без опций, неизвестные опции    |

Запуск одного скрипта:

```sh
sh scripts/test_repo_errors.sh            # Linux / macOS
```

```bat
scripts\test_repo_errors.bat              :: Windows (cmd)
```

Все скрипты подряд:

```sh
for f in scripts/*.sh; do sh "$f"; done              # Linux / macOS
```

```bat
for %f in (scripts\*.bat) do call %f                 :: Windows (cmd)
```

### Тестовый репозиторий

`examples/repos/simple.txt` - пример файла тестового репозитория для
опции `--repo` в режиме `--test-mode`. На этапе 1 проверяется только,
что файл существует и доступен для чтения; содержимое (строки вида
`A: B C` - пакет и его прямые зависимости) будет читаться начиная
с этапа 3.

## Примеры использования

```
$ ./run.sh -p org.slf4j:slf4j-api:2.0.9 -r https://repo.maven.apache.org/maven2 -a
package    = org.slf4j:slf4j-api:2.0.9
repo       = https://repo.maven.apache.org/maven2
test-mode  = false
ascii-tree = true
filter     = <not set>
```

```
$ ./run.sh -t -a -f E -r examples/repos/simple.txt -p A
package    = A
repo       = examples/repos/simple.txt
test-mode  = true
ascii-tree = true
filter     = E
```

```
$ ./run.sh --package A --test-mode --repo https://repo1.maven.org/maven2
depviz: error: --repo: 'https://repo1.maven.org/maven2': test mode requires a file path, not a URL
$ echo $?
2
```

```
$ ./run.sh --package org.junit:junit --filter junit
depviz: error: --filter: 'junit' excludes the analyzed package 'org.junit:junit' itself
$ echo $?
2
```
