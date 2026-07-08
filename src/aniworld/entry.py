import os
import sys
from pathlib import Path

from .arguments import parse_args
from .config import ACTION_METHODS, ANIWORLD_CONFIG_DIR, VERSION
from .env import merge_env
from .logger import get_logger
from .menu import app
from .providers import resolve_provider
from .search import search

merge_env(
    Path(__file__).resolve().parent / ".env.example",
    ANIWORLD_CONFIG_DIR / ".env",
)

logger = get_logger(__name__)


def set_terminal_title():
    """Set the terminal title if running in a TTY"""
    if sys.stdout.isatty():
        title = f"AniWorld-Downloader v.{VERSION}"
        print(f"\033]0;{title}\007", end="", flush=True)


def validate_action(action: str):
    if action not in ACTION_METHODS.values():
        raise ValueError(f"Invalid action: {action}")


def run_action(obj, action: str):
    validate_action(action)
    getattr(obj, action)()


def aniworld():
    """Main entry point"""
    try:
        logger.debug("Starting...")
        set_terminal_title()

        args = parse_args()

        action = (args.action or "download").lower()

        # ===== no-menu path =====
        if os.getenv("ANIWORLD_NO_MENU") == "1":
            urls = args.url
            logger.debug(urls)

            if not urls:
                raise ValueError("No URLs provided while using --no-menu")

            for url in urls:
                provider = resolve_provider(url)

                if provider.series_pattern and provider.series_pattern.fullmatch(url):
                    obj = provider.series_cls(url=url)

                elif provider.season_pattern and provider.season_pattern.fullmatch(url):
                    obj = provider.season_cls(url=url)

                elif provider.episode_pattern and provider.episode_pattern.fullmatch(
                    url
                ):
                    obj = provider.episode_cls(url=url)

                else:
                    raise ValueError(f"Invalid URL for provider: {url}")

                run_action(obj, action)

            return 0

        # ===== menu path =====
        url = args.url[0] if args.url else search()

        provider = resolve_provider(url)

        # If provider is NOT AniWorld -> bypass menu
        if provider.name != "AniWorld":
            if provider.series_pattern and provider.series_pattern.fullmatch(url):
                obj = provider.series_cls(url=url)

            elif provider.season_pattern and provider.season_pattern.fullmatch(url):
                obj = provider.season_cls(url=url)

            elif provider.episode_pattern and provider.episode_pattern.fullmatch(url):
                obj = provider.episode_cls(url=url)

            else:
                raise ValueError(f"Invalid URL for provider: {url}")

            run_action(obj, action)
            return 0

        # If AniWorld but URL is episode OR season -> bypass menu too
        if provider.episode_pattern.fullmatch(url) or provider.season_pattern.fullmatch(
            url
        ):
            obj = (
                provider.episode_cls(url=url)
                if provider.episode_pattern.fullmatch(url)
                else provider.season_cls(url=url)
            )
            run_action(obj, action)
            return 0

        # AniWorld series -> show menu
        result = app(url=url)
        if not result:
            return 130

        action = result.get("action")
        episodes = result.get("episodes", [])
        selected_path = result.get("path")
        selected_language = result.get("language")
        selected_provider = result.get("provider")

        os.environ["ANIWORLD_USE_ANISKIP"] = "1" if result.get("aniskip") else "0"

        if action in ACTION_METHODS:
            method_name = ACTION_METHODS[action]
            for episode_url in episodes:
                episode = provider.episode_cls(
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
