import unittest

from app.domain.errors import SessionError, SessionErrorCode
from app.services.session import Expense, Session


class SessionTest(unittest.TestCase):
    def test_totals_and_net_balances_split_cents(self) -> None:
        session = Session(1, "Trip", ["@a", "@b", "@c"])

        session.add_expense(Expense(10001, "@a", ["@a", "@b", "@c"], "hotel"))

        self.assertEqual(session.totals_paid_cents(), {"@a": 10001, "@b": 0, "@c": 0})
        self.assertEqual(session.totals_spent_cents(), {"@a": 3334, "@b": 3334, "@c": 3333})
        self.assertEqual(session.net_balances_cents(), {"@a": 6667, "@b": -3334, "@c": -3333})

    def test_calculate_transfers(self) -> None:
        session = Session(1, "Trip", ["@a", "@b", "@c"])
        session.add_expense(Expense(9000, "@a", ["@a", "@b", "@c"], "hotel"))

        self.assertEqual(session.calculate_transfers(), [("@b", "@a", 3000), ("@c", "@a", 3000)])

    def test_rejects_unknown_payer(self) -> None:
        session = Session(1, "Trip", ["@a"])

        with self.assertRaises(SessionError) as cm:
            session.add_expense(Expense(100, "@b", ["@a"], "coffee"))

        self.assertEqual(cm.exception.code, SessionErrorCode.PAYER_NOT_IN_SESSION)

    def test_rejects_unknown_participant(self) -> None:
        session = Session(1, "Trip", ["@a"])

        with self.assertRaises(SessionError) as cm:
            session.add_expense(Expense(100, "@a", ["@b"], "coffee"))

        self.assertEqual(cm.exception.code, SessionErrorCode.PARTICIPANT_NOT_IN_SESSION)

    def test_rejects_non_positive_amount(self) -> None:
        session = Session(1, "Trip", ["@a"])

        with self.assertRaises(SessionError) as cm:
            session.add_expense(Expense(0, "@a", ["@a"], "coffee"))

        self.assertEqual(cm.exception.code, SessionErrorCode.AMOUNT_MUST_BE_POSITIVE)


if __name__ == "__main__":
    unittest.main()
