import logging
import os

LOG_FILE = os.path.join(os.path.expanduser("~"), ".cli_anything_note_taker.log")
_logger = None


def get_logger() -> logging.Logger:
    global _logger
    if _logger:
        return _logger
    _logger = logging.getLogger("note_taker")
    _logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    _logger.addHandler(fh)
    return _logger


def log(action: str, **kwargs) -> None:
    details = " | ".join(f"{k}={v}" for k, v in kwargs.items())
    get_logger().info(f"ACTION={action} | {details}")
