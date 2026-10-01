"""UI 富文本：解析标签、叠加样式、按列宽折行。

缺陷：未闭合的左括号吞掉后续文本、转义不生效、内层标签闭合时把外层样式一起清掉、
折行按字符数而不是列宽、折行后的续行丢样式。
"""

DEFAULT_STYLE = {"bold": False, "color": None, "size": None}


def _fresh(style):
    return {"bold": style["bold"], "color": style["color"], "size": style["size"]}


class RichText:
    """富文本解析与折行。"""

    def __init__(self):
        self.work = 0

    def parse(self, text):
        """返回 (spans, malformed)，spans 是 [(文本, 样式)]。"""
        spans = []
        style = _fresh(DEFAULT_STYLE)
        buf = []
        malformed = 0
        index = 0
        while index < len(text):
            self.work += 1
            ch = text[index]
            if ch == "[":
                end = text.find("]", index)
                if end < 0:
                    break
                if buf:
                    spans.append(("".join(buf), _fresh(style)))
                    buf = []
                inner = text[index + 1:end]
                style = self._apply(inner, style)
                index = end + 1
            else:
                buf.append(ch)
                index += 1
        if buf:
            spans.append(("".join(buf), _fresh(style)))
        return spans, malformed

    def _apply(self, inner, style):
        if inner == "b":
            style = _fresh(style)
            style["bold"] = True
            return style
        if inner == "/b":
            return _fresh(DEFAULT_STYLE)
        if inner.startswith("color="):
            style = _fresh(style)
            style["color"] = inner[6:]
            return style
        if inner == "/color":
            return _fresh(DEFAULT_STYLE)
        if inner.startswith("size="):
            style = _fresh(style)
            style["size"] = int(inner[5:])
            return style
        if inner == "/size":
            return _fresh(DEFAULT_STYLE)
        return style

    def wrap(self, text, max_cols):
        """按列宽折行，返回行列表，每行是 [(文本, 样式)]。"""
        spans, _ = self.parse(text)
        lines = []
        cur = []
        cur_len = 0
        for chunk, style in spans:
            for ch in chunk:
                if cur_len >= max_cols:
                    lines.append(self._merge(cur))
                    cur = []
                    cur_len = 0
                    style = _fresh(DEFAULT_STYLE)
                cur.append((ch, style))
                cur_len += 1
        if cur:
            lines.append(self._merge(cur))
        return lines

    def _merge(self, chars):
        out = []
        for ch, style in chars:
            if out and out[-1][1] == style:
                out[-1] = (out[-1][0] + ch, style)
            else:
                out.append((ch, _fresh(style)))
        return out


def plain(lines):
    """把折行结果拼成纯文本行。"""
    return ["".join(chunk for chunk, _ in line) for line in lines]


def columns(line):
    """一行的列宽（这里按字符数算）。"""
    return sum(len(chunk) for chunk, _ in line)
