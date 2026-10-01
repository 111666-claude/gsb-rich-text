# rich-text

UI 富文本：解析行内标签、叠加样式、按列宽折行，只用 Python 标准库。

```
python3 -m richtext.cli --sample unclosed
python3 -m richtext.cli --sample escape
python3 -m richtext.cli --sample nest
python3 -m richtext.cli --sample wrap
python3 -m richtext.cli --sample stylewrap
python3 -m unittest discover -s tests -v
```

## 标签语法

- `[b]` / `[/b]`：加粗。
- `[color=RRGGBB]` / `[/color]`：颜色。
- `[size=N]` / `[/size]`：字号。
- `[[` 表示字面量的 `[`。

## 口径（README 为准）

- **合法标签**：三对标签按栈处理；闭合标签只关闭同类标签里最近的一次，
  外层的其它样式保持不动。
- **畸形标签**：`[` 找不到对应的 `]`、闭合标签没有对应的开标签、
  闭合标签与栈顶不同类，都按字面文本输出并计入 `malformed`，不许吞掉正文。
- **转义**：`[[` 输出一个字面 `[`，不计入标签、不计入畸形。
- **折行按列宽**：ASCII 记 1 列，东亚 Wide/Fullwidth 记 2 列；
  一行列宽不超过 `max_cols`，不许从宽字符中间断开。
- **样式跨行保留**：折出来的每一行都带着折行处的样式，不许在续行丢样式。
- **空行**：行首空白在折行点丢弃。
- **不变量**：`plain(wrap(text))` 拼起来的正文与输入正文逐字符相同（标签与转义除外）；
  同一份输入重复解析、折行结果相同。
- **规模**：10 万字符单遍处理，内存 O(一行 + 一个样式栈)。

## 输出契约（不改格式）

```
visible='..' malformed=..
inner=.. outer=..
lines=.. maxwidth=..
lines=.. styled=..
```

## 目录

```
richtext/core.py   解析、样式栈与折行
richtext/cli.py    命令行入口
tests/             unittest 用例
```
