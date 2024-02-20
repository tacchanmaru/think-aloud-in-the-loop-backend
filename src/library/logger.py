from datetime import datetime, timedelta, timezone
from logging import INFO, FileHandler, Formatter, Handler, StreamHandler, basicConfig, getLogger
from pathlib import Path

LOG_LEVEL = INFO
LOG_DIR_PATH = Path("logs")

FORMATTER = Formatter(
    fmt="[%(asctime)s]:%(levelname)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S(%Z)",
)

TOKYO = timezone(timedelta(hours=9))
TIMEZONE = TOKYO

now = datetime.now(tz=TIMEZONE).strftime("%Y-%m-%d_%Hh%Mm%Ss")
log_file = LOG_DIR_PATH / f"{now}.log"
LOG_DIR_PATH.mkdir(parents=True, exist_ok=True)

stream_handler = StreamHandler()
file_handler = FileHandler(log_file)
handlers: list[Handler] = [stream_handler, file_handler]
for handler in handlers:
    handler.setLevel(LOG_LEVEL)
    handler.setFormatter(FORMATTER)

basicConfig(level=LOG_LEVEL, handlers=handlers)
logger = getLogger(__name__)

logger.info("log file is %s", log_file)
