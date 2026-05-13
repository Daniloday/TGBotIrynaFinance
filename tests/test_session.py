import unittest

from app.domain.errors import SessionError, SessionErrorCode
from app.services.session import Expense, Session, Transfer


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

    def test_transfer_reduces_debt(self) -> None:
        session = Session(1, "Trip", ["@a", "@b"])
        session.add_expense(Expense(10000, "@a", ["@a", "@b"], "hotel"))
        session.add_transfer(Transfer(2000, "@b", "@a"))

        self.assertEqual(session.net_balances_cents(), {"@a": 3000, "@b": -3000})
        self.assertEqual(session.calculate_transfers(), [("@b", "@a", 3000)])

    def test_multiple_transfers_are_aggregated(self) -> None:
        session = Session(1, "Trip", ["@a", "@b"])
        session.add_transfer(Transfer(1000, "@b", "@a"))
        session.add_transfer(Transfer(1500, "@b", "@a"))

        self.assertEqual(session.actual_transfers_cents(), {("@b", "@a"): 2500})

    def test_closed_debt_has_no_calculated_transfers(self) -> None:
        session = Session(1, "Trip", ["@a", "@b"])
        session.add_expense(Expense(10000, "@a", ["@a", "@b"], "hotel"))
        session.add_transfer(Transfer(5000, "@b", "@a"))

        self.assertEqual(session.net_balances_cents(), {"@a": 0, "@b": 0})
        self.assertEqual(session.calculate_transfers(), [])

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

    def test_rejects_transfer_to_self(self) -> None:
        session = Session(1, "Trip", ["@a"])

        with self.assertRaises(SessionError) as cm:
            session.add_transfer(Transfer(100, "@a", "@a"))

        self.assertEqual(cm.exception.code, SessionErrorCode.TRANSFER_TO_SELF)


if __name__ == "__main__":
    unittest.main()
