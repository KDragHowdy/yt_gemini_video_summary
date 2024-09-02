import logging
from logging.handlers import RotatingFileHandler
import os


def setup_logging(log_dir):
    os.makedirs(log_dir, exist_ok=True)
    log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    log_file = os.path.join(log_dir, "mini_video_processor.log")
    log_handler = RotatingFileHandler(
        log_file, maxBytes=51200, backupCount=5
    )  # 51.2 KB per file, keep 5 files
    log_handler.setFormatter(log_formatter)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(log_handler)
    # Add a stream handler for console output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)
    return logger
