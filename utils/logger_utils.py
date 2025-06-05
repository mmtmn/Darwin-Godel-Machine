import logging
import threading
import sys
import os

# Thread-local storage for loggers
thread_local = threading.local()

def setup_logger(log_file="./chat_history.md"):
    """
    Initialize a logger for the current thread, writing to log_file.
    """
    logger = logging.getLogger(f"AgentLogger-{threading.get_ident()}")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        # log to file
        fh = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    thread_local.logger = logger
    return logger

def safe_log(message, level=logging.INFO):
    """
    Utility to log safely from any context.
    """
    logger = getattr(thread_local, "logger", None)
    if logger:
        logger.log(level, message)
    else:
        # fallback
        print(message)
