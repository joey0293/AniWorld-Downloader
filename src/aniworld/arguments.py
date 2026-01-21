import argparse
import logging
import os
import sys

from .config import VERSION
from .logger import get_logger

logger = get_logger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(prog="aniworld", description="AniWorld-Downloader")

    parser.add_argument(
        "--random-anime",
        action="store_true",
        help="<TODO>",
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version and exit",
    )

    parser.add_argument(
        "url",
        nargs="?",
        help="Series or Episode URL",
    )

    args = parser.parse_args()

    if args.random_anime:
        os.environ["ANIWORLD_RANDOM_ANIME"] = "1"

    if args.debug:
        # Set environment variable for debug mode
        os.environ["ANIWORLD_DEBUG"] = "1"

        # Set level on all existing loggers
        logging.getLogger().setLevel(logging.DEBUG)
        for name in logging.Logger.manager.loggerDict:
            logging.getLogger(name).setLevel(logging.DEBUG)

        logger.debug("Debug mode enabled")

    if args.version:
        # TODO: add logic
        is_newest_version = True
        latest_version = VERSION

        version_message = (
            "You are on the latest version."
            if is_newest_version
            else f"Your version is outdated.\nPlease update to the latest version (v.{latest_version})."
        )

        cowsay = Rf"""______________________________
< AniWorld-Downloader v.{VERSION} >
------------------------------
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||

{version_message}"""

        print(cowsay.strip())
        sys.exit(0)

    return args
