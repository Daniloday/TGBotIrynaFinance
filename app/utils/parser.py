import re
from typing import Iterable
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from app.domain.errors import ParseError, ParseErrorCode

_amount_re = re.compile(r"""
    ^\s*-\s*                          # starts with '-' (expense)
    (?P<num>\d+(?:[.,]\d{1,2})?)      # 12 | 12.3 | 12.34 | 12,34
    (?:\s+|$)                         # space or end
""", re.VERBOSE)


def _is_mention(token: str) -> bool:
    return token.startswith("@") and len(token) > 1 and " " not in token


def _to_cents(raw_num: str) -> int:
    raw_num = raw_num.replace(",", ".")
    try:
        dec = Decimal(raw_num)
    except InvalidOperation:
        raise ParseError(ParseErrorCode.INVALID_AMOUNT)

    if dec <= 0:
        raise ParseError(ParseErrorCode.INVALID_AMOUNT)

    return int((dec * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


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
        raise ParseError(ParseErrorCode.INVALID_FORMAT)

    m = _amount_re.match(text)
    if not m:
        raise ParseError(ParseErrorCode.INVALID_AMOUNT)

    raw_num = m.group("num")
    amount_cents = _to_cents(raw_num)

    rest = text[m.end():].strip()
    if not rest:
        raise ParseError(ParseErrorCode.INVALID_AMOUNT)

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
        raise ParseError(ParseErrorCode.NO_TITLE)

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
            raise ParseError(ParseErrorCode.UNKNOWN_PEOPLE)

    return {
        "amount_cents": amount_cents,
        "title": title,
        "payer": payer,
        "participants": participants_unique,
    }
