from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class Expense:
    amount: float
    payer: str
    participants: List[str]
    description: str


class Session:
    def __init__(self, name: str, participants: List[str]):
        self.name = name
        self.participants = list(dict.fromkeys(participants))  # unique, keep order
        self.expenses: List[Expense] = []

    def add_expense(self, expense: Expense) -> None:
        # Мини-валидация чтобы не ловить сюрпризы
        if expense.payer not in self.participants:
            # Если плательщика нет в сессии - это ошибка концепта
            raise ValueError(f"Payer '{expense.payer}' not in session participants")

        for u in expense.participants:
            if u not in self.participants:
                raise ValueError(f"Participant '{u}' not in session participants")

        if expense.amount <= 0:
            raise ValueError("Amount must be > 0")

        self.expenses.append(expense)

    def totals_paid(self) -> Dict[str, float]:
        paid = {u: 0.0 for u in self.participants}
        for e in self.expenses:
            paid[e.payer] += e.amount
        return paid

    def net_balances(self) -> Dict[str, float]:
        """
        Возвращает net для каждого:
        + значит человек должен ПОЛУЧИТЬ (он переплатил)
        - значит человек должен ОТДАТЬ
        """
        net = {u: 0.0 for u in self.participants}

        for e in self.expenses:
            share = e.amount / len(e.participants)
            net[e.payer] += e.amount
            for u in e.participants:
                net[u] -= share

        # округлим для стабильности
        for u in net:
            net[u] = round(net[u], 2)

        return net

    def settlements(self) -> List[Tuple[str, str, float]]:
        """
        Возвращает список переводов (debtor -> creditor, amount)
        """
        net = self.net_balances()

        creditors = [(u, net[u]) for u in net if net[u] > 0.0]
        debtors = [(u, -net[u]) for u in net if net[u] < 0.0]

        # сортируем: кто больше должен/кто больше получает
        creditors.sort(key=lambda x: x[1], reverse=True)
        debtors.sort(key=lambda x: x[1], reverse=True)

        i = 0
        j = 0
        transfers: List[Tuple[str, str, float]] = []

        while i < len(debtors) and j < len(creditors):
            debtor, debt = debtors[i]
            creditor, credit = creditors[j]

            x = round(min(debt, credit), 2)
            if x > 0:
                transfers.append((debtor, creditor, x))

            debt -= x
            credit -= x

            debtors[i] = (debtor, round(debt, 2))
            creditors[j] = (creditor, round(credit, 2))

            if debtors[i][1] == 0:
                i += 1
            if creditors[j][1] == 0:
                j += 1

        return transfers

    def ensure_users(self, users: List[str]) -> None:
        for u in users:
            if u not in self.participants:
                self.participants.append(u)

