import sqlite3
import time
import os
from typing import List
from app.session import Session, Expense


class SQLiteRepo:
    def __init__(self, db_path: str):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")

    def init(self):
        c = self.conn.cursor()

        c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            name TEXT,
            created_at INTEGER
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            session_id INTEGER,
            username TEXT,
            UNIQUE(session_id, username),
            FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            payer TEXT,
            amount INTEGER,
            title TEXT,
            created_at INTEGER,
            FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS expense_participants (
            expense_id INTEGER,
            username TEXT,
            UNIQUE(expense_id, username),
            FOREIGN KEY(expense_id) REFERENCES expenses(id) ON DELETE CASCADE
        )
        """)

        c.execute("CREATE INDEX IF NOT EXISTS idx_sessions_chat_created ON sessions(chat_id, created_at)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_expenses_session_created ON expenses(session_id, created_at)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_participants_session ON participants(session_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_exp_participants_expense ON expense_participants(expense_id)")

        self.conn.commit()

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

    def delete_chat_session(self, chat_id: int):
        self.conn.execute("DELETE FROM sessions WHERE chat_id=?", (chat_id,))
        self.conn.commit()

    # ---------- participants ----------

    def add_participant(self, session_id: int, username: str):
        with self.conn:
            self.conn.execute(
                "INSERT OR IGNORE INTO participants (session_id, username) VALUES (?, ?)",
                (session_id, username),
            )

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
        return cur.fetchone() is None

    def remove_participant(self, session_id: int, username: str) -> bool:
        if not self.can_remove_participant(session_id, username):
            return False
        with self.conn:
            self.conn.execute(
                "DELETE FROM participants WHERE session_id=? AND username=?",
                (session_id, username),
            )
        return True

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
    ):
        with self.conn:
            cur = self.conn.cursor()
            cur.execute(
                """
                INSERT OR IGNORE INTO expenses (session_id, payer, amount, title, created_at)
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

        cur.execute(
            "SELECT * FROM expenses WHERE session_id=? ORDER BY created_at",
            (session_id,),
        )
        expenses = cur.fetchall()

        for e in expenses:
            cur.execute(
                "SELECT username FROM expense_participants WHERE expense_id=?",
                (e["id"],),
            )
            p = [r["username"] for r in cur.fetchall()]

            session.add_expense(
                Expense(
                    amount_cents=e["amount"],
                    payer=e["payer"],
                    participants=p,
                    description=e["title"],
                )
            )

        return session

