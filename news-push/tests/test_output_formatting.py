from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from email_renderer import render_html_email  # noqa: E402
from notifier import SmtpNotifier  # noqa: E402
from text_utils import to_simplified  # noqa: E402


class OutputFormattingTests(unittest.TestCase):
    def test_traditional_chinese_is_converted(self) -> None:
        converted = to_simplified("國際新聞：臺灣企業發布軟體與網路服務。")

        self.assertEqual(converted, "国际新闻：台湾企业发布软体与网路服务。")

    def test_html_email_has_clear_hierarchy_and_metadata(self) -> None:
        markdown = """# 每日新闻简报

## 国际新闻

### 【A级】测试新闻

来源：测试媒体 | 发布时间：2026-06-11 08:00

新闻概述：
这是一条测试摘要。

链接：https://example.com/news
"""
        html = render_html_email("每日新闻简报", markdown)

        self.assertIn("<h1", html)
        self.assertIn("<h2", html)
        self.assertIn("<h3", html)
        self.assertIn("font-size:12px", html)
        self.assertIn('href="https://example.com/news"', html)
        self.assertNotIn("<style", html)

    def test_html_escapes_untrusted_news_text(self) -> None:
        html = render_html_email("每日新闻简报", "### <script>alert(1)</script>")

        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_smtp_message_contains_plain_text_and_html(self) -> None:
        sent_messages: list[str] = []

        class FakeSmtp:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def starttls(self):
                return None

            def login(self, _user: str, _password: str):
                return None

            def sendmail(self, _sender: str, _recipients: list[str], message: str):
                sent_messages.append(message)

        settings = SimpleNamespace(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="sender@example.com",
            smtp_password="secret",
            smtp_from="sender@example.com",
            smtp_to="reader@example.com",
            smtp_use_ssl=False,
        )
        with patch("notifier.smtplib.SMTP", return_value=FakeSmtp()):
            result = SmtpNotifier(settings).send("國際新聞", "# 國際新聞")

        self.assertEqual(result["status"], "success")
        self.assertEqual(len(sent_messages), 1)
        self.assertIn("multipart/alternative", sent_messages[0])
        self.assertIn("text/plain", sent_messages[0])
        self.assertIn("text/html", sent_messages[0])


if __name__ == "__main__":
    unittest.main()
