import logging
import os
import tempfile
from pathlib import Path

_global_logger = None


def get_logger(name=__name__, level=logging.WARNING):
    global _global_logger
    if _global_logger is None:
        _global_logger = logging.getLogger("aniworld")

        # Clear any existing handlers to avoid duplicates
        _global_logger.handlers.clear()

        log_format = "%(asctime)s - %(levelname)s - %(func_info)s - %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"

        # Determine temp log path
        temp_dir = tempfile.gettempdir()
        log_file_path = Path(temp_dir) / "aniworld.log"

        # File handler (overwrite each run)
        handler = logging.FileHandler(log_file_path, mode="w", encoding="utf-8")

        # Optional: keep colors in file (or remove for plain text)
        class PlainFormatter(logging.Formatter):
            def format(self, record):
                cwd = os.getcwd()
                rel_path = os.path.relpath(record.pathname, cwd)
                record.func_info = f"{rel_path}:{record.lineno}:{record.funcName}"
                return super().format(record)

        handler.setFormatter(PlainFormatter(log_format, datefmt=date_format))

        _global_logger.addHandler(handler)
        _global_logger.setLevel(level)

        # Reduce noise from urllib3
        logging.getLogger("urllib3").setLevel(logging.WARNING)

    return _global_logger
