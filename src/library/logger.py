import datetime
import logging
from pathlib import Path

now = int(datetime.datetime.now(tz=datetime.UTC).timestamp())

LOG_LEVEL = logging.INFO
LOG_DIR_PATH = "logs"

if not Path(LOG_DIR_PATH).exists():
    Path(LOG_DIR_PATH).mkdir(parents=True, exist_ok=True)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(LOG_LEVEL)
stream_handler.setFormatter(
    logging.Formatter("[%(asctime)s]:%(levelname)s:%(message)s"),
)

LOG_FILE = f"{LOG_DIR_PATH}/{now}.log"


file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(LOG_LEVEL)
file_handler.setFormatter(logging.Formatter("[%(asctime)s]:%(levelname)s:%(message)s"))

logging.basicConfig(level=logging.INFO, handlers=[stream_handler, file_handler])
logger = logging.getLogger(__name__)

logger.info("log file is %s.log", f"{LOG_DIR_PATH}/{now}")
