import re
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
    Rules:
      - Минус обязателен (это триггер "трата")
      - Сумма хранится как ПОЛОЖИТЕЛЬНАЯ (80.0)
      - Упоминания участников только с '@'
    """
    if not text or not text.lstrip().startswith("-"):
        raise ParseError("Invalid format")

    m = _amount_re.match(text)
    if not m:
        raise ParseError("Invalid format")

    raw_num = m.group("num").replace(",", ".")
    try:
        amount = float(raw_num)
    except ValueError:
        raise ParseError("Invalid format")

    if amount <= 0:
        raise ParseError("Invalid format")

    rest = text[m.end():].strip()
    if not rest:
        raise ParseError("Invalid format")

    tokens = rest.split()

    payer = author_username
    i = 0
    if tokens and _is_mention(tokens[0]):
        payer = tokens[0]
        i = 1

    mentions: list[str] = []
    title_parts: list[str] = []

    for t in tokens[i:]:
        if _is_mention(t):
            mentions.append(t)
        else:
            title_parts.append(t)

    title = " ".join(title_parts).strip()
    if not title:
        raise ParseError("Invalid format")

    session_participants = list(session_participants)

    if mentions:
        participants = mentions
    else:
        participants = session_participants

    if not participants:
        participants = [payer]

    if payer not in participants:
        participants = [payer] + participants

    seen = set()
    participants_unique = []
    for p in participants:
        if p not in seen:
            seen.add(p)
            participants_unique.append(p)

    for u in participants_unique:
        if u not in session_participants:
            raise ParseError("Not all people included in session")

    return {
        "amount": amount,
        "title": title,
        "payer": payer,
        "participants": participants_unique,
    }
