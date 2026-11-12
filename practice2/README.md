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

**Этап 3. Основные операции.** Строится граф зависимостей с учётом
транзитивности - алгоритмом DFS без рекурсии. Пакеты, имя которых
содержит заданную подстроку, не учитываются, циклические зависимости
находятся и выводятся. Вместо репозитория Maven можно указать файл
тестового репозитория, где пакеты называются заглавными латинскими
буквами.

**Этап 4. Дополнительные операции.** Режим вывода порядка загрузки
зависимостей пакета и сравнение результата с Maven. По заданию режим
нужен только на этапе 4, на этапе 5 он убран.

**Этап 5. Визуализация.** Граф выводится на языке диаграмм Graphviz и
в виде изображения, а по флагу `--ascii-tree` - в виде ASCII-дерева.
Результаты сравниваются со штатными средствами Maven.

Язык реализации: Python 3.8+ (только стандартная библиотека).

## Структура репозитория

```
src/depviz/         исходный код
  __main__.py       запуск через python -m depviz
  app.py            точка входа: опции, проверка, построение графа
  config.py         опции командной строки
  validation.py     проверка значений параметров
  maven.py          координаты, зависимости, адреса файлов Maven
  pom.py            разбор POM и maven-metadata.xml
  repository.py     загрузка файлов по HTTP(S)
  resolver.py       получение прямых зависимостей пакета
  graph.py          граф зависимостей: DFS без рекурсии, циклы, фильтр
  sources.py        источники данных: репозиторий Maven, тестовый
  testrepo.py       чтение файла тестового репозитория
  report.py         текст графа: Graphviz (DOT) и ASCII-дерево
  image.py          изображение графа: Graphviz dot и просмотр
tests/              модульные тесты (unittest, без сети)
examples/repos/     файлы тестовых репозиториев (broken/ - ошибочные)
examples/maven-repo/ локальный репозиторий Maven для демонстрации
examples/compare/   pom.xml для сравнения с Maven
scripts/            скрипты ОС для демонстрации (.sh и .bat)
run.sh, run.bat     скрипты запуска
Makefile            цели run и test
```

## Функции и настройки

### Параметры командной строки

| Опция | Параметр | По умолчанию |
|---|---|---|
| `--package`, `-p NAME` | имя анализируемого пакета (обязательный) | - |
| `--repo`, `-r URL\|PATH` | URL репозитория или путь к файлу тестового репозитория | Maven Central |
| `--test-mode`, `-t` | режим работы с тестовым репозиторием | выключен |
| `--ascii-tree`, `-a` | режим вывода зависимостей в формате ASCII-дерева | выключен |
| `--filter`, `-f SUBSTRING` | подстрока для фильтрации пакетов | не задана |
| `-h`, `--help` | справка по опциям | - |

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
  из файла тестового репозитория (`--repo`), а не из сети.
* **`--ascii-tree`** - флаг без значения: вместо описания на языке
  Graphviz зависимости выводятся ASCII-деревом.
* **`--filter`** - пакеты, имя которых содержит эту подстроку, не
  учитываются при анализе: они не попадают в граф, и их зависимости не
  обходятся. Для Maven с подстрокой сравнивается `groupId:artifactId`,
  в тестовом режиме - имя пакета. Подстрока не может быть пустой, не
  может содержать пробелы и не может входить в имя анализируемого пакета
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

### Построение графа зависимостей

Граф строится обходом в глубину (DFS) **без рекурсии**: вместо стека
вызовов используется явный стек, каждый элемент которого - пара
(пакет, итератор по его зависимостям). Поэтому глубина графа не
ограничена пределом рекурсии Python (это проверяется тестом на
цепочке из 2000 пакетов).

Каждый пакет при обходе находится в одном из состояний: ещё не
встречался, «в обработке» (лежит в стеке) или «обработан». Зависимости
пакета запрашиваются у источника один раз, при первом входе в пакет:

* зависимость, которая ещё не встречалась, кладётся в стек;
* зависимость «в обработке» означает **цикл**: путь от неё до вершины
  стека и обратно запоминается, а повторный обход не выполняется,
  поэтому циклы не приводят к зацикливанию;
