from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


DEFAULT_RSS_FEEDS = [
    {
        "name": "BBC中文",
        "url": "https://feeds.bbci.co.uk/zhongwen/simp/rss.xml",
        "category_hint": "international",
        "reliability": 0.88,
    },
    {
        "name": "央视国内新闻",
        "url": "https://www.cctv.com/program/rss/02/01/index.xml",
        "category_hint": "domestic",
        "reliability": 0.84,
    },
    {
        "name": "央视国际新闻",
        "url": "https://www.cctv.com/program/rss/02/02/index.xml",
        "category_hint": "international",
        "reliability": 0.84,
    },
    {
        "name": "央视财经新闻",
        "url": "https://www.cctv.com/program/rss/02/04/index.xml",
        "category_hint": "economy",
        "reliability": 0.84,
    },
    {
        "name": "央视文娱新闻",
        "url": "https://www.cctv.com/program/rss/02/07/index.xml",
        "category_hint": "culture",
        "reliability": 0.78,
    },
    {
        "name": "36氪",
        "url": "https://36kr.com/feed",
        "category_hint": "technology",
        "reliability": 0.72,
    },
    {
        "name": "财新",
        "url": "https://www.caixin.com/rss/",
        "category_hint": "economy",
        "reliability": 0.84,
    },
    {
        "name": "Google新闻-国际政治",
        "url": "https://news.google.com/rss/search?q=%E5%9B%BD%E9%99%85%E6%94%BF%E6%B2%BB%20OR%20%E4%B8%AD%E7%BE%8E%20OR%20%E6%AC%A7%E7%BE%8E%20when%3A1d&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        "category_hint": "international",
        "reliability": 0.68,
    },
    {
        "name": "Google新闻-国内新闻",
        "url": "https://news.google.com/rss/search?q=%E5%9B%BD%E5%86%85%E6%94%BF%E7%AD%96%20OR%20%E6%B0%91%E7%94%9F%20OR%20%E5%B0%B1%E4%B8%9A%20when%3A1d&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        "category_hint": "domestic",
        "reliability": 0.68,
    },
    {
        "name": "Google新闻-经济",
        "url": "https://news.google.com/rss/search?q=%E4%B8%AD%E5%9B%BD%E7%BB%8F%E6%B5%8E%20OR%20%E5%87%BA%E5%8F%A3%20OR%20%E6%B6%88%E8%B4%B9%20when%3A1d&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        "category_hint": "economy",
        "reliability": 0.68,
    },
    {
        "name": "Google新闻-文化",
        "url": "https://news.google.com/rss/search?q=%E6%96%87%E5%8C%96%20OR%20%E6%96%87%E6%97%85%20OR%20%E7%94%B5%E5%BD%B1%20OR%20%E6%BC%94%E5%87%BA%20when%3A1d&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        "category_hint": "culture",
        "reliability": 0.66,
    },
    {
        "name": "Google新闻-餐饮",
        "url": "https://news.google.com/rss/search?q=%E9%A4%90%E9%A5%AE%20OR%20%E9%A3%9F%E6%9D%90%20OR%20%E5%A4%96%E5%8D%96%20OR%20%E4%B8%87%E5%B7%9E%E7%83%A4%E9%B1%BC%20when%3A1d&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        "category_hint": "restaurant",
        "reliability": 0.66,
    },
]


SECTION_ORDER = [
    "international",
    "domestic",
    "economy",
    "technology",
    "culture",
    "restaurant",
]

SECTION_TITLES = {
    "international": "国际政治板块",
    "domestic": "国内新闻板块",
    "economy": "经济板块",
    "technology": "科技板块",
    "culture": "文化板块",
    "restaurant": "餐饮板块",
}


def _get_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    return int(value)


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if not value:
        return default
    return float(value)


def _get_json(name: str, default: Any) -> Any:
    value = os.getenv(name)
    if not value:
        return default
    return json.loads(value)


@dataclass(frozen=True)
class Settings:
    timezone: str = os.getenv("TIMEZONE", "Asia/Shanghai")
    schedule_hour: int = _get_int("SCHEDULE_HOUR", 8)
    schedule_minute: int = _get_int("SCHEDULE_MINUTE", 0)
    lookback_hours: int = _get_int("LOOKBACK_HOURS", 24)
    items_per_section: int = _get_int("ITEMS_PER_SECTION", 3)
    min_items_per_section: int = _get_int("MIN_ITEMS_PER_SECTION", 2)
    request_timeout: int = _get_int("REQUEST_TIMEOUT", 12)
    request_retries: int = _get_int("REQUEST_RETRIES", 3)
    retry_backoff_seconds: float = _get_float("RETRY_BACKOFF_SECONDS", 1.5)
    notifier: str = os.getenv("NOTIFIER", "smtp").lower()
    output_dir: Path = Path(os.getenv("OUTPUT_DIR", str(BASE_DIR / "output")))
    archive_dir: Path = Path(os.getenv("ARCHIVE_DIR", str(BASE_DIR / "news")))
    log_dir: Path = Path(os.getenv("LOG_DIR", str(BASE_DIR / "logs")))
    military_filter_enabled: bool = _get_bool("MILITARY_FILTER_ENABLED", True)
    rss_feeds: list[dict[str, Any]] = field(
        default_factory=lambda: _get_json("RSS_FEEDS_JSON", DEFAULT_RSS_FEEDS)
    )

    wecom_webhook_url: str = os.getenv("WECOM_WEBHOOK_URL", "")
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("CHAT_ID", "")
    smtp_host: str = os.getenv("SMTP_HOST", "smtp.office365.com")
    smtp_port: int = _get_int("SMTP_PORT", 587)
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_from: str = os.getenv("SMTP_FROM", "")
    smtp_to: str = os.getenv("SMTP_TO", "chenqiusong123@outlook.com")
    smtp_use_ssl: bool = _get_bool("SMTP_USE_SSL", False)


settings = Settings()
