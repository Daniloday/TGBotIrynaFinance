from app.texts import MSG


def build_session_created_text(name: str, users: list[str]) -> str:
    users_text = "\n".join(f"• {u}" for u in users) if users else MSG.EMPTY_DASH
    return (
        f"{MSG.SESSION_CREATED}\n\n"
        + MSG.SESSION_CREATED_NAME.format(name=name)
        + "\n\n"
        + MSG.SESSION_CREATED_USERS.format(users=users_text)
    )
