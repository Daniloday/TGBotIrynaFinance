import sqlite3
import time
import os
from typing import List
from app.session import Session, Expense


class SQLiteRepo:
    def __init__(self, db_path: str):
        # гарантируем папку
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def init(self):
        c = self.conn.cursor()

        c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            chat_id INTEGER PRIMARY KEY,
            created_at INTEGER
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            chat_id INTEGER,
            username TEXT,
            UNIQUE(chat_id, username)
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            amount REAL,
            payer TEXT,
            title TEXT,
            created_at INTEGER
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS expense_participants (
            expense_id INTEGER,
            username TEXT
        )
        """)

        self.conn.commit()

    # ---------- participants ----------

    def add_participant(self, chat_id: int, username: str):
        c = self.conn.cursor()
        c.execute(
            "INSERT OR IGNORE INTO participants (chat_id, username) VALUES (?, ?)",
            (chat_id, username),
        )
        self.conn.commit()

    def get_participants(self, chat_id: int) -> list[str]:
        c = self.conn.cursor()
        c.execute(
            "SELECT username FROM participants WHERE chat_id = ? ORDER BY username",
            (chat_id,),
        )
        return [r["username"] for r in c.fetchall()]

    # ---------- expenses ----------

    def add_expense(
        self,
        chat_id: int,
        payer: str,
        amount: float,
        title: str,
        participants: list[str],
    ):
        c = self.conn.cursor()
        c.execute(
            """
            INSERT INTO expenses (chat_id, amount, payer, title, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (chat_id, amount, payer, title, int(time.time())),
        )
        expense_id = c.lastrowid

        for u in participants:
            c.execute(
                "INSERT INTO expense_participants (expense_id, username) VALUES (?, ?)",
                (expense_id, u),
            )

        self.conn.commit()

    def list_expenses(self, chat_id: int):
        c = self.conn.cursor()
        c.execute(
            "SELECT * FROM expenses WHERE chat_id = ? ORDER BY created_at",
            (chat_id,),
        )
        expenses = c.fetchall()

        result = []
        for e in expenses:
            c.execute(
                "SELECT username FROM expense_participants WHERE expense_id = ?",
                (e["id"],),
            )
            parts = [r["username"] for r in c.fetchall()]

            result.append(
                {
                    "payer": e["payer"],
                    "amount": e["amount"],
                    "title": e["title"],
                    "participants": parts,
                }
            )
        return result

    def reset(self, chat_id: int):
        c = self.conn.cursor()

        c.execute(
            "SELECT id FROM expenses WHERE chat_id = ?",
            (chat_id,),
        )
        ids = [r["id"] for r in c.fetchall()]

        for eid in ids:
            c.execute("DELETE FROM expense_participants WHERE expense_id = ?", (eid,))

        c.execute("DELETE FROM expenses WHERE chat_id = ?", (chat_id,))
        c.execute("DELETE FROM participants WHERE chat_id = ?", (chat_id,))
        self.conn.commit()

    def load_session(self, chat_id: int) -> Session:
        participants = self.get_participants(chat_id)

        session = Session(
            name=str(chat_id),
            participants=participants,
        )

        expenses = self.list_expenses(chat_id)
        for e in expenses:
            session.add_expense(
                Expense(
                    amount=e["amount"],
                    payer=e["payer"],
                    participants=e["participants"],
                    description=e["title"],
                )
            )

        return session