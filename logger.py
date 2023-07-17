import logging
from colorlog import ColoredFormatter
from logging.handlers import TimedRotatingFileHandler
logs_file = "logs/app_logs.log"

app_logger = logging.getLogger("app")
app_logger.setLevel(logging.DEBUG)

# ---
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
