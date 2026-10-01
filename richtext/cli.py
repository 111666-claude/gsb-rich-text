"""命令行入口：跑富文本样例。"""

import argparse

from .core import RichText, columns, plain


def build_parser():
    parser = argparse.ArgumentParser(prog="rich-text", description="UI 富文本")
    parser.add_argument("--sample", default="nest",
                        help="unclosed / escape / nest / wrap / stylewrap")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.sample == "unclosed":
        spans, malformed = RichText().parse("a[b")
        print("visible=%r malformed=%d" % ("".join(t for t, _ in spans), malformed))
    elif args.sample == "escape":
        spans, malformed = RichText().parse("a[[b]c")
        print("visible=%r malformed=%d" % ("".join(t for t, _ in spans), malformed))
    elif args.sample == "nest":
        spans, _ = RichText().parse("[color=ff0000][b]x[/b]y[/color]")
        inner = next((s["color"] for t, s in spans if t == "x"), None)
        outer = next((s["color"] for t, s in spans if t == "y"), None)
        print("inner=%s outer=%s" % (inner, outer))
    elif args.sample == "wrap":
        lines = RichText().wrap("中文字符测试", 6)
        print("lines=%d maxwidth=%d" % (len(lines), max(columns(line) for line in lines)))
    elif args.sample == "stylewrap":
        lines = RichText().wrap("[b]aaaaaaaaaa[/b]", 4)
        styled = sum(1 for line in lines if all(s["bold"] for _, s in line))
        print("lines=%d styled=%d" % (len(lines), styled))
    else:
        raise SystemExit("需要 --sample unclosed|escape|nest|wrap|stylewrap")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
