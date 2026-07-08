import os
import logging

# ANSI color codes
RESET = "\033[0m"
COLORS = {
    logging.DEBUG: "\033[36m",
    logging.INFO: "\033[32m",
    logging.WARNING: "\033[33m",
    logging.ERROR: "\033[31m",
    logging.CRITICAL: "\033[41m",
}

TIME_COLOR = "\033[35m"  # Magenta
FUNC_COLOR = "\033[34m"  # Blue
MSG_COLOR = "\033[37m"  # White/Gray


class ColorFormatter(logging.Formatter):
    def format(self, record):
        level_color = COLORS.get(record.levelno, RESET)
        record.levelname = f"{level_color}{record.levelname}{RESET}"

        cwd = os.getcwd()
        rel_path = os.path.relpath(record.pathname, cwd)
        record.func_info = (
            f"{FUNC_COLOR}{rel_path}:{record.lineno}:{record.funcName}{RESET}"
        )

        record.msg = f"{MSG_COLOR}{record.getMessage()}{RESET}"

        formatted = super().format(record)

        # Color the timestamp
        parts = formatted.split(" - ", 1)
        if len(parts) == 2:
            timestamp, rest = parts
            formatted = f"{TIME_COLOR}{timestamp}{RESET} - {rest}"

        return formatted


# TODO: I dont like having global variables at all...
_global_logger = None


def get_logger(name=__name__, level=logging.WARNING):
    global _global_logger
    if _global_logger is None:
        _global_logger = logging.getLogger("aniworld")

        log_format = "%(asctime)s - %(levelname)s - %(func_info)s - %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"

        handler = logging.StreamHandler()
        handler.setFormatter(ColorFormatter(log_format, datefmt=date_format))

        _global_logger.addHandler(handler)

        if os.environ.get("ANIWORLD_DEBUG"):
            _global_logger.setLevel(logging.DEBUG)
        else:
            _global_logger.setLevel(level)

        logging.getLogger("urllib3").setLevel(logging.WARNING)

    return _global_logger
