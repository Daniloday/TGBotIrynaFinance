from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from app.domain.errors import SessionError, SessionErrorCode


@dataclass(frozen=True)
class Expense:
    amount_cents: int
    payer: str
    participants: List[str]
    description: str


class Session:
    def __init__(self, sid: int, name: str, participants: List[str]):
        self.sid = sid
        self.name = name
        self.participants = list(dict.fromkeys(participants))
        self.expenses: List[Expense] = []

    def add_expense(self, expense: Expense) -> None:

        if expense.payer not in self.participants:
            raise SessionError(SessionErrorCode.PAYER_NOT_IN_SESSION)

        for u in expense.participants:
            if u not in self.participants:
                raise SessionError(SessionErrorCode.PARTICIPANT_NOT_IN_SESSION)

        if expense.amount_cents <= 0:
            raise SessionError(SessionErrorCode.AMOUNT_MUST_BE_POSITIVE)

        self.expenses.append(expense)

    def net_balances_cents(self) -> Dict[str, int]:
        net = {u: 0 for u in self.participants}

        for e in self.expenses:
            n = len(e.participants)
            base = e.amount_cents // n
            rem = e.amount_cents % n

            net[e.payer] += e.amount_cents

            for i, u in enumerate(e.participants):
                share = base + (1 if i < rem else 0)
                net[u] -= share

        return net

    def calculate_transfers(self) -> List[Tuple[str, str, int]]:
        net = self.net_balances_cents()

        creditors = [(u, v) for u, v in net.items() if v > 0]
        debtors = [(u, -v) for u, v in net.items() if v < 0]

        creditors.sort(key=lambda x: x[1], reverse=True)
        debtors.sort(key=lambda x: x[1], reverse=True)

        i = j = 0
        transfers = []

        while i < len(debtors) and j < len(creditors):
            d, debt = debtors[i]
            c, credit = creditors[j]

            x = min(debt, credit)
            transfers.append((d, c, x))

            debt -= x
            credit -= x

            debtors[i] = (d, debt)
            creditors[j] = (c, credit)

            if debt == 0:
                i += 1
            if credit == 0:
                j += 1

        return transfers
