"""UI 富文本：解析标签、叠加样式、按列宽折行。

标签按栈处理，闭合只关闭同类里最近的一次；畸形标签按字面输出并计入
malformed；``[[`` 转义为字面 ``[``；折行按列宽（ASCII 1 列、东亚宽字符
2 列），样式跨行保留，折行点行首空白丢弃。
"""

import unicodedata

DEFAULT_STYLE = {"bold": False, "color": None, "size": None}

_WIDE = ("W", "F")

_WRAP_WS = " \t"


def _fresh(style):
    return {"bold": style["bold"], "color": style["color"], "size": style["size"]}


def _col_width(ch):
    return 2 if unicodedata.east_asian_width(ch) in _WIDE else 1


def _classify(inner):
    """把方括号内容分类为 ("open"/"close", 类别, 值)，不是合法标签返回 None。"""
    if inner == "b":
        return ("open", "b", True)
    if inner == "/b":
        return ("close", "b", None)
    if inner.startswith("color="):
        return ("open", "color", inner[len("color="):])
    if inner == "/color":
        return ("close", "color", None)
    if inner.startswith("size="):
        try:
            value = int(inner[len("size="):])
        except ValueError:
            return None
        return ("open", "size", value)
    if inner == "/size":
        return ("close", "size", None)
    return None


class RichText:
    """富文本解析与折行。"""

    def __init__(self):
        self.work = 0

    def parse(self, text):
        """返回 (spans, malformed)，spans 是 [(文本, 样式)]。"""
        spans = []
        buf = []
        malformed = 0
        kinds = []
        bold_depth = 0
        colors = []
        sizes = []

        def style_now():
            return {
                "bold": bold_depth > 0,
                "color": colors[-1] if colors else None,
                "size": sizes[-1] if sizes else None,
            }

        def flush():
            if buf:
                spans.append(("".join(buf), style_now()))
                del buf[:]

        index = 0
        end_of = len(text)
        while index < end_of:
            self.work += 1
            ch = text[index]
            if ch != "[":
                buf.append(ch)
                index += 1
                continue
            if index + 1 < end_of and text[index + 1] == "[":
                buf.append("[")
                index += 2
                continue
            close = text.find("]", index + 1)
            if close < 0:
                malformed += 1
                buf.append("[")
                index += 1
                continue
            tag = _classify(text[index + 1:close])
            if tag is None:
                buf.append(text[index:close + 1])
                index = close + 1
                continue
            action, kind, value = tag
            if action == "open":
                flush()
                kinds.append(kind)
                if kind == "b":
                    bold_depth += 1
                elif kind == "color":
                    colors.append(value)
                else:
                    sizes.append(value)
            elif kinds and kinds[-1] == kind:
                flush()
                kinds.pop()
                if kind == "b":
                    bold_depth -= 1
                elif kind == "color":
                    colors.pop()
                else:
                    sizes.pop()
            else:
                malformed += 1
                buf.append(text[index:close + 1])
            index = close + 1
        flush()
        return spans, malformed

    def wrap(self, text, max_cols):
        """按列宽折行，返回行列表，每行是 [(文本, 样式)]。"""
        spans, _ = self.parse(text)
        lines = []
        cur = []
        cur_cols = 0
        drop_ws = False
        for chunk, style in spans:
            for ch in chunk:
                if drop_ws and ch in _WRAP_WS:
                    continue
                drop_ws = False
                width = _col_width(ch)
                if cur and cur_cols + width > max_cols:
                    lines.append(self._merge(cur))
                    cur = []
                    cur_cols = 0
                    if ch in _WRAP_WS:
                        drop_ws = True
                        continue
                cur.append((ch, style))
                cur_cols += width
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
    """一行的列宽（ASCII 1 列，东亚 Wide/Fullwidth 2 列）。"""
    return sum(_col_width(ch) for chunk, _ in line for ch in chunk)
