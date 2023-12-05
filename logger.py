import logging
import os
import sys
from datetime import date

from colorlog import ColoredFormatter
from logging.handlers import TimedRotatingFileHandler
logs_file = "logs/app_logs.log"

app_logger = logging.getLogger("app")
app_logger.setLevel(logging.DEBUG)

# --- General logger
# TODO: Maybe change the file handler to per execution.
file_handler = TimedRotatingFileHandler(logs_file, when="D", interval=1)
log_formatter = logging.Formatter(
    "%(asctime)s [%(threadName)s] [%(levelname)-5.5s]  %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(log_formatter)
app_logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
log_formatter = ColoredFormatter(
    "%(log_color)s%(asctime)s [%(threadName)s] [%(levelname)-5.5s]  %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S'
)
console_handler.setFormatter(log_formatter)
app_logger.addHandler(console_handler)


# --
logs_jobs_folder = "./logs_jobs"

# --- Easy to apply logger
# TODO: var(date) replacement should not be here, but where it is used
easy_to_apply_file = os.path.join(logs_jobs_folder, f"jobs-easy-to-apply-{date.today()}.log")

easy_to_apply_logger = logging.getLogger("easy-to-apply")
easy_to_apply_logger.setLevel(logging.DEBUG)

easy_to_apply_file_handler = TimedRotatingFileHandler(easy_to_apply_file, when='D', interval=1)
easy_to_apply_log_formatter = logging.Formatter(
    "%(message)s",
    datefmt='%Y-%m-%d %H:%M:%S'
)
easy_to_apply_file_handler.setFormatter(easy_to_apply_log_formatter)
easy_to_apply_logger.addHandler(easy_to_apply_file_handler)
easy_to_apply_logger.propagate = False

# --- To apply job handler logger
# TODO: var(date) replacement should not be here, but where it is used
jobs_to_apply_file = os.path.join(logs_jobs_folder, f"jobs-to-apply-{date.today()}.log")
jobs_to_apply_logger = logging.getLogger("jobs-to-apply")
jobs_to_apply_logger.setLevel(logging.DEBUG)

jobs_to_apply_file_handler = TimedRotatingFileHandler(jobs_to_apply_file, when='D', interval=1)
jobs_to_apply_log_formatter = logging.Formatter(
    "%(message)s",
    datefmt='%Y-%m-%d %H:%M:%S'
)
jobs_to_apply_file_handler.setFormatter(jobs_to_apply_log_formatter)
jobs_to_apply_logger.addHandler(jobs_to_apply_file_handler)
jobs_to_apply_logger.propagate = False

