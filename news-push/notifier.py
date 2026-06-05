from __future__ import annotations

import logging
import smtplib
import time
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

import requests

from config import Settings


logger = logging.getLogger(__name__)


class NotificationError(RuntimeError):
    pass


class BaseNotifier:
    def send(self, title: str, content: str):
        raise NotImplementedError


class FileNotifier(BaseNotifier):
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir

    def send(self, title: str, content: str):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_brief.md"
        path = self.output_dir / filename
        path.write_text(content, encoding="utf-8")
        logger.info("简报已写入 %s", path)
        return {"kind": "file", "path": str(path)}


class WeComNotifier(BaseNotifier):
    def __init__(self, webhook_url: str):
        if not webhook_url:
            raise NotificationError("缺少 WECOM_WEBHOOK_URL")
        self.webhook_url = webhook_url

    def send(self, title: str, content: str):
        response = requests.post(
            self.webhook_url,
            json={"msgtype": "markdown", "markdown": {"content": content[:3900]}},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("errcode") != 0:
            raise NotificationError(f"企业微信推送失败：{data}")
        return data


class TelegramNotifier(BaseNotifier):
    def __init__(self, bot_token: str, chat_id: str):
        if not bot_token or not chat_id:
            raise NotificationError("缺少 TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID")
        self.url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        self.chat_id = chat_id

    def send(self, title: str, content: str):
        responses = []
        chunks = [content[i : i + 3500] for i in range(0, len(content), 3500)]
        for chunk in chunks:
            response = requests.post(
                self.url,
                json={"chat_id": self.chat_id, "text": chunk},
                timeout=15,
            )
            response.raise_for_status()
            try:
                data = response.json()
            except ValueError as exc:
                raise NotificationError(f"Telegram 返回非 JSON：{response.text[:200]}") from exc
            if not data.get("ok"):
                raise NotificationError(f"Telegram 推送失败：{data}")
            logger.info("Telegram 推送成功：chat_id=%s message_id=%s", self.chat_id, data.get("result", {}).get("message_id"))
            responses.append(data)
        return responses


class SmtpNotifier(BaseNotifier):
    def __init__(self, settings: Settings, max_attempts: int = 3):
        required = [settings.smtp_host, settings.smtp_user, settings.smtp_password, settings.smtp_to]
        if not all(required):
            raise NotificationError("缺少 SMTP_HOST、SMTP_USER、SMTP_PASSWORD 或 SMTP_TO")
        self.settings = settings
        self.max_attempts = max_attempts

    def send(self, title: str, content: str):
        sender = self.settings.smtp_from or self.settings.smtp_user
        message = MIMEText(content, "plain", "utf-8")
        message["Subject"] = title
        message["From"] = sender
        message["To"] = self.settings.smtp_to

        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                if self.settings.smtp_use_ssl:
                    with smtplib.SMTP_SSL(self.settings.smtp_host, self.settings.smtp_port, timeout=30) as server:
                        server.login(self.settings.smtp_user, self.settings.smtp_password)
                        server.sendmail(sender, [self.settings.smtp_to], message.as_string())
                else:
                    with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=30) as server:
                        server.starttls()
                        server.login(self.settings.smtp_user, self.settings.smtp_password)
                        server.sendmail(sender, [self.settings.smtp_to], message.as_string())
                sent_at = datetime.now().isoformat(timespec="seconds")
                logger.info(
                    "邮件发送成功：发送时间=%s 邮件主题=%s 收件人=%s 发送状态=success attempt=%s",
                    sent_at,
                    title,
                    self.settings.smtp_to,
                    attempt,
                )
                return {
                    "kind": "smtp",
                    "sent_at": sent_at,
                    "subject": title,
                    "to": self.settings.smtp_to,
                    "status": "success",
                    "attempt": attempt,
                }
            except Exception as exc:
                last_error = exc
                logger.exception("邮件发送失败：subject=%s to=%s attempt=%s", title, self.settings.smtp_to, attempt)
                if attempt < self.max_attempts:
                    time.sleep(min(2**attempt, 10))

        raise NotificationError(f"邮件发送失败，已重试 {self.max_attempts} 次：{last_error}")


def get_notifier(settings: Settings) -> BaseNotifier:
    if settings.notifier == "wecom":
        return WeComNotifier(settings.wecom_webhook_url)
    if settings.notifier == "telegram":
        return TelegramNotifier(settings.telegram_bot_token, settings.telegram_chat_id)
    if settings.notifier == "smtp":
        return SmtpNotifier(settings)
    if settings.notifier == "file":
        return FileNotifier(settings.output_dir)
    raise NotificationError(f"不支持的 NOTIFIER：{settings.notifier}")


def send_alert(settings: Settings, message: str) -> None:
    try:
        get_notifier(settings).send("新闻推送异常报警", f"新闻推送程序运行异常：\n\n{message}")
    except Exception as exc:
        logger.error("异常报警发送失败：%s", exc)
