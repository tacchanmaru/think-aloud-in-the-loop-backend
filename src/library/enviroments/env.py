import os

from dotenv import load_dotenv

from src.library.log.logger import logger

load_dotenv()


def get_env(key: str) -> str:
    var = os.getenv(key)
    if var is None:
        logger.error(f"env variable {key} is not defined")
        exit(1)
    return var
