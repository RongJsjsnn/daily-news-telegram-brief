from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import settings  # noqa: E402
from main import setup_logging  # noqa: E402
from classifier import prepare_news  # noqa: E402
from fetchers import fetch_rss_news  # noqa: E402
from summarizer import render_brief  # noqa: E402
from notifier import NotificationError, get_notifier  # noqa: E402


def _mask_value(value: str) -> str:
    if not value:
        return ""
    if "@" in value:
        name, domain = value.split("@", 1)
        return f"{name[:2]}***@{domain}"
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:2]}***{value[-2:]}"


def _write_report(report_file: Path, payload: dict) -> None:
    report_file.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Execution Report",
        "",
        f"- generated_at: {payload['generated_at']}",
        f"- timezone: {payload['timezone']}",
        f"- attempt: {payload['attempt']}/{payload['max_attempts']}",
        f"- status: {payload['status']}",
        f"- push_channel: {payload['push_channel']}",
        f"- recipient: {payload['recipient_masked']}",
    ]
    if payload.get("subject"):
        lines.append(f"- subject: {payload['subject']}")
    if payload.get("brief_path"):
        lines.append(f"- brief_path: {payload['brief_path']}")
    if payload.get("archive_path"):
        lines.append(f"- archive_path: {payload['archive_path']}")
    if payload.get("error"):
        lines += ["", "## Error", "", payload["error"]]
    if payload.get("send_result"):
        lines += ["", "## Send Result", "", "```json", json.dumps(payload["send_result"], ensure_ascii=False, indent=2), "```"]
    report_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-file", required=True)
    parser.add_argument("--attempt", type=int, required=True)
    parser.add_argument("--max-attempts", type=int, required=True)
    args = parser.parse_args()

    setup_logging()
    report_path = Path(args.report_file)
    now = datetime.now(ZoneInfo(settings.timezone))
    payload = {
        "generated_at": now.isoformat(),
        "timezone": settings.timezone,
        "attempt": args.attempt,
        "max_attempts": args.max_attempts,
        "status": "failure",
        "push_channel": settings.notifier,
        "recipient_masked": _mask_value(settings.smtp_to or settings.telegram_chat_id or ""),
        "subject": None,
        "brief_path": None,
        "archive_path": None,
        "error": None,
        "send_result": None,
    }

    try:
        logging.info("开始生成每日战略新闻简报")
        raw_news = fetch_rss_news(settings, now)
        grouped_news = prepare_news(raw_news, settings, now)
        brief = render_brief(grouped_news, settings, now)
        settings.output_dir.mkdir(parents=True, exist_ok=True)
        brief_path = settings.output_dir / f"{now.strftime('%Y%m%d_%H%M%S')}_brief.md"
        brief_path.write_text(brief, encoding="utf-8")
        payload["brief_path"] = str(brief_path)
        settings.archive_dir.mkdir(parents=True, exist_ok=True)
        archive_path = settings.archive_dir / f"{now.strftime('%Y-%m-%d')}.md"
        archive_path.write_text(brief, encoding="utf-8")
        payload["archive_path"] = str(archive_path)
        title = f"【全球战略新闻简报】{now.strftime('%Y-%m-%d')}"
        payload["subject"] = title
        result = get_notifier(settings).send(title, brief)
        payload["send_result"] = result
        payload["status"] = "success"
        logging.info("简报内容长度=%d", len(brief))
    except NotificationError as exc:
        payload["error"] = str(exc)
        logging.exception("新闻推送失败")
        _write_report(report_path, payload)
        return 1
    except Exception as exc:
        payload["error"] = str(exc)
        logging.exception("新闻推送失败")
        _write_report(report_path, payload)
        return 1

    _write_report(report_path, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