* зависимость, которая уже обработана, - общий пакет нескольких путей
  («ромб»), ребро добавляется, обход не повторяется;
* зависимость, имя которой содержит подстроку `--filter`, в граф не
  добавляется и не обходится.

Если не удалось получить сам анализируемый пакет, выводится ошибка
(код 1). Если не удалось получить зависимости другого пакета (нет POM,
диапазон версий `[1.0,2.0)`, нет пакета в тестовом репозитории), пакет
помечается как неразрешённый, а обход продолжается.

Для репозитория Maven учитываются те же зависимости, что и в
`mvn dependency:tree`: у анализируемого пакета - все прямые
зависимости, у остальных пакетов - только транзитивные, то есть
`compile` и `runtime` без `optional`. Узел графа - точные координаты
`groupId:artifactId:version`.

### Визуализация

После построения графа инструмент:

1. Формирует описание графа на языке диаграмм **Graphviz** (DOT):
   узел - пакет, ребро - зависимость. Анализируемый пакет выделяется
   жирной рамкой, неразрешённые пакеты - пунктирной.
2. Выводит на экран **изображение графа**: описание передаётся
   программе `dot` из пакета [Graphviz](https://graphviz.org), она
   создаёт временный файл PNG, который открывается программой
   просмотра изображений, назначенной в системе (`os.startfile` в
   Windows, `open` в macOS, `xdg-open` в Linux).
3. Печатает текст: без флага `--ascii-tree` - описание на языке
   Graphviz, с флагом - **ASCII-дерево** зависимостей.

ASCII-дерево оформлено как вывод `mvn dependency:tree`. Поддерево
каждого пакета выводится один раз, повторное появление пакета
отмечается `(*)`, зависимость, замыкающая цикл, - `(cycle)`,
неразрешённый пакет - `(not resolved)`.

Примеры для трёх пакетов (скрипт `scripts/test_visualize` выводит
эти же тексты и открывает изображения графов):

**`A` из `examples/repos/simple.txt`** - граф без циклов с общей
зависимостью D:

```
$ ./run.sh -t -r examples/repos/simple.txt -p A
digraph dependencies {
    rankdir=LR;
    node [shape=box];
    "A" [style=bold];
    "B";
    "D";
    "C";
    "E";
    "A" -> "B";
    "A" -> "C";
    "B" -> "D";
    "C" -> "D";
    "C" -> "E";
}
$ ./run.sh -t -r examples/repos/simple.txt -p A --ascii-tree
A
+- B
|  \- D
\- C
   +- D (*)
   \- E
```

**`A` из `examples/repos/cycles.txt`** - два цикла:

```
$ ./run.sh -t -r examples/repos/cycles.txt -p A --ascii-tree
A
\- B
   +- C
   |  \- A (cycle)
   \- D
      \- E
         +- D (cycle)
         \- F
```

**`APP` из `examples/repos/names.txt`** - общая зависимость CORE и
цикл APP -> TEST -> APP:

```
$ ./run.sh -t -r examples/repos/names.txt -p APP --ascii-tree
APP
+- WEB
|  +- CORE
|  \- JSON
|     \- CORE (*)
+- LOG
|  \- CORE (*)
\- TEST
   +- APP (cycle)
   \- CORE (*)
```

### Сравнение с Maven

Штатные средства визуализации Maven - команда `mvn dependency:tree`
(дерево в тексте) и она же с `-DoutputType=dot` (описание на языке
Graphviz). Для сравнения в `examples/compare/pom.xml` описан проект
с одной зависимостью `junit:junit:4.13.2`:

```sh
cd examples/compare
mvn dependency:tree
mvn dependency:tree -DoutputType=dot -DoutputFile=junit.dot
```

Результат Maven:

```
compare:compare:jar:1.0
\- junit:junit:jar:4.13.2:compile
   \- org.hamcrest:hamcrest-core:jar:1.3:compile

digraph "compare:compare:jar:1.0" {
    "compare:compare:jar:1.0" -> "junit:junit:jar:4.13.2:compile" ;
    "junit:junit:jar:4.13.2:compile" -> "org.hamcrest:hamcrest-core:jar:1.3:compile" ;
}
```

Результат инструмента:

```
$ ./run.sh --package junit:junit:4.13.2 --ascii-tree
junit:junit:4.13.2
+- org.hamcrest:hamcrest-core:1.3
\- org.hamcrest:hamcrest-library:1.3
   \- org.hamcrest:hamcrest-core:1.3 (*)
```

Расхождения и их причины:

1. **Корень.** Maven строит дерево проекта, в котором junit - одна из
   зависимостей. Инструмент строит граф самого пакета junit.
2. **Лишний `hamcrest-library`.** У junit это зависимость со
   `scope=test`. Инструмент учитывает все прямые зависимости
   анализируемого пакета, а Maven не передаёт `test`-зависимости
   зависимостей проекту.
3. **Повторы.** Maven выводит каждый пакет один раз и не показывает
   повторные пути (только с `-Dverbose`). Инструмент показывает
   повторы с отметкой `(*)`, а в Graphviz - как несколько рёбер в один
   узел, поэтому изображение - граф, а не дерево.
4. **Подписи.** Maven добавляет к координатам тип (`jar`) и область
   видимости (`compile`), инструмент выводит `groupId:artifactId:version`.
5. **Версии.** Maven оставляет одну версию каждого пакета (ближайшую к
   корню, «nearest wins») и учитывает `exclusions`, а инструмент
   считает разные версии разными пакетами. На больших графах из-за
   этого число пакетов может отличаться.

### Тестовый репозиторий

Файл описания графа - текст в UTF-8 (с BOM или без), по одному
пакету на строку: имя пакета, двоеточие и зависимости через пробел.
Пакеты называются заглавными латинскими буквами (`A`, `B`, `APP`).
Пустые строки и текст после `#` пропускаются.

```
# A зависит от B и C
A: B C
B: D
C: D E
D:
E:
```

Пакет, который указан только как зависимость, считается отсутствующим
в репозитории (как пакет без POM в Maven) и помечается как
неразрешённый.

### Обработка ошибок

При любой ошибке сообщение выводится в поток ошибок в формате
`depviz: error: <сообщение>`. Ошибки в опциях - код завершения 2,
ошибки получения данных об анализируемом пакете - код 1.

Синтаксические ошибки обрабатывает `argparse` (перед сообщением
выводится строка `usage`):

| Ситуация | Сообщение |
|---|---|
| не задан `--package` | `the following arguments are required: --package/-p` |
| опция без значения | `argument --repo/-r: expected one argument` |
| опция задана дважды | `argument --filter: specified more than once` |
| флаг со значением | `argument --test-mode/-t: ignored explicit argument 'yes'` |
| неизвестная опция, лишний аргумент | `unrecognized arguments: --unknown` |

Ошибки в значениях (`depviz: error: <опция>: <сообщение>`):

| Опция | Ситуация | Сообщение |
|---|---|---|
| `--package` | пустое имя | `package name must not be empty` |
| `--package` | не координаты Maven | `'junit' is not a Maven coordinate groupId:artifactId[:version]` |
| `--package` | не заглавные буквы (тест) | `'a': in test mode package name must consist of capital Latin letters` |
| `--repo` | пустое значение | `value must not be empty` |
| `--repo` | схема не http/https | `'ftp://...' is not an HTTP(S) URL` |
| `--repo` | файл без `--test-mode` | `'...' is not an HTTP(S) URL (use --test-mode for a test repository file)` |
| `--repo` | URL без имени сервера | `'https:///maven2': URL has no host` |
| `--repo` | пробел в URL | `'...': URL must not contain whitespace` |
| `--repo` | тестовый режим без `--repo` | `test mode requires a path to the test repository file` |
| `--repo` | URL в тестовом режиме | `'https://...': test mode requires a file path, not a URL` |
| `--repo` | файл не существует | `no/such/file.txt: No such file or directory` |
| `--repo` | каталог вместо файла | `examples/repos: Is a directory` |
| `--repo` | нет прав на чтение | `...: Permission denied` |
| `--filter` | пустая подстрока | `substring must not be empty` |
| `--filter` | пробелы в подстроке | `'ham crest': substring must not contain whitespace` |
| `--filter` | подстрока входит в имя пакета | `'junit' excludes the analyzed package 'org.junit:junit' itself` |

Ошибки флагов `--test-mode` и `--ascii-tree` - значение и повтор
флага - перечислены в таблице синтаксических ошибок. Кроме того,
`--test-mode` меняет требования к `--package` и `--repo`, поэтому их
несогласованность с режимом тоже является ошибкой.

Ошибки получения зависимостей (код 1):

| Ситуация | Сообщение |
|---|---|
| нет POM пакета (HTTP 404) | `package g:a:1.0 not found in repository (<url>: HTTP 404 Not Found)` |
| нет maven-metadata.xml | `package g:a not found in repository (...)` |
| в метаданных нет версий | `<url>: no versions found` |
| некорректный XML | `<url>: invalid XML: mismatched tag: line 7, column 2` |
| файл не является POM | `<url>: root element is <html>, expected <project>` |
| нет родительского POM | `cannot load parent of g:a:1.0: package ... not found ...` |
| циклическая цепочка родителей | `cyclic parent reference: g:a:1.0 -> g:b:1.0 -> g:a:1.0` |
| сервер недоступен | `<url>: cannot connect: [Errno 111] Connection refused` |
| неизвестный сервер | `<url>: cannot connect: [Errno -2] Name or service not known` |
| другой ответ HTTP | `<url>: HTTP 500 Internal Server Error` |

Ошибки тестового репозитория (код 1):

| Ситуация | Сообщение |
|---|---|
| строка без двоеточия | `f.txt:2: expected 'PACKAGE: DEPENDENCIES', got 'B C'` |
| имя не из заглавных букв | `f.txt:2: invalid package name 'c': expected capital Latin letters` |
| пакет описан дважды | `f.txt:3: duplicate package 'A'` |
| повтор в списке зависимостей | `f.txt:1: duplicate dependency 'B' of A` |
| файл не в UTF-8 | `'f.txt' is not a UTF-8 text file` |
| анализируемого пакета нет | `package Q not found in test repository` |

Ошибки показа изображения (код 1, текст графа к этому моменту уже
выведен):

| Ситуация | Сообщение |
|---|---|
| Graphviz не установлен | `Graphviz is not installed: 'dot' not found in PATH` |
| ошибка программы dot | `dot failed: <сообщение dot>` |
| не открылась программа просмотра | `cannot open image <файл>: <причина>` |

## Сборка и запуск

Сборка не требуется. Нужны Python 3.8+ и Graphviz для вывода
изображения графа (https://graphviz.org/download/; в Windows при
установке отметить добавление в `PATH`, в Linux - пакет `graphviz`).

```sh
./run.sh --package junit:junit:4.13.2           # Linux / macOS
run.bat --package junit:junit:4.13.2            # Windows
make run ARGS="--package junit:junit"           # через make (без ARGS - справка)
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

| Скрипт | Что проверяет |
|---|---|
| `scripts/test_valid_params` | корректные параметры: все опции, короткие формы, `=`, любой порядок |
| `scripts/test_package_errors` | ошибки `--package` |
| `scripts/test_repo_errors` | ошибки `--repo` в обоих режимах |
| `scripts/test_mode_errors` | ошибки флагов `--test-mode` и `--ascii-tree` |
| `scripts/test_filter_errors` | ошибки `--filter` |
| `scripts/test_bad_usage` | справка, запуск без опций, неизвестные опции |

Получение зависимостей из репозитория Maven (этап 2; начиная с
этапа 3 выводится граф):

| Скрипт | Что проверяет |
|---|---|
| `scripts/test_deps_local` | `examples/maven-repo` без интернета: версия, родитель, свойства, BOM, scope |
| `scripts/test_deps_errors` | нет пакета или версий, неверный XML, не POM, нет родителя, цикл, нет сервера |
| `scripts/test_deps_central` | реальные пакеты из Maven Central (нужен интернет) |

Граф зависимостей (этап 3):

| Скрипт | Что проверяет |
|---|---|
| `scripts/test_graph_test_repo` | тестовые репозитории: ромб, циклы, глубина 26, нет пакетов, нет корня |
| `scripts/test_graph_filter` | фильтрация: удаление поддерева, разрыв цикла, несколько пакетов |
| `scripts/test_graph_broken` | некорректные файлы тестового репозитория |
| `scripts/test_graph_maven` | граф из `examples/maven-repo`: транзитивность, scope, цикл, фильтр |

Визуализация (этап 5):

| Скрипт | Что проверяет |
|---|---|
| `scripts/test_visualize` | три пакета: текст на языке Graphviz и изображение, затем ASCII-деревья |

Начиная с этапа 5 каждый успешный запуск открывает изображение графа,
поэтому скрипты открывают по одному окну просмотра на запуск.

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

| Пакет | Что демонстрирует |
|---|---|
| `junit:junit` (4.13.2) | свойство в версии, `scope=test`, версия из метаданных |
| `org.hamcrest:hamcrest-library:1.3` | родительский POM, `${project.version}` |
| `org.example:demo-app` (1.0.0, 1.1.0) | версия из метаданных, родитель, свойства, управление версиями, BOM, scope |
| `org.example:no-deps:1.0` | пакет без зависимостей, POM без пространства имён |
| `org.example:broken-xml:1.0` | некорректный XML |
| `org.example:not-a-pom:1.0` | файл не является POM |
| `org.example:orphan:1.0` | отсутствующий родительский POM |
| `org.example:cycle-a:1.0` | циклическая цепочка родителей |
| `org.example:no-versions` | метаданные без версий |
| `org.example:demo-core:1.1.0` | `optional`, `test` и `provided` не транзитивны, `runtime` транзитивна |
| `org.example:cycle-x:1.0` | цикл зависимостей cycle-x -> cycle-y -> cycle-z -> cycle-x |
| `org.example:missing-dep:1.0` | транзитивные зависимости без POM и с диапазоном версий |

Для полноты графа `demo-app` в репозитории есть упрощённые POM
транзитивных зависимостей (`slf4j-api`, `guava` и её зависимости,
`jackson-*`, `commons-lang3`, `jakarta.servlet-api`). Они содержат
только прямые зависимости этих пакетов, остальные элементы убраны.

Тестовые репозитории в `examples/repos/`:

| Файл | Граф |
|---|---|
| `simple.txt` | без циклов, общая зависимость D (ромб) |
| `cycle.txt` | цикл A -> B -> C -> A |
| `self_cycle.txt` | пакет зависит сам от себя |
| `cycles.txt` | два цикла, второй достижим из первого |
| `deep.txt` | цепочка из 26 уровней A -> ... -> Z |
| `names.txt` | имена из нескольких букв, цикл APP -> TEST -> APP |
| `missing.txt` | зависимости, не описанные в репозитории |
| `broken/*.txt` | ошибки формата: имя, двоеточие, повторы, пустой файл, не UTF-8 |

## Примеры использования

Граф на языке Graphviz и изображение (открывается в программе
просмотра):

```
$ ./run.sh --test-mode --repo examples/repos/cycle.txt --package A
digraph dependencies {
    rankdir=LR;
    node [shape=box];
    "A" [style=bold];
    "B";
    "C";
    "D";
    "A" -> "B";
    "B" -> "C";
    "C" -> "A";
    "C" -> "D";
}
```

ASCII-дерево с фильтром:

```
$ ./run.sh -t -r examples/repos/names.txt -p APP -f T -a
APP
+- WEB
|  +- CORE
|  \- JSON
|     \- CORE (*)
\- LOG
   \- CORE (*)
```

Пакет из Maven Central:

```
$ ./run.sh --package junit:junit:4.13.2 --ascii-tree
junit:junit:4.13.2
+- org.hamcrest:hamcrest-core:1.3
\- org.hamcrest:hamcrest-library:1.3
   \- org.hamcrest:hamcrest-core:1.3 (*)
```

Неразрешённые пакеты не прерывают построение графа:

```
$ ./run.sh --package org.example:missing-dep:1.0 --repo http://127.0.0.1:8765 -a
org.example:missing-dep:1.0
+- org.example:ghost:1.0 (not resolved)
+- org.example:no-deps:1.0
\- org.example:ranged:[1.0,2.0) (not resolved)
```

Ошибка в файле тестового репозитория:

```
$ ./run.sh -t -r examples/repos/broken/no_colon.txt -p A
depviz: error: examples/repos/broken/no_colon.txt:2: expected 'PACKAGE: DEPENDENCIES', got 'B C'
$ echo $?
1
```
