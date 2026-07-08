import sys
import logging

from .config import VERSION
from .entry import aniworld


def set_terminal_title() -> None:
    title = f"AniWorld-Downloader v.{VERSION}"
    print(f"\033]0;{title}\007", end="", flush=True)


def main():
    try:
        set_terminal_title()
        aniworld()

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(130)

    except Exception as err:
        logging.error("Unexpected error", exc_info=True)
        print(f"\nAn unexpected error occurred: {err}", file=sys.stderr)
        print("Please check the logs for more details.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
