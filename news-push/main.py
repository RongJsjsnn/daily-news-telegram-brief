from __future__ import annotations

import argparse
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from classifier import prepare_news
from config import settings
from fetchers import fetch_rss_news
from notifier import get_notifier, send_alert
from scheduler import start_scheduler
from summarizer import render_brief


def setup_logging() -> None:
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[
            logging.FileHandler(settings.log_dir / "news_push.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def run_once() -> str:
    now = datetime.now(ZoneInfo(settings.timezone))
    logging.info("开始生成每日战略新闻简报")
    raw_news = fetch_rss_news(settings, now)
    grouped_news = prepare_news(raw_news, settings, now)
    brief = render_brief(grouped_news, settings, now)
    archive_path = settings.archive_dir / f"{now.strftime('%Y-%m-%d')}.md"
    settings.archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path.write_text(brief, encoding="utf-8")
    logging.info("Markdown 归档已写入 %s", archive_path)
    title = f"【全球战略新闻简报】{now.strftime('%Y-%m-%d')}"
    result = get_notifier(settings).send(title, brief)
    logging.info("推送结果：%s", result)
    logging.info("每日战略新闻简报生成并推送完成")
    return brief


def guarded_run_once() -> None:
    try:
        run_once()
    except Exception as exc:
        logging.exception("新闻推送任务失败")
        send_alert(settings, str(exc))


def main() -> None:
    parser = argparse.ArgumentParser(description="每日自动新闻推送程序")
    parser.add_argument(
        "command",
        choices=("once", "schedule"),
        nargs="?",
        default="schedule",
        help="once 立即运行一次；schedule 启动工作日 08:00 定时任务",
    )
    args = parser.parse_args()

    setup_logging()
    if args.command == "once":
        guarded_run_once()
        return

    start_scheduler(settings, guarded_run_once)


if __name__ == "__main__":
    main()
