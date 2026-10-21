"""Разбор командной строки эмулятора на аргументы.

Парсер работает по правилам, близким к POSIX shell:

* аргументы разделяются пробельными символами;
* в одинарных кавычках всё берётся буквально;
* в двойных кавычках работает экранирование ``\\"`` и ``\\\\``;
* вне кавычек обратная косая черта экранирует следующий символ;
* кавычки могут склеиваться с обычным текстом: ``a"b c"d`` -> ``ab cd``.
"""

SINGLE_QUOTE = "'"
DOUBLE_QUOTE = '"'
ESCAPE = "\\"
DOUBLE_QUOTE_ESCAPABLE = (DOUBLE_QUOTE, ESCAPE)


class ParseError(Exception):
    """Ошибка разбора командной строки (например, незакрытая кавычка)."""


def tokenize(line):
    """Разбить строку на список аргументов с учётом кавычек.

    :param line: строка, введённая пользователем.
    :return: список аргументов (пустой список для пустой строки).
    :raises ParseError: при незакрытой кавычке или висящем ``\\``.
    """
    tokens = []
    current = []
    in_token = False
    pos = 0
    while pos < len(line):
        char = line[pos]
        if char.isspace():
            if in_token:
                tokens.append("".join(current))
                current = []
                in_token = False
            pos += 1
            continue
        in_token = True
        if char in (SINGLE_QUOTE, DOUBLE_QUOTE):
            pos = _read_quoted(line, pos, current)
        elif char == ESCAPE:
            pos = _read_escaped(line, pos, current)
        else:
            current.append(char)
            pos += 1
    if in_token:
        tokens.append("".join(current))
    return tokens


def _read_quoted(line, start, out):
    """Прочитать фрагмент в кавычках, начиная с позиции открывающей кавычки.

    :param line: исходная строка.
    :param start: индекс открывающей кавычки.
    :param out: список символов текущего аргумента (дополняется).
    :return: индекс символа, следующего за закрывающей кавычкой.
    :raises ParseError: если закрывающая кавычка не найдена.
    """
    quote = line[start]
    pos = start + 1
    while pos < len(line):
        char = line[pos]
        if char == quote:
            return pos + 1
        next_pos = pos + 1
        if (quote == DOUBLE_QUOTE and char == ESCAPE
                and next_pos < len(line)
                and line[next_pos] in DOUBLE_QUOTE_ESCAPABLE):
            char = line[next_pos]
            pos = next_pos
        out.append(char)
        pos += 1
    raise ParseError(
        "unexpected EOF while looking for matching `{}'".format(quote))


def _read_escaped(line, start, out):
    """Обработать обратную косую черту вне кавычек.

    :param line: исходная строка.
    :param start: индекс символа ``\\``.
    :param out: список символов текущего аргумента (дополняется).
    :return: индекс символа после экранированного.
    :raises ParseError: если ``\\`` стоит в конце строки.
    """
    next_pos = start + 1
    if next_pos >= len(line):
        raise ParseError("unexpected end of line after `\\'")
    out.append(line[next_pos])
    return next_pos + 1
