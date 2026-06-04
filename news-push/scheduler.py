from __future__ import annotations

import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from config import Settings


logger = logging.getLogger(__name__)


def start_scheduler(settings: Settings, job) -> None:
    scheduler = BlockingScheduler(timezone=settings.timezone)
    trigger = CronTrigger(
        day_of_week="mon-fri",
        hour=settings.schedule_hour,
        minute=settings.schedule_minute,
        timezone=settings.timezone,
    )
    scheduler.add_job(
        job,
        trigger=trigger,
        id="daily_news_brief",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=1800,
    )
    logger.info(
        "定时任务已启动：工作日 %02d:%02d，时区 %s",
        settings.schedule_hour,
        settings.schedule_minute,
        settings.timezone,
    )
    scheduler.start()
