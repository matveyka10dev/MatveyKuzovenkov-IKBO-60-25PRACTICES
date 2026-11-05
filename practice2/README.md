# Визуализатор графа зависимостей (вариант 17)

Инструмент командной строки (CLI) для визуализации графа зависимостей
пакетов Java (Maven). Готовые менеджеры пакетов и библиотеки для
получения зависимостей не используются.

**Этап 1. Минимальный прототип с конфигурацией.** Приложение принимает
пять параметров в виде опций командной строки и проверяет каждый из
них. Для любого параметра выводится понятное сообщение об ошибке.

**Этап 2. Сбор данных.** По URL репозитория Maven скачиваются файлы
POM заданного пакета (и его родителей), из них извлекаются и выводятся
на экран все прямые зависимости пакета. Для загрузки используется
только `urllib`, для разбора XML - `xml.etree.ElementTree` из
стандартной библиотеки Python.

Язык реализации: Python 3.8+ (только стандартная библиотека).

## Структура репозитория

```
src/depviz/         исходный код
  __main__.py       запуск через python -m depviz
  app.py            точка входа: опции, проверка, вывод зависимостей
  config.py         опции командной строки
  validation.py     проверка значений параметров
  maven.py          координаты, зависимости, адреса файлов Maven
  pom.py            разбор POM и maven-metadata.xml
  repository.py     загрузка файлов по HTTP(S)
  resolver.py       получение прямых зависимостей пакета
tests/              модульные тесты (unittest, без сети)
examples/repos/     пример файла тестового репозитория
examples/maven-repo/ локальный репозиторий Maven для демонстрации
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
  например `junit:junit:4.13.2`. Если версия не указана, берётся
  последняя выпущенная версия из `maven-metadata.xml`. В тестовом режиме
  пакеты называются заглавными латинскими буквами: `A`, `B`, `ABC`.
* **`--repo`** - URL репозитория Maven со схемой `http` или `https`.
  Без опции используется Maven Central `https://repo1.maven.org/maven2`.
  В тестовом режиме опция обязательна и задаёт путь к существующему
  файлу описания графа.
* **`--test-mode`** - флаг без значения: пакеты и зависимости берутся
  из файла тестового репозитория, а не из сети. Чтение файла будет
  реализовано на этапе 3, пока выводится сообщение
  `test mode: dependencies from a test repository file are not
  supported yet`.
* **`--ascii-tree`** - флаг без значения: зависимости будут выведены
  ASCII-деревом (этап 5, пока не влияет на вывод).
* **`--filter`** - пакеты, имя которых содержит эту подстроку, не
  учитываются при анализе (этап 3, пока не влияет на вывод). Подстрока не может быть пустой, не может
  содержать пробелы и не может входить в имя анализируемого пакета
  (без версии), иначе анализировать было бы нечего.

### Получение прямых зависимостей

Файлы в репозитории Maven располагаются по схеме:

```
<repo>/<groupId: . -> />/<artifactId>/maven-metadata.xml
<repo>/<groupId: . -> />/<artifactId>/<version>/<artifactId>-<version>.pom
```

Например, POM пакета `junit:junit:4.13.2` в Maven Central:
`https://repo1.maven.org/maven2/junit/junit/4.13.2/junit-4.13.2.pom`.

Порядок работы (повторяет построение «эффективного POM» в Maven):

1. Если версия не задана, она берётся из `maven-metadata.xml`:
   элемент `release`, иначе `latest`, иначе последний из `versions`.
2. Скачивается POM пакета, затем цепочка родительских POM (`parent`).
3. По цепочке сливаются `properties`, `dependencyManagement` и
   `dependencies`: значения потомка важнее значений родителя, поэтому
   зависимости, объявленные в родителе, тоже являются прямыми.
4. Подставляются свойства `${...}`: из `properties` и встроенные
   `project.groupId`, `project.artifactId`, `project.version`,
   `project.parent.*`. Неизвестные свойства остаются как есть.
5. Записи `dependencyManagement` со `scope=import` и `type=pom`
   (BOM) заменяются управляемыми зависимостями этого BOM. Явно
   объявленные записи важнее импортированных.
6. Зависимости без версии или `scope` получают их из
   `dependencyManagement`; `scope` по умолчанию - `compile`.

Зависимости плагинов сборки (`build/plugins`) и профилей (`profiles`)
не являются зависимостями пакета и не учитываются. Скачанные файлы
кэшируются в памяти, повторно не загружаются.

Выводятся все прямые зависимости с областью видимости (`compile`,
`test`, `provided`, `runtime`, `system`) и отметкой `optional`.
Код завершения 0:

```
Direct dependencies of junit:junit:4.13.2 (2):
  org.hamcrest:hamcrest-core:1.3 [compile]
  org.hamcrest:hamcrest-library:1.3 [test]
```

Если зависимостей нет, выводится `(no dependencies)`. Если версию не
удалось определить, вместо неё выводится `<unknown version>`.

### Обработка ошибок

При любой ошибке сообщение выводится в поток ошибок в формате
`depviz: error: <сообщение>`. Ошибки в опциях - код завершения 2,
ошибки получения зависимостей - код 1.

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

Ошибки получения зависимостей (код 1):

