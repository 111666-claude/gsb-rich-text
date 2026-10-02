"""UI 富文本：解析标签、样式栈与按列宽折行。

标签：[b]/[/b]、[color=RRGGBB]/[/color]、[size=N]/[/size]；[[ 为字面 [。
合法开标签入栈，闭合标签只在与栈顶同类时弹出它；其余 [..] 一律按字面
输出并计入 malformed。折行按显示列宽（Wide/Fullwidth 记 2 列），样式随
字符保留到续行，折行点行首空白丢弃。
"""

import unicodedata

DEFAULT_STYLE = {"bold": False, "color": None, "size": None}

_HEX = set("0123456789abcdefABCDEF")


def _fresh(style):
    return {"bold": style["bold"], "color": style["color"], "size": style["size"]}


def char_cols(ch):
    """一个字符的显示列宽：东亚 Wide/Fullwidth 记 2 列，其余记 1 列。"""
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


class RichText:
    """富文本解析与折行。"""

    def __init__(self):
        self.work = 0

    def _scan(self, text, emit):
        """单遍扫描 text，每识别出一段正文就调用 emit(文本, 样式)。

        返回畸形标签计数。样式状态是一个开标签栈加每类标签的辅助栈，
        开/合法闭都是 O(1)；扫描指针只前进，不回退。
        """
        stack = []
        bold_depth = 0
        colors = []
        sizes = []

        def active():
            return {
                "bold": bold_depth > 0,
                "color": colors[-1] if colors else None,
                "size": sizes[-1] if sizes else None,
            }

        buf = []
        cur_style = active()
        malformed = 0

        def flush():
            if buf:
                emit("".join(buf), cur_style)
                buf.clear()

        def change_style():
            nonlocal cur_style
            flush()
            cur_style = active()

        def push(kind, value=None):
            nonlocal bold_depth
            stack.append(kind)
            if kind == "b":
                bold_depth += 1
            elif kind == "color":
                colors.append(value)
            else:
                sizes.append(value)

        def pop_top():
            nonlocal bold_depth
            kind = stack.pop()
            if kind == "b":
                bold_depth -= 1
            elif kind == "color":
                colors.pop()
            else:
                sizes.pop()

        index = 0
        length = len(text)
        while index < length:
            self.work += 1
            ch = text[index]
            if ch != "[":
                buf.append(ch)
                index += 1
                continue

            # [[ -> 一个字面 [，不是标签也不是畸形。
            if index + 1 < length and text[index + 1] == "[":
                buf.append("[")
                index += 2
                continue

            end = text.find("]", index + 1)
            if end < 0:
                # 找不到右方括号：这个 [ 按字面输出，继续扫描后面的正文。
                buf.append("[")
                malformed += 1
                index += 1
                continue

            tag = self._parse_tag(text[index + 1:end])
            if tag is None:
                # 不认识的标签形态：整段按字面输出。
                buf.append(text[index:end + 1])
                malformed += 1
                index = end + 1
                continue

            mode, kind = tag[0], tag[1]
            if mode == "open":
                flush()
                push(kind, tag[2] if len(tag) > 2 else None)
                change_style()
            elif stack and stack[-1] == kind:
                # 与栈顶同类：只关闭最近这一次，外层样式保持不动。
                flush()
                pop_top()
                change_style()
            else:
                # 没有开标签，或闭合标签与栈顶不同类：按字面输出。
                buf.append(text[index:end + 1])
                malformed += 1
            index = end + 1

        flush()
        return malformed

    @staticmethod
    def _parse_tag(inner):
        if inner == "b":
            return ("open", "b")
        if inner == "/b":
            return ("close", "b")
        if inner == "/color":
            return ("close", "color")
        if inner == "/size":
            return ("close", "size")
        if inner.startswith("color="):
            value = inner[len("color="):]
            if len(value) == 6 and all(c in _HEX for c in value):
                return ("open", "color", value)
        elif inner.startswith("size="):
            value = inner[len("size="):]
            if value.isdigit():
                return ("open", "size", int(value))
        return None

    def parse(self, text):
        """返回 (spans, malformed)，spans 是 [(文本, 样式)]。"""
        spans = []
        malformed = self._scan(text, lambda chunk, style: spans.append((chunk, style)))
        return spans, malformed

    def wrap(self, text, max_cols):
        """按列宽折行，返回行列表，每行是 [(文本, 样式)]。"""
        lines = []
        cur = []
        width = 0
        started = False

        def add(ch, style):
            nonlocal width, started
            cols = char_cols(ch)
            if width > 0 and width + cols > max_cols:
                lines.append(self._merge(cur))
                cur.clear()
                width = 0
                started = True
            # 折行点行首空白丢弃；宽字符放不下也整字挪到下一行，不从中间断开。
            if width == 0 and started and ch.isspace():
                return
            cur.append((ch, style))
            width += cols

        def emit(chunk, style):
            for ch in chunk:
                add(ch, style)

        self._scan(text, emit)
        if cur:
            lines.append(self._merge(cur))
        return lines

    def _merge(self, chars):
        out = []
        for ch, style in chars:
            if out and out[-1][1] == style:
                out[-1][0] += ch
            else:
                out.append([ch, _fresh(style)])
        return [(text, style) for text, style in out]


def plain(lines):
    """把折行结果拼成纯文本行。"""
    return ["".join(chunk for chunk, _ in line) for line in lines]


def columns(line):
    """一行的显示列宽（ASCII 记 1，东亚 Wide/Fullwidth 记 2）。"""
    return sum(char_cols(ch) for chunk, _ in line for ch in chunk)
