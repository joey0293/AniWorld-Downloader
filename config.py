import logging
from enum import Enum

from niquests import Session

# ANSI color codes
RESET = "\033[0m"
COLORS = {
    logging.DEBUG: "\033[36m",  # Cyan
    logging.INFO: "\033[32m",  # Green
    logging.WARNING: "\033[33m",  # Yellow
    logging.ERROR: "\033[31m",  # Red
    logging.CRITICAL: "\033[41m",  # Red background
}


class ColorFormatter(logging.Formatter):
    def format(self, record):
        color = COLORS.get(record.levelno, RESET)
        record.levelname = f"{color}{record.levelname}{RESET}"
        return super().format(record)


# Configure logging
handler = logging.StreamHandler()
handler.setFormatter(ColorFormatter("%(levelname)s: %(message)s"))

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Silence urllib3
logging.getLogger("urllib3").setLevel(logging.WARNING)


GLOBAL_SESSION = Session(
    resolver=["doh+google://"],
    headers={
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-Dest": "document",
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-Fetch-Mode": "navigate",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/26.2 Safari/605.1.15"
        ),
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://aniworld.to/search",
        "Priority": "u=0, i",
    },
)


class Language(Enum):
    JAPANESE = "Japanese"
    GERMAN = "German"
    ENGLISH = "English"


class TrackType(Enum):
    SUB = "Sub"
    DUB = "Dub"
