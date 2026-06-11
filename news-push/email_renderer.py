from __future__ import annotations

from html import escape


BODY_STYLE = "margin:0;padding:0;background:#f3f0e8;color:#24231f;font-family:'Microsoft YaHei','PingFang SC','Helvetica Neue',Arial,sans-serif;"
PARAGRAPH_STYLE = "margin:8px 0 12px;font-size:15px;line-height:1.8;color:#34332f;"


def _render_paragraph(text: str) -> str:
    safe_text = escape(text)
    if text.startswith("来源：") and "发布时间：" in text:
        return f'<p style="margin:14px 0 8px;font-size:12px;line-height:1.6;color:#77746c;">{safe_text}</p>'
    if text.startswith("链接："):
        url = text.removeprefix("链接：").strip()
        safe_url = escape(url, quote=True)
        return (
            '<p style="margin:10px 0 14px;font-size:13px;line-height:1.6;">'
            f'<a href="{safe_url}" style="color:#a34428;text-decoration:underline;">查看原文</a>'
            "</p>"
        )
    if text.endswith("："):
        return f'<p style="margin:14px 0 4px;font-size:14px;line-height:1.6;color:#24231f;font-weight:700;">{safe_text}</p>'
    return f'<p style="{PARAGRAPH_STYLE}">{safe_text}</p>'


def render_html_email(title: str, markdown_content: str) -> str:
    """Render the project's predictable Markdown format as inline-CSS HTML."""
    parts: list[str] = []
    paragraph: list[str] = []
    article_open = False
    has_h1 = False

    def flush_paragraph() -> None:
        if paragraph:
            parts.append(_render_paragraph(" ".join(paragraph)))
            paragraph.clear()

    def close_article() -> None:
        nonlocal article_open
        if article_open:
            parts.append("</div>")
            article_open = False

    for raw_line in markdown_content.splitlines():
        line = raw_line.strip()
        if not line:
            flush_paragraph()
            continue
        if line == "---":
            flush_paragraph()
            close_article()
            parts.append('<hr style="border:0;border-top:1px solid #d8d2c5;margin:24px 0;">')
            continue
        if line.startswith("# "):
            flush_paragraph()
            close_article()
            has_h1 = True
            parts.append(
                '<h1 style="margin:0 0 12px;font-size:30px;line-height:1.35;color:#1f2925;font-weight:800;">'
                f"{escape(line[2:])}</h1>"
            )
            continue
        if line.startswith("## "):
            flush_paragraph()
            close_article()
            parts.append(
                '<h2 style="margin:34px 0 16px;padding:10px 14px;border-left:5px solid #b34c2e;'
                'background:#eee8dc;font-size:22px;line-height:1.4;color:#1f2925;font-weight:800;">'
                f"{escape(line[3:])}</h2>"
            )
            continue
        if line.startswith("### "):
            flush_paragraph()
            close_article()
            parts.append('<div style="margin:0;padding:4px 0 2px;">')
            article_open = True
            parts.append(
                '<h3 style="margin:0 0 12px;font-size:18px;line-height:1.55;color:#202823;font-weight:800;">'
                f"{escape(line[4:])}</h3>"
            )
            continue
        paragraph.append(line)

    flush_paragraph()
    close_article()
    if not has_h1:
        parts.insert(
            0,
            '<h1 style="margin:0 0 12px;font-size:30px;line-height:1.35;color:#1f2925;font-weight:800;">'
            f"{escape(title)}</h1>",
        )

    body = "".join(parts)
    return f"""<!doctype html>
<html>
<body style="{BODY_STYLE}">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;background:#f3f0e8;">
  <tr>
    <td align="center" style="padding:24px 12px;">
      <table role="presentation" width="680" cellspacing="0" cellpadding="0" border="0" style="width:100%;max-width:680px;background:#fffdf8;border:1px solid #ddd6c9;">
        <tr>
          <td style="padding:32px 36px;">
            {body}
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
</body>
</html>"""
