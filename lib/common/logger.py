import logging
import os
import sys

def setup_logger(level: str = "INFO", log_dir: str = "logs", quiet: bool = False) -> None:
    """
    Sets up a root logger for the entire project.
    In quiet mode, only file logging is active (no console output).

    :param level: Logging level (e.g., "INFO", "DEBUG", "ERROR").
    :param log_dir: Directory for log files.
    :param quiet: If True, disables console StreamHandler.
    """
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "app.log")

    handlers = [logging.FileHandler(log_file, encoding="utf-8")]
    if not quiet:
        handlers.append(logging.StreamHandler(stream=sys.stderr))

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )

def get_logger(name: str) -> logging.Logger:
    """Returns a configured logger instance."""
    return logging.getLogger(name)