| Ситуация                         | Сообщение                                                 |
|----------------------------------|-----------------------------------------------------------|
| нет POM пакета (HTTP 404)        | `package g:a:1.0 not found in repository (<url>: HTTP 404 Not Found)` |
| нет maven-metadata.xml           | `package g:a not found in repository (...)`               |
| в метаданных нет версий          | `<url>: no versions found`                                |
| некорректный XML                 | `<url>: invalid XML: mismatched tag: line 7, column 2`    |
| файл не является POM             | `<url>: root element is <html>, expected <project>`       |
| нет родительского POM            | `cannot load parent of g:a:1.0: package ... not found ...` |
| циклическая цепочка родителей    | `cyclic parent reference: g:a:1.0 -> g:b:1.0 -> g:a:1.0`  |
| сервер недоступен                | `<url>: cannot connect: [Errno 111] Connection refused`   |
| неизвестный сервер               | `<url>: cannot connect: [Errno -2] Name or service not known` |
| другой ответ HTTP                | `<url>: HTTP 500 Internal Server Error`                   |

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

Получение прямых зависимостей (этап 2):

| Скрипт                        | Что проверяет                                   |
|-------------------------------|-------------------------------------------------|
| `scripts/test_deps_local`     | пакеты из `examples/maven-repo` (без интернета): версия из метаданных, родитель, свойства, BOM, scope, optional |
| `scripts/test_deps_errors`    | ошибки: нет пакета, нет версий, неверный XML, не POM, нет родителя, цикл родителей, недоступный сервер |
| `scripts/test_deps_central`   | реальные пакеты из Maven Central (нужен интернет) |

Скрипты `test_deps_local` и `test_deps_errors` на время работы
запускают встроенный HTTP-сервер Python
(`python -m http.server 8765 --directory examples/maven-repo`), так
что инструмент работает с настоящим URL `http://127.0.0.1:8765`.
В Windows сервер открывается в отдельном свёрнутом окне
`depviz-repo`, которое закрывается в конце скрипта. Сервер можно
запустить и вручную, а инструмент - в другом окне терминала:

```sh
python3 -m http.server 8765 --directory examples/maven-repo
./run.sh --package org.example:demo-app --repo http://127.0.0.1:8765
```

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

### Примеры репозиториев

`examples/maven-repo/` - локальный репозиторий Maven со стандартной
раскладкой каталогов. POM-файлы `junit` и `hamcrest` - упрощённые
копии настоящих (оставлены только элементы, влияющие на зависимости),
пакеты `org.example:*` придуманы для демонстрации:

| Пакет                                | Что демонстрирует                                  |
|--------------------------------------|----------------------------------------------------|
| `junit:junit` (4.13.2)               | свойство в версии, `scope=test`, версия из метаданных |
| `org.hamcrest:hamcrest-library:1.3`  | родительский POM, `${project.version}`             |
| `org.example:demo-app` (1.0.0, 1.1.0) | версия из метаданных, родитель `demo-parent`, переопределение свойства, управление версиями, импорт BOM `demo-bom`, `provided`, `optional`, унаследованная зависимость, игнорирование зависимостей плагина |
| `org.example:no-deps:1.0`            | пакет без зависимостей, POM без пространства имён  |
| `org.example:broken-xml:1.0`         | некорректный XML                                   |
| `org.example:not-a-pom:1.0`          | файл не является POM                               |
| `org.example:orphan:1.0`             | отсутствующий родительский POM                     |
| `org.example:cycle-a:1.0`            | циклическая цепочка родителей                      |
| `org.example:no-versions`            | метаданные без версий                              |

`examples/repos/simple.txt` - пример файла тестового репозитория для
режима `--test-mode`. Сейчас проверяется только, что файл существует и
доступен для чтения; содержимое (строки вида `A: B C` - пакет и его
прямые зависимости) будет читаться начиная с этапа 3.

## Примеры использования

Пакет из Maven Central (по умолчанию):

```
$ ./run.sh --package junit:junit:4.13.2
Direct dependencies of junit:junit:4.13.2 (2):
  org.hamcrest:hamcrest-core:1.3 [compile]
  org.hamcrest:hamcrest-library:1.3 [test]
```

Локальный репозиторий, версия из метаданных, родитель и BOM:

```
$ ./run.sh --package org.example:demo-app --repo http://127.0.0.1:8765
Direct dependencies of org.example:demo-app:1.1.0 (7):
  org.slf4j:slf4j-api:2.0.9 [compile]
  com.google.guava:guava:33.0.0-jre [compile]
  com.fasterxml.jackson.core:jackson-databind:2.16.1 [compile]
  org.example:demo-core:1.1.0 [compile]
  jakarta.servlet:jakarta.servlet-api:6.0.0 [provided]
  org.apache.commons:commons-lang3:3.14.0 [compile, optional]
  junit:junit:4.13.2 [test]
```

Здесь `slf4j-api` получает версию из свойства, переопределённого в
`demo-app`, `guava` - из `dependencyManagement` родителя (версия
`31.0-jre` из BOM проигрывает явной записи), `jackson-databind` - из
импортированного BOM, `demo-core` - из `${project.version}`, а
`junit` унаследован от родителя вместе с `scope=test`.

Ошибки:

```
$ ./run.sh --package org.example:cycle-a:1.0 --repo http://127.0.0.1:8765
depviz: error: cyclic parent reference: org.example:cycle-a:1.0 -> org.example:cycle-b:1.0 -> org.example:cycle-a:1.0
$ echo $?
1
```

```
$ ./run.sh --package A --test-mode --repo https://repo1.maven.org/maven2
depviz: error: --repo: 'https://repo1.maven.org/maven2': test mode requires a file path, not a URL
$ echo $?
2
```
