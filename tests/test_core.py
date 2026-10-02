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


class MalformedTest(unittest.TestCase):
    def test_unclosed_bracket_is_literal_and_counted(self):
        spans, malformed = RichText().parse("a[b")
        self.assertEqual("".join(t for t, _ in spans), "a[b")
        self.assertEqual(malformed, 1)

    def test_unclosed_bracket_does_not_swallow_text(self):
        spans, malformed = RichText().parse("a[bcdef")
        self.assertEqual("".join(t for t, _ in spans), "a[bcdef")
        self.assertEqual(malformed, 1)

    def test_close_without_open_is_literal_and_counted(self):
        spans, malformed = RichText().parse("a[/b]c")
        self.assertEqual("".join(t for t, _ in spans), "a[/b]c")
        self.assertEqual(malformed, 1)

    def test_mismatched_close_is_literal_and_keeps_open_style(self):
        spans, malformed = RichText().parse("[b]x[/color]y[/b]")
        self.assertEqual("".join(t for t, _ in spans), "x[/color]y")
        self.assertEqual(malformed, 1)
        self.assertTrue(all(s["bold"] for _, s in spans))

    def test_unknown_tag_is_literal_not_malformed(self):
        spans, malformed = RichText().parse("a[foo]b")
        self.assertEqual("".join(t for t, _ in spans), "a[foo]b")
        self.assertEqual(malformed, 0)


class EscapeTest(unittest.TestCase):
    def test_double_bracket_outputs_one_literal_bracket(self):
        spans, malformed = RichText().parse("a[[b]c")
        self.assertEqual("".join(t for t, _ in spans), "a[b]c")
        self.assertEqual(malformed, 0)

    def test_escaped_bracket_is_never_a_tag(self):
        spans, malformed = RichText().parse("[[b]")
        self.assertEqual("".join(t for t, _ in spans), "[b]")
        self.assertEqual(malformed, 0)
        self.assertFalse(any(s["bold"] for _, s in spans))


class NestedStyleTest(unittest.TestCase):
    def test_inner_close_keeps_outer_style(self):
        spans, _ = RichText().parse("[color=ff0000][b]x[/b]y[/color]")
        styles = {t: s for t, s in spans}
        self.assertEqual(styles["x"]["color"], "ff0000")
        self.assertTrue(styles["x"]["bold"])
        self.assertEqual(styles["y"]["color"], "ff0000")
        self.assertFalse(styles["y"]["bold"])

    def test_same_kind_close_pops_nearest_only(self):
        spans, _ = RichText().parse("[b][b]x[/b]y[/b]z")
        styles = {t: s for t, s in spans}
        self.assertTrue(styles["x"]["bold"])
        self.assertTrue(styles["y"]["bold"])
        self.assertFalse(styles["z"]["bold"])


class WrapWidthTest(unittest.TestCase):
    def test_wide_chars_count_two_columns(self):
        lines = RichText().wrap("中文字符测试", 6)
        self.assertEqual(len(lines), 2)
        self.assertEqual([columns(line) for line in lines], [6, 6])

    def test_wide_char_is_never_split(self):
        lines = plain(RichText().wrap("abc中", 4))
        self.assertEqual(lines, ["abc", "中"])

    def test_every_continuation_line_keeps_style(self):
        lines = RichText().wrap("[b]aaaaaaaaaa[/b]", 4)
        self.assertEqual(len(lines), 3)
        self.assertTrue(all(all(s["bold"] for _, s in line) for line in lines))

    def test_leading_space_at_wrap_point_is_dropped(self):
        self.assertEqual(plain(RichText().wrap("abc def", 3)), ["abc", "def"])

    def test_plain_text_is_recoverable_after_wrap(self):
        text = "[b]hello[/b][color=ff0000]world[/color]中文[[x]"
        lines = plain(RichText().wrap(text, 5))
        self.assertEqual("".join(lines), "helloworld中文[x]")

    def test_repeated_parse_and_wrap_are_stable(self):
        text = "[b]ab[/b]中[[c]"
        self.assertEqual(RichText().parse(text), RichText().parse(text))
        self.assertEqual(RichText().wrap(text, 3), RichText().wrap(text, 3))


if __name__ == "__main__":
    unittest.main()
