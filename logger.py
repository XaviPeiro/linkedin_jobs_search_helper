from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from colorlog import ColoredFormatter


DEFAULT_LOG_DIR = Path("logs")
QUIET_LOGGERS = ("selenium", "urllib3", "webdriver_manager")

_configured_log_file: Path | None = None


def configure_logging(
    *,
    log_dir: Path = DEFAULT_LOG_DIR,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
) -> Path:
    global _configured_log_file

    if _configured_log_file is not None:
        return _configured_log_file

    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{datetime.now():%Y-%m-%d_%H-%M-%S}.log"

    root_logger = logging.getLogger()
    root_logger.setLevel(min(console_level, file_level))

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(file_level)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)-5.5s] %(name)s:%(lineno)d  %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(
        ColoredFormatter(
            "%(log_color)s%(asctime)s [%(levelname)-5.5s] %(name)s  %(message)s",
            datefmt="%H:%M:%S",
        )
    )

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    for logger_name in QUIET_LOGGERS:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    _configured_log_file = log_file
    return log_file
