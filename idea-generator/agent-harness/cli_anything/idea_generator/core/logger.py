import logging
import os
from datetime import datetime

LOG_FILE = os.path.join(
    os.path.expanduser("~"), ".cli_anything_idea_generator.log"
)

_logger = None


def get_logger() -> logging.Logger:
    global _logger
    if _logger is not None:
        return _logger

    _logger = logging.getLogger("idea_generator")
    _logger.setLevel(logging.DEBUG)

    # File handler — always logs DEBUG+
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    )
    _logger.addHandler(fh)

    return _logger


def log(action: str, **kwargs) -> None:
    logger = get_logger()
    details = " | ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.info(f"ACTION={action} | {details}")
