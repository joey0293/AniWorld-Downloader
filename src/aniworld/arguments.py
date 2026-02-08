import argparse
import logging
import os
import sys

from .anime4k import anime4k
from .config import ACTION_METHODS, LANG_LABELS, SUPPORTED_PROVIDERS, VERSION
from .logger import get_logger

logger = get_logger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(
        prog="aniworld",
        description=(
            "AniWorld Downloader is a cross-platform tool for streaming and "
            "downloading anime from aniworld.to, as well as movies and series "
            "from s.to. It runs on Windows, macOS, and Linux, providing a "
            "seamless experience for offline viewing or instant playback."
        ),
    )

    parser.add_argument(
        "--action",
        choices=sorted(ACTION_METHODS.keys()),
        help="Choose action method",
    )

    parser.add_argument(
        "--language",
        choices=sorted(LANG_LABELS.values()),
        help="Choose language",
    )

    parser.add_argument(
        "--provider",
        choices=sorted(SUPPORTED_PROVIDERS),
        help="Choose provider",
    )

    parser.add_argument(
        "--random-anime",
        action="store_true",
        help="Fetch a random anime series",
    )

    parser.add_argument(
        "--anime4k",
        choices=["High", "Low", "Remove"],
        help="Enable Anime4K upscaling with specified mode",
    )

    parser.add_argument(
        "--episode-file",
        help="Path to a text file containing episode URLs (one URL per line)",
    )

    parser.add_argument(
        "--provider-url",
        help="Custom provider URL",
    )

    parser.add_argument(
        "--no-menu",
        action="store_true",
        help="Disable interactive menu",
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information and exit",
    )

    parser.add_argument(
        "url",
        nargs="*",
        help="URLs of series, season, or episodes",
    )

    args = parser.parse_args()

    if args.language:
        os.environ["ANIWORLD_LANGUAGE"] = args.language

    if args.provider:
        os.environ["ANIWORLD_PROVIDER"] = args.provider

    if args.random_anime:
        os.environ["ANIWORLD_RANDOM_ANIME"] = "1"

    if args.no_menu:
        os.environ["ANIWORLD_NO_MENU"] = "1"

    if args.anime4k:
        mode = args.anime4k.lower()
        logger.debug(f"Anime4K upscaling set to: {mode}")
        anime4k(mode)

    if args.debug:
        # Set environment variable for debug mode
        os.environ["ANIWORLD_DEBUG_MODE"] = "1"

        # Set level on all existing loggers
        logging.getLogger().setLevel(logging.DEBUG)
        for name in logging.Logger.manager.loggerDict:
            logging.getLogger(name).setLevel(logging.DEBUG)

        logger.debug("Debug mode enabled")

    if args.episode_file:
        try:
            with open(args.episode_file, "r") as f:
                for line in f:
                    url = line.strip()
                    if url:
                        args.url.append(url)
            logger.debug(f"Loaded {len(args.url)} URLs from {args.episode_file}")
        except Exception as e:
            logger.error(f"Failed to read episode file: {e}")
            sys.exit(1)

    if args.provider_url and args.provider:
        import ffmpeg

        from .config import PROVIDER_HEADERS_D
        from .extractors import provider_functions

        provider_key = (args.provider or "").strip()
        headers = PROVIDER_HEADERS_D.get(provider_key, {})

        # ffmpeg expects headers as a single string with CRLF line endings
        headers_str = "".join(f"{k}: {v}\r\n" for k, v in headers.items())

        # Resolve the provider page URL to a direct media URL
        direct_link = provider_functions[
            f"get_direct_link_from_{provider_key.lower()}"
        ](args.provider_url)

        download_dir = os.getenv("ANIWORLD_DOWNLOAD_PATH", ".")
        output_path = os.path.join(download_dir, "input.mkv")

        (
            ffmpeg.input(
                direct_link,
                headers=headers_str if headers_str else None,
            )
            .output(
                output_path,
                c="copy",  # stream copy (no re-encode)
                f="matroska",  # optional; inferred from .mkv
            )
            .run()
        )

        sys.exit(0)

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
