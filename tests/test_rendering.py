import unittest

from app.routers.history import history_nav_kb
from app.routers.balances.render import build_balance_text
from app.routers.sessions.parse import parse_new_args
from app.services.session import Session, Transfer
from app.utils.currency import format_uah


class RenderingHelpersTest(unittest.TestCase):
    def test_format_uah(self) -> None:
        self.assertEqual(format_uah(123456), "1 234.56 грн")
        self.assertEqual(format_uah(-500), "-5.00 грн")

    def test_parse_new_args(self) -> None:
        self.assertEqual(parse_new_args("/new Trip @a @b"), ("Trip", ["@a", "@b"]))
        self.assertEqual(parse_new_args("/new @a"), (None, ["@a"]))

    def test_history_nav_keyboard(self) -> None:
        kb = history_nav_kb(2, 3, prefix="hist:", back_cb="back")

        self.assertEqual(kb.inline_keyboard[0][0].callback_data, "hist:1")
        self.assertEqual(kb.inline_keyboard[0][1].callback_data, "hist:3")
        self.assertEqual(kb.inline_keyboard[1][0].callback_data, "back")

    def test_balance_text_includes_actual_transfers(self) -> None:
        session = Session(1, "Trip", ["@a", "@b"])
        session.add_transfer(Transfer(50000, "@b", "@a"))

        text = build_balance_text(session)

        self.assertIn("Хто кому скинув:", text)
        self.assertIn("@b → @a: 500.00 грн", text)


if __name__ == "__main__":
    unittest.main()
