from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
from time import mktime
from typing import Any

import feedparser
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import Settings
from models import NewsItem


logger = logging.getLogger(__name__)


def _build_session(settings: Settings) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=settings.request_retries,
        read=settings.request_retries,
        connect=settings.request_retries,
        status=settings.request_retries,
        backoff_factor=settings.retry_backoff_seconds,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    session.mount("http://", HTTPAdapter(max_retries=retry))
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update(
        {
            "User-Agent": "news-push/1.0 (+https://example.local; RSS strategic brief bot)"
        }
    )
    return session


def _parse_datetime(entry: Any) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        parsed = getattr(entry, key, None)
        if parsed:
            return datetime.fromtimestamp(mktime(parsed)).astimezone()

    for key in ("published", "updated", "created"):
        value = getattr(entry, key, None)
        if value:
            try:
                return parsedate_to_datetime(value).astimezone()
            except (TypeError, ValueError, AttributeError):
                continue
    return None


def _clean_text(value: str) -> str:
    text = unescape(value or "")
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(text.replace("\n", " ").split())


def fetch_rss_news(settings: Settings, now: datetime) -> list[NewsItem]:
    session = _build_session(settings)
    cutoff = now - timedelta(hours=settings.lookback_hours)
    items: list[NewsItem] = []

    for feed in settings.rss_feeds:
        name = str(feed.get("name", "unknown"))
        url = str(feed.get("url", ""))
        if not url:
            continue

        try:
            response = session.get(url, timeout=settings.request_timeout)
            response.raise_for_status()
            parsed = feedparser.parse(response.content)
        except Exception as exc:
            logger.warning("抓取 RSS 失败 source=%s url=%s error=%s", name, url, exc)
            continue

        if getattr(parsed, "bozo", False):
            logger.warning("RSS 解析存在异常 source=%s url=%s", name, url)

        for entry in parsed.entries:
            published_at = _parse_datetime(entry)
            if not published_at or published_at < cutoff or published_at > now:
                continue

            title = _clean_text(getattr(entry, "title", ""))
            link = _clean_text(getattr(entry, "link", ""))
            if not title or not link:
                continue

            summary = _clean_text(getattr(entry, "summary", "") or getattr(entry, "description", ""))
            items.append(
                NewsItem(
                    title=title,
                    url=link,
                    source=name,
                    published_at=published_at,
                    summary=summary,
                    category_hint=str(feed.get("category_hint", "")),
                    reliability=float(feed.get("reliability", 0.7)),
                )
            )

    logger.info("RSS 抓取完成，共获得 %s 条候选新闻", len(items))
    return items
