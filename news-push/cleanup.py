from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    return int(value)


OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", str(BASE_DIR / "output")))
LOG_DIR = Path(os.getenv("LOG_DIR", str(BASE_DIR / "logs")))
BRIEF_RETENTION_DAYS = _get_int("CLEANUP_BRIEF_RETENTION_DAYS", 15)
LOG_RETENTION_DAYS = _get_int("CLEANUP_LOG_RETENTION_DAYS", 60)


def setup_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / "cleanup.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def _delete_old_files(directory: Path, patterns: list[str], retention_days: int) -> int:
    if not directory.exists():
        return 0

    cutoff = datetime.now().timestamp() - timedelta(days=retention_days).total_seconds()
    deleted = 0

    for pattern in patterns:
        for path in directory.glob(pattern):
            if not path.is_file():
                continue
            if path.stat().st_mtime >= cutoff:
                continue
            path.unlink()
            deleted += 1
            logging.info("已清理旧文件：%s", path)

    return deleted


def main() -> None:
    setup_logging()
    brief_deleted = _delete_old_files(OUTPUT_DIR, ["*_brief.md"], BRIEF_RETENTION_DAYS)
    log_deleted = _delete_old_files(LOG_DIR, ["*.log"], LOG_RETENTION_DAYS)
    logging.info(
        "清理完成：删除旧简报 %s 个，旧日志 %s 个。简报保留 %s 天，日志保留 %s 天。",
        brief_deleted,
        log_deleted,
        BRIEF_RETENTION_DAYS,
        LOG_RETENTION_DAYS,
    )


if __name__ == "__main__":
    main()
