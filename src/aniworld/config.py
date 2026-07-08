from niquests import Session
from .logger import get_logger

logger = get_logger(__name__)

VERSION = "4.0.0"

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

logger.debug("Config initialized successfully")
