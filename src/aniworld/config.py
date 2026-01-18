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

SUPPORTED_PROVIDERS = (
    "Filemoon",
    "Vidmoly",
    "VOE",
    "LoadX",
    "Luluvdo",
    "Doodstream",
    "SpeedFiles",
    "Streamtape",
    "Vidoza",
)

RANDOM_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.2 Safari/605.1.15"

LULUVDO_USER_AGENT = (
    "Mozilla/5.0 (Android 15; Mobile; rv:132.0) Gecko/132.0 Firefox/132.0"
)

PROVIDER_HEADERS_D = {
    "Vidmoly": {"Referer": "https://vidmoly.net"},
    "Doodstream": {"Referer": "https://dood.li/"},
    "VOE": {"User-Agent": RANDOM_USER_AGENT},
    "LoadX": {"Accept": "*/*"},
    "Filemoon": {"User-Agent": RANDOM_USER_AGENT, "Referer": "https://filemoon.to"},
    "Luluvdo": {
        "User-Agent": LULUVDO_USER_AGENT,
        "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
        "Origin": "https://luluvdo.com",
        "Referer": "https://luluvdo.com/",
    },
}

PROVIDER_HEADERS_W = {
    "Vidmoly": {"Referer": "https://vidmoly.net"},
    "Doodstream": {"Referer": "https://dood.li/"},
    "VOE": {"User-Agent": RANDOM_USER_AGENT},
    "Luluvdo": {"User-Agent": LULUVDO_USER_AGENT},
    "Filemoon": {"User-Agent": RANDOM_USER_AGENT, "Referer": "https://filemoon.to"},
}
