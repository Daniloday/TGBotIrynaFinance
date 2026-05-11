import unittest

from app.domain.errors import ParseError, ParseErrorCode
from app.utils.parser import parse_message


class ParserTest(unittest.TestCase):
    participants = ["@author", "@roma", "@anna"]

    def test_plain_text_is_not_expense(self) -> None:
        self.assertIsNone(parse_message("hello", "@author", self.participants))

    def test_dash_without_amount_is_not_expense(self) -> None:
        self.assertIsNone(parse_message("- hello", "@author", self.participants))

    def test_amount_without_fraction(self) -> None:
        parsed = parse_message("-80 pizza", "@author", self.participants)

        self.assertEqual(parsed, {
            "amount_cents": 8000,
            "title": "pizza",
            "payer": "@author",
            "participants": self.participants,
        })

    def test_amount_with_comma_fraction_and_space_after_dash(self) -> None:
        parsed = parse_message("- 80,50 taxi", "@author", self.participants)

        self.assertEqual(parsed["amount_cents"], 8050)
        self.assertEqual(parsed["title"], "taxi")

    def test_first_mention_after_amount_is_payer(self) -> None:
        parsed = parse_message("-420 @roma bar", "@author", self.participants)

        self.assertEqual(parsed["payer"], "@roma")
        self.assertEqual(parsed["participants"], self.participants)

    def test_mentions_after_title_are_expense_participants(self) -> None:
        parsed = parse_message("-420 bar @anna", "@author", self.participants)

        self.assertEqual(parsed["participants"], ["@author", "@anna"])

    def test_empty_title_fails(self) -> None:
        with self.assertRaises(ParseError) as cm:
            parse_message("-80 @roma", "@author", self.participants)

        self.assertEqual(cm.exception.code, ParseErrorCode.NO_TITLE)

    def test_unknown_people_fail(self) -> None:
        with self.assertRaises(ParseError) as cm:
            parse_message("-80 bar @missing", "@author", self.participants)

        self.assertEqual(cm.exception.code, ParseErrorCode.UNKNOWN_PEOPLE)


if __name__ == "__main__":
    unittest.main()
