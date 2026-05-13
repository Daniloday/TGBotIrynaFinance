import re
from typing import Iterable
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from app.domain.errors import ParseError, ParseErrorCode

_amount_re = re.compile(r"""
    ^\s*-\s*                          # starts with '-' (expense)
    (?P<num>\d+(?:[.,]\d{1,2})?)      # 12 | 12.3 | 12.34 | 12,34
    (?:\s+|$)                         # space or end
""", re.VERBOSE)
_amount_token_re = re.compile(r"^\d+(?:[.,]\d{1,2})?$")


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
) -> dict[str, str | int | list[str]] | None:
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

    text_stripped = text.lstrip()

    if not text or not text_stripped.startswith("-"):
        return None

    rest_after_dash = text_stripped[1:].lstrip()
    if not rest_after_dash or not rest_after_dash[0].isdigit():
        return None

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

    if author_username not in participants:
        participants = [author_username] + participants

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


def parse_transfer_message(
        text: str,
        author_username: str,
        session_participants: Iterable[str],
) -> dict[str, str | int]:
    tokens = text.strip().split()
    if not tokens:
        raise ParseError(ParseErrorCode.INVALID_FORMAT)

    command = tokens[0].split("@", 1)[0]
    if command != "/transfer":
        raise ParseError(ParseErrorCode.INVALID_FORMAT)

    args = tokens[1:]
    if len(args) == 2:
        if _is_mention(args[0]):
            sender = args[0]
            raw_amount = args[1]
            recipient = author_username
        elif _is_mention(args[1]):
            sender = author_username
            raw_amount = args[0]
            recipient = args[1]
        else:
            raise ParseError(ParseErrorCode.INVALID_FORMAT)
    elif len(args) == 3 and _is_mention(args[0]) and _is_mention(args[2]):
        sender = args[0]
        raw_amount = args[1]
        recipient = args[2]
    else:
        raise ParseError(ParseErrorCode.INVALID_FORMAT)

    if not _amount_token_re.fullmatch(raw_amount):
        raise ParseError(ParseErrorCode.INVALID_FORMAT)

    amount_cents = _to_cents(raw_amount)

    if sender == recipient:
        raise ParseError(ParseErrorCode.INVALID_FORMAT)

    session_participants = list(session_participants)
    if sender not in session_participants or recipient not in session_participants:
        raise ParseError(ParseErrorCode.UNKNOWN_PEOPLE)

    return {
        "amount_cents": amount_cents,
        "sender": sender,
        "recipient": recipient,
    }
