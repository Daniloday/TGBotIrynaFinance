from datetime import datetime

START_TEXT = (
    "Привіт, я Ірина 🙂\n"
    "Я рахую спільні витрати в чаті.\n\n"
    "Формат:\n"
    "-450 піца\n"
    "-600 @danil бар @anna @roma\n"
    "-120,67 таксі додому\n\n"
    "Правила:\n"
    "• Імена людей тільки через @\n"
    "• Без опису витрати не приймаю\n\n"
    "Команди:\n"
    "/members — учасники\n"
    "/balance — хто кому винен\n"
)


class MSG:
    NO_USERNAME = "У тебе немає Telegram username. Додай його в налаштуваннях."
    MEMBERS_EMPTY = "Поки що немає учасників."
    NO_EXPENSES = "Ще немає витрат. Напиши щось типу: -450 піца"
    RESET_DONE = "Готово. Все стерла, починаємо з нуля ✅"
    EXPENSE_SAVED = "Записала ✅"

    NO_SESSION = "❗ Спочатку створи сесію через /new"
    SESSION_CREATED = "✅ Сесію створено"
    SESSION_DELETED = "🗑️ Сесію видалено. Почни нову через /new"
    SESSION_NOT_FOUND = "❗ Немає активної сесії"

    NO_PARTICIPANTS = "❗ У сесії немає учасників. Додай людей через /add @username"
    ADD_FORMAT = "Формат: /add @username @username2"
    REMOVE_FORMAT = "Формат: /remove @username"
    CANT_REMOVE_USED = "❗ Не можу видалити: цей учасник вже фігурує у витратах"

    # Parse errors
    PARSE_INVALID_FORMAT = "Невірний формат. Приклад: -450 піца або -120,67 таксі"
    PARSE_NO_TITLE = "Без опису витрати не приймаю."
    PARSE_UNKNOWN_PEOPLE = "Є люди, яких немає в учасниках сесії. Додай їх через /add"
    PARSE_BAD_AMOUNT = "Сума має бути > 0 і з максимум 2 знаками після коми."

    EXPENSE_SAVED_DETAILS = (
        "{payer} — {amount}\n"
        "{title}\n"
        "Учасники: {participants}"
    )

    SESSION_CREATED_NAME = "Назва: {name}"
    SESSION_CREATED_USERS = "Учасники:\n{users}"
    EMPTY_DASH = "—"

    NO_ACTIVE_SESSION = "❗ Немає активної сесії"

    MEMBERS_TITLE = "Учасники:\n{users}"
    MEMBERS_EMPTY_ADD = "Поки що немає учасників. Додай через /add @username"
    ADDED_USERS = "✅ Додала: {users}"
    REMOVE_CANT_USED = "❗ Не можу видалити: цей учасник вже фігурує у витратах"
    REMOVED_USER = "✅ Видалила {user}"

    NO_EXPENSES_YET = "Ще немає витрат"
    BALANCE_TITLE = "Баланс:\n{lines}"
    TRANSFERS_TITLE = "💸 Хто кому скидає:\n{lines}"
    TRANSFERS_NONE = "Ніхто нікому не винен ✅"

    EXPENSE_DELETED = "🗑️ Трату видалено ✅"
    EXPENSE_DELETE_BTN = "🗑️ Видалити трату"
    EXPENSE_DELETE_ERROR = "Не знайдено або вже видалено"
    EXPENSE_DELETE_BAD_DATA = "Хибні дані"


def default_session_name() -> str:
    return datetime.now().strftime("Сесія %d.%m %H:%M")
