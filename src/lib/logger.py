import logging
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.lib.env import ENV


def get_log_level(level_name: str) -> int:
    return logging.getLevelNamesMapping()[level_name]


LOG_LEVEL = get_log_level(ENV.get("LOG_LEVEL", "INFO"))
LOG_DIR = Path(ENV.get("LOG_DIR", "./logs"))
TIMEZONE = ZoneInfo(ENV.get("TZ", "UTC"))


def configure_logger(logger: logging.Logger) -> None:
    formatter = logging.Formatter(
        fmt="[%(asctime)s]:%(levelname)s:%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S(%Z)",
    )
    now = datetime.now(TIMEZONE).strftime("%Y-%m-%d_%Hh%Mm%Ss")
    log_file = LOG_DIR / f"{sys.argv[0]}_{now}.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(LOG_LEVEL)
    stream_handler.setFormatter(formatter)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    logging.info("log file is %s", log_file)
    logging.info("log level is %s", LOG_LEVEL)
    logging.info("timezone is %s", TIMEZONE)


def configure_root_logger() -> None:
    root = logging.getLogger()
    configure_logger(root)


class Logger(logging.getLoggerClass()):
    _is_instanced = False

    def __new__(cls) -> logging.Logger:
        logger = logging.getLogger(__name__)
        if not cls._is_instanced:
            cls._is_instanced = True
            configure_logger(logger)
        return logger


LOGGER = Logger()
