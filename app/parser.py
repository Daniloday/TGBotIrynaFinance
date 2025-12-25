import re
from dataclasses import dataclass
from typing import Iterable


class ParseError(Exception):
    pass


_amount_re = re.compile(r"""
    ^\s*-\s*                          # starts with '-' (expense)
    (?P<num>\d+(?:[.,]\d{1,2})?)      # 12 | 12.3 | 12.34 | 12,34
    (?:\s+|$)                         # space or end
""", re.VERBOSE)


_mention_re = re.compile(r"^@[A-Za-z0-9_]{4,32}$")  # tg username rules (rough)


def _is_mention(token: str) -> bool:
    return bool(_mention_re.match(token))


def parse_message(
    text: str,
    author_username: str,
    session_participants: Iterable[str],
) -> dict:
    """
    Форматы:
      -80 pizza
      -80,5 таксі
      - 600 бар @anna @roma
      -420 @danya pizza @anna @roma   (первый @... после суммы = payer)
    Правила:
      - Минус обязателен (это триггер "трата")
      - Сумма хранится как ПОЛОЖИТЕЛЬНАЯ (80.0)
      - Упоминания участников только с '@'
    """
    if not text or not text.lstrip().startswith("-"):
        raise ParseError("Формат: -450 піца")

    m = _amount_re.match(text)
    if not m:
        raise ParseError("Не бачу суму. Формат: `-450 піца` або `-120,67 таксі`")

    raw_num = m.group("num").replace(",", ".")
    try:
        amount = float(raw_num)
    except ValueError:
        raise ParseError("Некоректна сума. Приклад: `-120,67 таксі`")

    if amount <= 0:
        # 0 або мінус в самій цифрі нам не треба
        raise ParseError("Сума має бути більшою за 0. Приклад: `-450 піца`")

    rest = text[m.end():].strip()
    if not rest:
        raise ParseError("Додай назву витрати. Приклад: `-450 піца`")

    tokens = rest.split()

    # payer: первый токен-упоминание после суммы
    payer = author_username
    i = 0
    if tokens and _is_mention(tokens[0]):
        payer = tokens[0]
        i = 1

    # дальше: собираем участников из упоминаний, а остальное = title
    mentions: list[str] = []
    title_parts: list[str] = []

    for t in tokens[i:]:
        if _is_mention(t):
            mentions.append(t)
        else:
            title_parts.append(t)

    title = " ".join(title_parts).strip()
    if not title:
        # если человек написал только "-80 @payer @anna" без названия
        raise ParseError("Додай назву витрати після суми. Приклад: `-80 піца @anna`")

    session_participants = list(session_participants)

    # participants:
    # - если указали @mentions (кроме payer) -> берем их
    # - если не указали никого -> все участники сессии
    if mentions:
        participants = mentions
    else:
        participants = session_participants

    # если вообще пусто (новый чат) -> хотя бы payer
    if not participants:
        participants = [payer]

    # payer должен быть в participants (иначе баланс будет странный)
    if payer not in participants:
        participants = [payer] + participants

    # дедуп + стабильный порядок
    seen = set()
    participants_unique = []
    for p in participants:
        if p not in seen:
            seen.add(p)
            participants_unique.append(p)

    return {
        "amount": amount,
        "title": title,
        "payer": payer,
        "participants": participants_unique,
    }
