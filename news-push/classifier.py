from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from datetime import datetime

from config import SECTION_ORDER, Settings
from models import NewsItem


CATEGORY_KEYWORDS = {
    "international": [
        "美国",
        "欧盟",
        "欧洲",
        "俄罗斯",
        "乌克兰",
        "中东",
        "联合国",
        "外交",
        "贸易谈判",
        "制裁",
        "白宫",
        "地缘",
    ],
    "domestic": ["国务院", "部委", "地方", "民生", "教育", "医疗", "就业", "房地产", "消费券", "政策"],
    "economy": ["经济", "财政", "货币", "央行", "出口", "进口", "制造业", "通胀", "价格", "产业", "投资"],
    "technology": ["科技", "AI", "人工智能", "芯片", "半导体", "大模型", "互联网", "电商", "新能源", "机器人"],
    "culture": ["文化", "旅游", "电影", "演出", "体育", "文旅", "消费场景", "假期", "非遗"],
    "restaurant": ["餐饮", "饭店", "外卖", "烤鱼", "火锅", "食品", "食材", "预制菜", "门店", "客流"],
}

MILITARY_KEYWORDS = [
    "军事",
    "军队",
    "军演",
    "导弹",
    "武器",
    "战机",
    "舰艇",
    "国防",
    "战场",
    "空袭",
]

HIGH_IMPACT_KEYWORDS = [
    "政策",
    "监管",
    "利率",
    "通胀",
    "出口",
    "就业",
    "消费",
    "供应链",
    "AI",
    "芯片",
    "能源",
    "食品",
    "房地产",
]


def _normalized_title(title: str) -> str:
    return re.sub(r"[\W_]+", "", title.lower())


def _fingerprint(item: NewsItem) -> str:
    key = _normalized_title(item.title)
    if not key:
        key = item.url
    return hashlib.sha1(key.encode("utf-8")).hexdigest()


def _contains_any(text: str, keywords: list[str]) -> bool:
    lower = text.lower()
    return any(keyword.lower() in lower for keyword in keywords)


def _classify(item: NewsItem) -> str:
    text = f"{item.title} {item.summary}"
    if item.category_hint in CATEGORY_KEYWORDS:
        hinted = item.category_hint
        if _contains_any(text, CATEGORY_KEYWORDS[hinted]):
            return hinted

    scores = {
        category: sum(1 for keyword in keywords if keyword.lower() in text.lower())
        for category, keywords in CATEGORY_KEYWORDS.items()
    }
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return item.category_hint if item.category_hint in CATEGORY_KEYWORDS else "domestic"
    return best


def _score(item: NewsItem, now: datetime) -> float:
    text = f"{item.title} {item.summary}"
    age_hours = max((now - item.published_at).total_seconds() / 3600, 0.1)
    recency = max(0, 24 - age_hours) / 24
    impact = sum(1 for keyword in HIGH_IMPACT_KEYWORDS if keyword.lower() in text.lower())
    source_bonus = item.reliability
    length_bonus = min(len(item.summary) / 240, 1)
    return source_bonus * 3 + recency * 2 + impact * 0.7 + length_bonus


def _rating(score: float) -> str:
    if score >= 7.0:
        return "S"
    if score >= 5.6:
        return "A"
    if score >= 4.2:
        return "B"
    return "C"


def prepare_news(items: list[NewsItem], settings: Settings, now: datetime) -> dict[str, list[NewsItem]]:
    seen: set[str] = set()
    buckets: dict[str, list[NewsItem]] = defaultdict(list)

    for item in items:
        if settings.military_filter_enabled and _contains_any(f"{item.title} {item.summary}", MILITARY_KEYWORDS):
            continue

        fp = _fingerprint(item)
        if fp in seen:
            continue
        seen.add(fp)

        item.category = _classify(item)
        item.score = _score(item, now)
        item.rating = _rating(item.score)
        buckets[item.category].append(item)

    for category in SECTION_ORDER:
        buckets[category].sort(key=lambda x: (x.score, x.published_at), reverse=True)
        buckets[category] = buckets[category][: settings.items_per_section]

    return {category: buckets.get(category, []) for category in SECTION_ORDER}
