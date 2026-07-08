import os
import platform
from enum import Enum

from niquests import Session

from .autodeps import DependencyManager
from .logger import get_logger

logger = get_logger(__name__)

VERSION = "4.0.0"

NAMING_TEMPLATE = os.getenv(
    "ANIWORLD_NAMING_TEMPLATE",
    "{title} ({year}) [imdbid-{imdbid}]/Season {season}/{title} S{season}E{episode}.mkv",
)

# NIQUESTS

DEFAULT_USER_AGENT = "Mozilla/5.0 (iPhone16,2; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Resorts/4.7.5"

LULUVDO_USER_AGENT = (
    "Mozilla/5.0 (Android 15; Mobile; rv:132.0) Gecko/132.0 Firefox/132.0"
)

GLOBAL_SESSION = Session(
    resolver=["doh+google://"],
    headers={
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-Dest": "document",
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-Fetch-Mode": "navigate",
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://aniworld.to/search",
        "Priority": "u=0, i",
    },
)

logger.debug("Config initialized successfully")

# -----------------------------
# Provider Stuff
# -----------------------------
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

PROVIDER_HEADERS_D = {
    "Vidmoly": {"Referer": "https://vidmoly.net"},
    "Doodstream": {"Referer": "https://dood.li/"},
    "VOE": {"User-Agent": DEFAULT_USER_AGENT},
    "LoadX": {"Accept": "*/*"},
    "Filemoon": {"User-Agent": DEFAULT_USER_AGENT, "Referer": "https://filemoon.to"},
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
    "VOE": {"User-Agent": DEFAULT_USER_AGENT},
    "Luluvdo": {"User-Agent": LULUVDO_USER_AGENT},
    "Filemoon": {"User-Agent": DEFAULT_USER_AGENT, "Referer": "https://filemoon.to"},
}


# -----------------------------
# Language Stuff
# -----------------------------
class Audio(Enum):
    """
    Available audio language options:

        - JAPANESE: Japanese dubbed audio
        - GERMAN:   German dubbed audio
        - ENGLISH:  English dubbed audio

    Required source for each option:

        Japanese Dub -> Source: German Sub, English Sub
        German Dub   -> Source: German Dub
        English Dub  -> Source: English Dub
    """

    JAPANESE = "Japanese"
    GERMAN = "German"
    ENGLISH = "English"


class Subtitles(Enum):
    """
    Available subtitle language options:

        - NONE:    No subtitles
        - GERMAN:  German subtitles
        - ENGLISH: English subtitles

    Required source for each option:

        German Sub   -> Source: German Sub
        English Sub  -> Source: English Sub
    """

    NONE = "None"
    GERMAN = "German"
    ENGLISH = "English"


# Map site-specific language keys to semantic meaning
LANG_KEY_MAP = {
    "1": (Audio.GERMAN, Subtitles.NONE),  # German Dub
    "2": (Audio.JAPANESE, Subtitles.ENGLISH),  # English Sub
    "3": (Audio.JAPANESE, Subtitles.GERMAN),  # German Sub
}

LANG_LABELS = {
    "1": "German Dub",
    "2": "English Sub",
    "3": "German Sub",
}

INVERSE_LANG_KEY_MAP = {v: k for k, v in LANG_KEY_MAP.items()}

# -----------------------------
# Executables
# -----------------------------

# TODO: add function to fetch latest url
deps = {
    "mpv": {
        "Windows": {
            "package": "mpv.net",
            "url": "<>",
        },
        "Linux": {
            "package": "mpv",
            "url": "<>",
        },
        "Darwin": {
            "package": "mpv",  # TODO: check env var if iina wanted instead in DependencyManager
            "url": "<>",
        },
    },
    "syncplay": {
        "Windows": {
            "package": "Syncplay.Syncplay",
            "url": "<>",
        },
        "Linux": {
            "package": "syncplay",
            "url": "<>",
        },
        "Darwin": {
            "package": "syncplay",
            "url": "<>",
        },
    },
    "iina": {
        "Darwin": {
            "package": "iina",
            "url": "<>",
        },
    },
}


def get_player_path():
    deps_manager = DependencyManager(deps=deps)

    use_iina = os.getenv("ANIWORLD_USE_IINA") == "1"

    if platform.system() == "Darwin" and use_iina:
        return deps_manager.fetch_binary("iina")

    return deps_manager.fetch_binary("mpv")


def get_syncplay_path():
    deps_manager = DependencyManager(deps=deps)
    return deps_manager.fetch_binary("syncplay")
