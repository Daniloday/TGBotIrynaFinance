import os
import sqlite3
import time
from typing import List, Literal

from app.services.session import Session, Expense, Transfer
from .schema import init_schema

RemoveStatus = Literal["removed", "not_found", "used"]


class SQLiteRepo:
    def __init__(self, db_path: str):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")

    def init(self) -> None:
        init_schema(self.conn)

    # ---------- sessions ----------

    def create_session(self, chat_id: int, name: str) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO sessions (chat_id, name, created_at)
            VALUES (?, ?, ?)
            """,
            (chat_id, name, int(time.time())),
        )
        self.conn.commit()
        return cur.lastrowid

    def delete_chat_session(self, chat_id: int) -> None:
        self.conn.execute("DELETE FROM sessions WHERE chat_id=?", (chat_id,))
        self.conn.commit()

    def load_session(self, chat_id: int) -> Session | None:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, name FROM sessions WHERE chat_id=? ORDER BY created_at DESC LIMIT 1",
            (chat_id,),
        )
        s = cur.fetchone()
        if not s:
            return None

        session_id = s["id"]
        name = s["name"] or str(session_id)
        parts = self.list_participants(session_id)

        session = Session(sid=session_id, name=name, participants=parts)

        self._load_expenses(session)
        self._load_transfers(session)

        return session

    def _load_expenses(self, session: Session) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, payer, amount_cents, title, created_at FROM expenses WHERE session_id=? ORDER BY created_at",
            (session.sid,),
        )
        expenses = cur.fetchall()
        if not expenses:
            return

        ids = [e["id"] for e in expenses]
        placeholders = ",".join("?" for _ in ids)
        cur.execute(
            f"SELECT expense_id, username FROM expense_participants WHERE expense_id IN ({placeholders})",
            ids,
        )
        parts_map: dict[int, list[str]] = {}
        for r in cur.fetchall():
            parts_map.setdefault(r["expense_id"], []).append(r["username"])

        for e in expenses:
            session.add_expense(
                Expense(
                    amount_cents=e["amount_cents"],
                    payer=e["payer"],
                    participants=parts_map.get(e["id"], []),
                    description=e["title"],
                )
            )

    def _load_transfers(self, session: Session) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT sender, recipient, amount_cents
            FROM transfers
            WHERE session_id=?
            ORDER BY created_at
            """,
            (session.sid,),
        )
        for r in cur.fetchall():
            session.add_transfer(
                Transfer(
                    amount_cents=r["amount_cents"],
                    sender=r["sender"],
                    recipient=r["recipient"],
                )
            )

    # ---------- participants ----------

    def participant_exists(self, session_id: int, username: str) -> bool:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT 1 FROM participants WHERE session_id=? AND username=? LIMIT 1",
            (session_id, username),
        )
        return cur.fetchone() is not None

    def add_participant(self, session_id: int, username: str) -> bool:
        with self.conn:
            cur = self.conn.execute(
                "INSERT OR IGNORE INTO participants (session_id, username) VALUES (?, ?)",
                (session_id, username),
            )
            return cur.rowcount == 1

    def can_remove_participant(self, session_id: int, username: str) -> bool:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT 1 FROM expenses WHERE session_id=? AND payer=? LIMIT 1",
            (session_id, username),
        )
        if cur.fetchone():
            return False

        cur.execute(
            """
            SELECT 1
            FROM expense_participants ep
            JOIN expenses e ON e.id = ep.expense_id
            WHERE e.session_id=? AND ep.username=?
            LIMIT 1
            """,
            (session_id, username),
        )
        if cur.fetchone():
            return False

        cur.execute(
            """
            SELECT 1
            FROM transfers
            WHERE session_id=? AND (sender=? OR recipient=?)
            LIMIT 1
            """,
            (session_id, username, username),
        )
        return cur.fetchone() is None

    def remove_participant(self, session_id: int, username: str) -> RemoveStatus:
        if not self.participant_exists(session_id, username):
            return "not_found"

        if not self.can_remove_participant(session_id, username):
            return "used"

        with self.conn:
            cur = self.conn.execute(
                "DELETE FROM participants WHERE session_id=? AND username=?",
                (session_id, username),
            )
            return "removed" if cur.rowcount > 0 else "not_found"

    def list_participants(self, session_id: int) -> List[str]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT username FROM participants WHERE session_id=? ORDER BY username",
            (session_id,),
        )
        return [r["username"] for r in cur.fetchall()]

    # ---------- expenses ----------

    def add_expense(
        self,
        session_id: int,
        payer: str,
        amount_cents: int,
        title: str,
        participants: List[str],
    ) -> int:
        with self.conn:
            cur = self.conn.cursor()
            cur.execute(
                """
                INSERT INTO expenses (session_id, payer, amount_cents, title, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, payer, amount_cents, title, int(time.time())),
            )
            eid = cur.lastrowid

            for u in participants:
                cur.execute(
                    "INSERT INTO expense_participants (expense_id, username) VALUES (?, ?)",
                    (eid, u),
                )

        return eid

    def delete_expense(self, expense_id: int, session_id: int) -> bool:
        with self.conn:
            cur = self.conn.cursor()
            cur.execute(
                "DELETE FROM expenses WHERE id=? AND session_id=?",
                (expense_id, session_id),
            )
            return cur.rowcount > 0

    def list_expenses(self, session_id: int, limit: int, offset: int) -> list[dict]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT id, payer, amount_cents, title, created_at
            FROM expenses
            WHERE session_id=?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (session_id, limit, offset),
        )
        rows = cur.fetchall()
        if not rows:
            return []

        ids = [r["id"] for r in rows]
        placeholders = ",".join("?" for _ in ids)

        cur.execute(
            f"SELECT expense_id, username FROM expense_participants WHERE expense_id IN ({placeholders})",
            ids,
        )

        parts_map: dict[int, list[str]] = {}
        for r in cur.fetchall():
            parts_map.setdefault(r["expense_id"], []).append(r["username"])

        expenses: list[dict] = []
        for r in rows:
            expenses.append(
                {
                    "id": r["id"],
                    "payer": r["payer"],
                    "amount_cents": r["amount_cents"],
                    "title": r["title"],
                    "participants": parts_map.get(r["id"], []),
                    "created_at": r["created_at"],
                }
            )

        return expenses

    def count_expenses(self, session_id: int) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM expenses WHERE session_id=?", (session_id,))
        return cur.fetchone()["cnt"]

    # ---------- transfers ----------

    def add_transfer(
        self,
        session_id: int,
        sender: str,
        recipient: str,
        amount_cents: int,
    ) -> int:
        with self.conn:
            cur = self.conn.cursor()
            cur.execute(
                """
                INSERT INTO transfers (session_id, sender, recipient, amount_cents, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, sender, recipient, amount_cents, int(time.time())),
            )
            return cur.lastrowid

    def delete_transfer(self, transfer_id: int, session_id: int) -> bool:
        with self.conn:
            cur = self.conn.cursor()
            cur.execute(
                "DELETE FROM transfers WHERE id=? AND session_id=?",
                (transfer_id, session_id),
            )
            return cur.rowcount > 0

    def count_transfers(self, session_id: int) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM transfers WHERE session_id=?", (session_id,))
        return cur.fetchone()["cnt"]
