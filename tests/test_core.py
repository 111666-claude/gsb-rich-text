import unittest

from richtext.core import RichText, columns, plain


class ParseTest(unittest.TestCase):
    def test_plain_text_has_default_style(self):
        spans, malformed = RichText().parse("hello")
        self.assertEqual([t for t, _ in spans], ["hello"])
        self.assertEqual(malformed, 0)

    def test_bold_tag_is_applied(self):
        spans, _ = RichText().parse("[b]hi[/b]")
        self.assertTrue(all(s["bold"] for _, s in spans))

    def test_result_keys_are_stable(self):
        spans, _ = RichText().parse("hi")
        for key in ("bold", "color", "size"):
            self.assertIn(key, spans[0][1])


class WrapTest(unittest.TestCase):
    def test_empty_text_wraps_to_nothing(self):
        self.assertEqual(RichText().wrap("", 4), [])

    def test_plain_short_text_is_one_line(self):
        self.assertEqual(plain(RichText().wrap("abc", 4)), ["abc"])

    def test_columns_counts_characters(self):
        self.assertEqual(columns([("abc", {"bold": False, "color": None, "size": None})]), 3)


if __name__ == "__main__":
    unittest.main()
