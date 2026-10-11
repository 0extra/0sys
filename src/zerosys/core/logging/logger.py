from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from platformdirs import user_log_dir

ROOT_LOGGER_NAME = "zerosys"
DEFAULT_LOG_DIR = Path(user_log_dir("0sys", "0extra"))
DEFAULT_LOG_FILE = DEFAULT_LOG_DIR / "0sys.log"
DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_MAX_BYTES = 1_000_000
DEFAULT_BACKUP_COUNT = 3


def get_logger(name: str | None = None) -> logging.Logger:
    if name is None or name == ROOT_LOGGER_NAME:
        return logging.getLogger(ROOT_LOGGER_NAME)
    return logging.getLogger(f"{ROOT_LOGGER_NAME}.{name}")


def configure_logging(
    level: int = logging.INFO,
    log_file: Path | None = None,
    console: bool = False,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
) -> logging.Logger:
    logger = logging.getLogger(ROOT_LOGGER_NAME)
    logger.setLevel(level)
    logger.handlers.clear()
    logger.propagate = False

    formatter = logging.Formatter(DEFAULT_LOG_FORMAT, datefmt=DEFAULT_DATE_FORMAT)

    target = log_file or DEFAULT_LOG_FILE
    target.parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        target,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    logger.addHandler(file_handler)

    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        logger.addHandler(console_handler)

    return logger


def disable_logging() -> None:
    logger = logging.getLogger(ROOT_LOGGER_NAME)
    logger.handlers.clear()
    logger.addHandler(logging.NullHandler())


def set_level(level: int) -> None:
    logger = logging.getLogger(ROOT_LOGGER_NAME)
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)


def current_level() -> int:
    return logging.getLogger(ROOT_LOGGER_NAME).level


def log_file_path() -> Path:
    return DEFAULT_LOG_FILE
