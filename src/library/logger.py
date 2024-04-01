import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

LOG_LEVEL = logging.INFO
LOG_DIR_PATH = Path("logs")


TOKYO = timezone(timedelta(hours=9))
TIMEZONE = TOKYO


def configure_root_logger() -> None:
    formatter = logging.Formatter(
        fmt="[%(asctime)s]:%(levelname)s:%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S(%Z)",
    )
    now = datetime.now(tz=TIMEZONE).strftime("%Y-%m-%d_%Hh%Mm%Ss")
    log_file = LOG_DIR_PATH / f"{sys.argv[0]}_{now}.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    stream_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(log_file)
    handlers: list[logging.Handler] = [stream_handler, file_handler]
    for handler in handlers:
        handler.setLevel(LOG_LEVEL)
        handler.setFormatter(formatter)
    logging.basicConfig(level=LOG_LEVEL, handlers=handlers)
    logging.info("log file is %s", log_file)


class Logger(logging.getLoggerClass()):
    _is_instanced = False

    def __new__(cls) -> logging.Logger:
        if not cls._is_instanced:
            cls._is_instanced = True
            configure_root_logger()
        return logging.getLogger(__name__)


LOGGER = Logger()
