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


@dataclass(frozen=True)
class Transfer:
    amount_cents: int
    sender: str
    recipient: str


class Session:
    def __init__(self, sid: int, name: str, participants: List[str]):
        self.sid = sid
        self.name = name
        self.participants = list(dict.fromkeys(participants))
        self.expenses: List[Expense] = []
        self.transfers: List[Transfer] = []

    def totals_paid_cents(self) -> Dict[str, int]:
        paid = {u: 0 for u in self.participants}
        for e in self.expenses:
            paid[e.payer] += e.amount_cents
        return paid

    def totals_spent_cents(self) -> Dict[str, int]:
        spent = {u: 0 for u in self.participants}
        for e in self.expenses:
            n = len(e.participants)
            base = e.amount_cents // n
            rem = e.amount_cents % n
            for i, u in enumerate(e.participants):
                share = base + (1 if i < rem else 0)
                spent[u] += share
        return spent

    def add_expense(self, expense: Expense) -> None:

        if expense.payer not in self.participants:
            raise SessionError(SessionErrorCode.PAYER_NOT_IN_SESSION)

        for u in expense.participants:
            if u not in self.participants:
                raise SessionError(SessionErrorCode.PARTICIPANT_NOT_IN_SESSION)

        if expense.amount_cents <= 0:
            raise SessionError(SessionErrorCode.AMOUNT_MUST_BE_POSITIVE)

        self.expenses.append(expense)

    def add_transfer(self, transfer: Transfer) -> None:
        if transfer.sender not in self.participants:
            raise SessionError(SessionErrorCode.SENDER_NOT_IN_SESSION)

        if transfer.recipient not in self.participants:
            raise SessionError(SessionErrorCode.RECIPIENT_NOT_IN_SESSION)

        if transfer.sender == transfer.recipient:
            raise SessionError(SessionErrorCode.TRANSFER_TO_SELF)

        if transfer.amount_cents <= 0:
            raise SessionError(SessionErrorCode.AMOUNT_MUST_BE_POSITIVE)

        self.transfers.append(transfer)

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

        for t in self.transfers:
            net[t.sender] += t.amount_cents
            net[t.recipient] -= t.amount_cents

        return net

    def has_operations(self) -> bool:
        return bool(self.expenses or self.transfers)

    def actual_transfers_cents(self) -> Dict[Tuple[str, str], int]:
        totals: Dict[Tuple[str, str], int] = {}
        for t in self.transfers:
            key = (t.sender, t.recipient)
            totals[key] = totals.get(key, 0) + t.amount_cents
        return totals

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
