import os
import sys

from dotenv import load_dotenv

from .arguments import parse_args

# Load environment variables from ~/.aniworld/.env file
from .config import (
    ANIWORLD_CONFIG_DIR,
    ANIWORLD_EPISODE_PATTERN,
    ANIWORLD_SEASON_PATTERN,
    ANIWORLD_SERIES_PATTERN,
    VERSION,
)
from .logger import get_logger
from .menu import app
from .models import AniworldEpisode, AniworldSeason, AniworldSeries
from .search import search

load_dotenv(ANIWORLD_CONFIG_DIR / ".env")


logger = get_logger(__name__)


def set_terminal_title():
    """Set the terminal title if running in a TTY"""
    if sys.stdout.isatty():
        title = f"AniWorld-Downloader v.{VERSION}"
        print(f"\033]0;{title}\007", end="", flush=True)


def aniworld():
    """Main entry point"""
    try:
        logger.debug("Starting...")
        set_terminal_title()

        args = parse_args()

        if os.getenv("ANIWORLD_NO_MENU") == "1":
            urls = args.url
            logger.debug(urls)

            if not urls:
                raise ValueError("No URLs provided while using --no-menu")

            for url in urls:
                # Match URL type
                if ANIWORLD_SERIES_PATTERN.match(url):
                    obj = AniworldSeries(url=url)
                elif ANIWORLD_SEASON_PATTERN.match(url):
                    obj = AniworldSeason(url=url)
                elif ANIWORLD_EPISODE_PATTERN.match(url):
                    obj = AniworldEpisode(url=url)
                else:
                    raise ValueError("Invalid AniWorld URL format")

                # TODO: I don't like this...
                action = args.action.lower() if args.action else "download"
                getattr(obj, action)()

            return 0

        url = args.url[0] if args.url else search()
        result = app(url=url)

        if not result:
            return 130  # user aborted

        # Map action names to methods
        action_methods = {
            "Download": "download",
            "Watch": "watch",
            "Syncplay": "syncplay",
        }

        action = result.get("action")
        episodes = result.get("episodes", [])
        selected_path = result.get("path")
        selected_language = result.get("language")
        selected_provider = result.get("provider")

        os.environ["ANIWORLD_USE_ANISKIP"] = "1" if result.get("aniskip") else "0"

        if action in action_methods:
            method_name = action_methods[action]
            for episode_url in episodes:
                episode = AniworldEpisode(
                    url=episode_url,
                    selected_path=selected_path,
                    selected_language=selected_language,
                    selected_provider=selected_provider,
                )
                getattr(episode, method_name)()

        return 0

    except KeyboardInterrupt:
        print("\nQuitting.", file=sys.stderr)
        return 130

    except Exception as err:
        logger.error("Unexpected error occurred", exc_info=True)
        print(f"\nAn unexpected error occurred: {err}", file=sys.stderr)
        print("Please check the logs for more details.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(aniworld())
