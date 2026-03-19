import logging
import os

LOG_FILE = os.path.join(os.path.expanduser("~"), ".cli_anything_mini_crm.log")
_logger = None


def get_logger():
    global _logger
    if _logger:
        return _logger
    _logger = logging.getLogger("mini_crm")
    _logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    _logger.addHandler(fh)
    return _logger


def log(action: str, **kwargs):
    details = " | ".join(f"{k}={v}" for k, v in kwargs.items())
    get_logger().info(f"ACTION={action} | {details}")
