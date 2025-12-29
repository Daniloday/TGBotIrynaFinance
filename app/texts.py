from datetime import datetime

from app.utils.time import TZ

# ------------------------------------------------------------
# Start / Help
# ------------------------------------------------------------

START_TEXT = (
    "Привіт, я Ірина 🙂\n"
    "Я рахую спільні витрати в цьому чаті 💸\n\n"
    "Швидкий старт:\n"
    "• додай мене у групу\n"
    "• створи нову сесію командою /new [назва (не обов'язкова)] @user1 @user2\n"
    "• записуйте витрати\n\n"
    "Як писати витрати?\n"
    "-900 піца\n"
    "  ти оплатив, витрата ділиться на всіх учасників сесії\n\n"
    "-900 кіно @roma @misha\n"
    "  ти оплатив, витрата ділиться на тебе, Рому та Мішу\n\n"
    "-280 @roma таксі\n"
    "  Рома оплатив, витрата ділиться на всіх учасників сесії\n\n"
    "-1240 @roma бар @andrew\n"
    "  Рома оплатив, витрата ділиться на тебе (автор повідомлення), Рому та Андрія\n\n"
    "Що далі?\n"
    "• викликай /check щоб все порахувати\n\n"
    "Правила:\n"
    "• Сума: '-' + число (можна з комою), максимум 2 знаки після коми\n"
    "• @ (якщо є) ДО опису - хто платив, інакше платник - автор\n"
    "• @ ПІСЛЯ опису (якщо є) - учасники витрати, інакше всі учасники сесії\n"
    "• Автор повідомлення завжди рахується учасником витрати\n"
    "• З учасниками без нікнейму не працюю\n"
    "• Без опису витрати не приймаю\n\n"
    "Команди:\n"
    "/help — підказка\n"
    "/new [назва (не обов'язкова)] @user1 @user2 — нова сесія\n"
    "/add @user1 @user2 — додати людей\n"
    "/remove @username — видалити людину\n"
    "/check — розрахувати\n"
    "/history — історія витрат\n"
    "/members — учасники\n"
    "/balance — баланс\n"
)

HELP_TEXT = START_TEXT


# ------------------------------------------------------------
# Messages
# ------------------------------------------------------------

