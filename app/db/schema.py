import sqlite3


def init_schema(conn: sqlite3.Connection) -> None:
    c = conn.cursor()

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
        amount_cents INTEGER,
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

    c.execute("""
    CREATE TABLE IF NOT EXISTS transfers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        sender TEXT,
        recipient TEXT,
        amount_cents INTEGER,
        created_at INTEGER,
        FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
    )
    """)

    c.execute("CREATE INDEX IF NOT EXISTS idx_sessions_chat_created ON sessions(chat_id, created_at)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_expenses_session_created ON expenses(session_id, created_at)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_transfers_session_created ON transfers(session_id, created_at)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_participants_session ON participants(session_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_exp_participants_expense ON expense_participants(expense_id)")

    conn.commit()
