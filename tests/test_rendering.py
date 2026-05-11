import unittest

from app.routers.history import history_nav_kb
from app.routers.sessions.parse import parse_new_args
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


if __name__ == "__main__":
    unittest.main()
