import sys

from .arguments import parse_args
from .config import VERSION
from .logger import get_logger
from .menu import app
from .search import search

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
        url = args.url or search()

        app(url=url)
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
