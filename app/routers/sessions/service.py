from app.db import SQLiteRepo
from app.texts import default_session_name


def create_new_session_db(
    repo: SQLiteRepo,
    chat_id: int,
    name: str | None,
    mentions: list[str],
    creator: str | None,
) -> tuple[int, str, list[str]]:

    if not name:
        name = default_session_name()

    sid = repo.create_session(chat_id, name)

    if creator:
        repo.add_participant(sid, creator)

    for u in mentions:
        repo.add_participant(sid, u)

    users = repo.list_participants(sid)
    return sid, name, users
