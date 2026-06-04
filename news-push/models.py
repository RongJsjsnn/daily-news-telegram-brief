from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class NewsItem:
    title: str
    url: str
    source: str
    published_at: datetime
    summary: str = ""
    category_hint: str = ""
    reliability: float = 0.7
    category: str = "domestic"
    score: float = 0.0
    rating: str = "B"
