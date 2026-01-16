import argparse
import logging
import os

from .logger import get_logger

logger = get_logger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(prog="aniworld", description="AniWorld-Downloader")

    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    parser.add_argument(
        "url",
        nargs="?",
        help="Series or Episode URL",
    )

    args = parser.parse_args()

    if args.debug:
        # Set environment variable for debug mode
        os.environ["ANIWORLD_DEBUG"] = "1"

        # Set level on all existing loggers
        logging.getLogger().setLevel(logging.DEBUG)
        for name in logging.Logger.manager.loggerDict:
            logging.getLogger(name).setLevel(logging.DEBUG)

        logger.debug("Debug mode enabled")

    return args