class MSG:
    # Common / account
    EMPTY_DASH = ""
    NO_USERNAME = "У тебе немає Telegram username. Додай його в налаштуваннях"
    RESET_DONE = "Готово. Все стерла, починаємо з нуля ✅"

    # Session
    NO_SESSION = "❗ Немає активної сесії. Створи через /new"
    SESSION_CREATED = "✅ Сесію створено"
    SESSION_CREATED_NAME = "Назва: {name}"
    SESSION_CREATED_USERS = "Учасники:\n{users}"

    SESSION_DELETED = "🗑️ Сесію видалено. Почни нову через /new"

    SESSION_DELETE_CONFIRM_TITLE = (
        "⚠️ Ти точно хочеш видалити сесію?\n"
        "Всі дані цієї сесії будуть втрачені назавжди"
    )
    SESSION_DELETE_CONFIRM_NAME = "Сесія: {name}"
    SESSION_DELETE_BTN_YES = "✅ Так, видалити"
    SESSION_DELETE_BTN_NO = "❌ Скасувати"
    SESSION_DELETE_CANCELED = "Ок, не видаляю 👍"
    SESSION_DELETE_BAD_DATA = "❗ Хибні дані"
    SESSION_DELETE_NOT_ACTUAL = "ℹ️ Ця сесія вже неактуальна"

    SESSION_NEW_CONFIRM_TITLE = (
        "⚠️ Створити нову сесію?\n"
        "Всі дані поточної сесії будуть втрачені"
    )
    SESSION_NEW_CONFIRM_NAME = "Поточна: {name}"
    SESSION_NEW_BTN_YES = "✅ Так, створити нову"
    SESSION_NEW_BTN_NO = "❌ Скасувати"
    SESSION_NEW_CANCELED = "Ок, залишаємо поточну сесію 👍"
    SESSION_NEW_BAD_DATA = "❗ Хибні дані"

    # Members
    MEMBERS_TITLE = "{name}\n\nУчасники:\n{users}"
    MEMBERS_EMPTY_ADD = "Поки що немає учасників. Додай через /add @username"

    ADD_FORMAT = "Формат: /add @username @username2"
    REMOVE_FORMAT = "Формат: /remove @username"

    NO_PARTICIPANTS = "❗ У сесії немає учасників. Додай людей через /add @username"
    EXPENSE_NEED_TWO_PARTICIPANTS = (
        "❗ Для додавання витрати потрібно мінімум 2 учасники.\n"
        "Додай ще когось через /add @username"
    )

    ADDED_USERS = "✅ Додала: {users}"
    ALREADY_USERS = "ℹ️ Вже є в сесії: {users}"

    REMOVED_USER = "✅ Видалила {user}"
    REMOVE_NOT_FOUND = "ℹ️ {user} і так немає в сесії"
    CANT_REMOVE_USED = "❗ Не можу видалити: цей учасник вже фігурує у витратах"

    # Parse errors
    PARSE_INVALID_FORMAT = "Невірний формат. Приклад: -450 піца або -120,67 таксі"
    PARSE_NO_TITLE = "Без опису витрати не приймаю"
    PARSE_UNKNOWN_PEOPLE = "Є люди, яких немає в учасниках сесії. Додай їх через /add @username"
    PARSE_BAD_AMOUNT = "Сума має бути > 0 і з максимум двома знаками після коми"

    # Expenses
    NO_EXPENSES = "Ще немає витрат. Напиши щось типу: -450 піца"
    EXPENSE_SAVED = "Записала ✅"

    EXPENSE_SAVED_DETAILS = (
        "\n{title}\n{payer} — {amount}\n\n"
        "Учасники витрати:\n{participants}"
    )

    EXPENSE_DELETED = "🗑️ Витрату видалено ✅"
    EXPENSE_DELETE_BTN = "🗑️ Видалити витрату"
    EXPENSE_DELETE_ERROR = "Не знайдено або вже видалено"
    EXPENSE_DELETE_BAD_DATA = "❗ Хибні дані"

    # Balance / Check
    CHECK_BTN_HISTORY = "🧾 Історія"
    CHECK_BTN_DETAILS = "📊 Деталі"
    BTN_BACK = "↩️ Назад"
    BTN_CALCULATE = "💸 Розрахувати"

    TRANSFERS_TITLE = "{name}\n\n💸 Хто кому скидає:\n{lines}"
    TRANSFERS_NONE = "Ніхто нікому не винен ✅"

    BALANCE_BLOCK_TITLE = "Баланс:\n{lines}"
    BALANCE_PAID_TITLE = "Хто скільки платив:\n{lines}"
    BALANCE_SPENT_TITLE = "Хто скільки витратив:\n{lines}"

    BALANCE_FULL = (
        "{name}\n\n"
        "{balance}\n\n"
        "____________________________________\n\n"
        "{paid}\n\n"
        "{spent}"
    )

    # History
    HISTORY_TITLE = "🧾 Історія витрат (стор. {page}/{pages})"
    HISTORY_EMPTY = "Ще немає витрат"
    HISTORY_ITEM = (
        "{idx}) {time} · {payer}\n"
        "{title}\n"
        "{amount}\n"
        "Учасники: {participants}"
    )

    HISTORY_PREV = "⬅️"
    HISTORY_NEXT = "➡️"

    HISTORY_DAY_TODAY = "📅 Сьогодні"
    HISTORY_DAY_YESTERDAY = "📅 Вчора"
    HISTORY_DAY_DATE = "📅 {date}"


def default_session_name() -> str:
    now = datetime.now(TZ)
    return now.strftime("Сесія %d.%m %H:%M")
