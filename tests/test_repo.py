import tempfile
import unittest
from pathlib import Path

from app.db import SQLiteRepo


class SQLiteRepoTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.sqlite3"
        self.repo = SQLiteRepo(str(self.db_path))
        self.repo.init()

    def tearDown(self) -> None:
        self.repo.conn.close()
        self.temp_dir.cleanup()

    def test_create_load_session_with_expense(self) -> None:
        sid = self.repo.create_session(1001, "Trip")
        self.repo.add_participant(sid, "@a")
        self.repo.add_participant(sid, "@b")
        self.repo.add_expense(sid, "@a", 10000, "hotel", ["@a", "@b"])

        session = self.repo.load_session(1001)

        self.assertIsNotNone(session)
        self.assertEqual(session.name, "Trip")
        self.assertEqual(session.participants, ["@a", "@b"])
        self.assertEqual(session.net_balances_cents(), {"@a": 5000, "@b": -5000})

    def test_list_count_and_delete_expenses(self) -> None:
        sid = self.repo.create_session(1001, "Trip")
        self.repo.add_participant(sid, "@a")
        expense_id = self.repo.add_expense(sid, "@a", 500, "coffee", ["@a"])

        self.assertEqual(self.repo.count_expenses(sid), 1)
        self.assertEqual(self.repo.list_expenses(sid, limit=5, offset=0)[0]["title"], "coffee")
        self.assertTrue(self.repo.delete_expense(expense_id, sid))
        self.assertEqual(self.repo.count_expenses(sid), 0)

    def test_remove_participant_statuses(self) -> None:
        sid = self.repo.create_session(1001, "Trip")
        self.repo.add_participant(sid, "@a")
        self.repo.add_participant(sid, "@b")
        self.repo.add_expense(sid, "@a", 500, "coffee", ["@a"])

        self.assertEqual(self.repo.remove_participant(sid, "@missing"), "not_found")
        self.assertEqual(self.repo.remove_participant(sid, "@a"), "used")
        self.assertEqual(self.repo.remove_participant(sid, "@b"), "removed")


if __name__ == "__main__":
    unittest.main()
