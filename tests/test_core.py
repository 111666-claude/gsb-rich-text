import unittest

from richtext.core import RichText, char_cols, columns, plain


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


class MalformedTest(unittest.TestCase):
    def test_unclosed_bracket_keeps_text(self):
        spans, malformed = RichText().parse("a[b")
        self.assertEqual("".join(t for t, _ in spans), "a[b")
        self.assertEqual(malformed, 1)

    def test_close_without_open_is_literal(self):
        spans, malformed = RichText().parse("x[/b]y")
        self.assertEqual("".join(t for t, _ in spans), "x[/b]y")
        self.assertEqual(malformed, 1)

    def test_mismatched_close_is_literal(self):
        spans, malformed = RichText().parse("[b]x[/color]y[/b]")
        self.assertEqual("".join(t for t, _ in spans), "x[/color]y")
        self.assertEqual(malformed, 1)
        self.assertTrue(all(s["bold"] for _, s in spans))

    def test_unknown_tag_is_literal(self):
        spans, malformed = RichText().parse("a[i]b")
        self.assertEqual("".join(t for t, _ in spans), "a[i]b")
        self.assertEqual(malformed, 1)

    def test_bad_color_value_is_literal(self):
        spans, malformed = RichText().parse("[color=red]x")
        self.assertEqual("".join(t for t, _ in spans), "[color=red]x")
        self.assertEqual(malformed, 1)


class EscapeTest(unittest.TestCase):
    def test_double_bracket_is_literal(self):
        spans, malformed = RichText().parse("a[[b]c")
        self.assertEqual("".join(t for t, _ in spans), "a[b]c")
        self.assertEqual(malformed, 0)

    def test_escape_does_not_open_tag(self):
        spans, malformed = RichText().parse("[[b]x")
        self.assertEqual("".join(t for t, _ in spans), "[b]x")
        self.assertEqual(malformed, 0)
        self.assertFalse(spans[-1][1]["bold"])


class NestTest(unittest.TestCase):
    def test_inner_close_keeps_outer_style(self):
        spans, _ = RichText().parse("[color=ff0000][b]x[/b]y[/color]")
        by_text = {t: s for t, s in spans}
        self.assertEqual(by_text["x"]["color"], "ff0000")
        self.assertTrue(by_text["x"]["bold"])
        self.assertEqual(by_text["y"]["color"], "ff0000")
        self.assertFalse(by_text["y"]["bold"])

    def test_close_pops_only_nearest_same_kind(self):
        spans, _ = RichText().parse("[b][b]x[/b]y[/b]")
        by_text = {t: s for t, s in spans}
        self.assertTrue(by_text["x"]["bold"])
        self.assertTrue(by_text["y"]["bold"])


class WrapColsTest(unittest.TestCase):
    def test_wide_chars_count_two_columns(self):
        lines = RichText().wrap("中文字符测试", 6)
        self.assertEqual(len(lines), 2)
        self.assertEqual(max(columns(line) for line in lines), 6)
        self.assertEqual(plain(lines), ["中文字", "符测试"])

    def test_wide_char_never_split(self):
        lines = RichText().wrap("ab中cd", 3)
        self.assertEqual(plain(lines), ["ab", "中c", "d"])

    def test_style_survives_line_break(self):
        lines = RichText().wrap("[b]aaaaaaaaaa[/b]", 4)
        self.assertEqual(len(lines), 3)
        self.assertTrue(all(s["bold"] for line in lines for _, s in line))

    def test_leading_space_at_break_is_dropped(self):
        self.assertEqual(plain(RichText().wrap("ab cd", 2)), ["ab", "cd"])

    def test_wrap_is_repeatable(self):
        text = "[color=00ff00]ab中文[/color] [b]xy[/b]"
        first = RichText().wrap(text, 5)
        second = RichText().wrap(text, 5)
        self.assertEqual(plain(first), plain(second))
        self.assertEqual(first, second)

    def test_char_cols(self):
        self.assertEqual(char_cols("a"), 1)
        self.assertEqual(char_cols("中"), 2)


if __name__ == "__main__":
    unittest.main()
