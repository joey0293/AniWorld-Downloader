import curses
import os
import random
import re

from .ascii import display_ascii_art
from .config import GLOBAL_SESSION, logger

SEARCH_URL = "https://aniworld.to/ajax/search"
RANDOM_URL = "https://aniworld.to/ajax/randomGeneratorSeries"


def random_anime():
    """Fetch a random anime series from Aniworld and return its URL."""
    data = {"productionStart": "all", "productionEnd": "all", "genres[]": "all"}

    try:
        response = GLOBAL_SESSION.post(RANDOM_URL, data=data)
        response.raise_for_status()
        result = response.json()

        if not result:
            logger.error("Random anime response is empty")
            return None

        # Pick a random anime from the list
        series = random.choice(result)
        link = series.get("link")
        if link:
            return f"https://aniworld.to/anime/stream/{link}"
        else:
            logger.error("No link found in selected random anime")
            return None

    except Exception as e:
        logger.error(f"Failed to fetch random anime: {e}")
        return None


def query(keyword):
    """Send a search request to Aniworld with given keyword."""
    response = GLOBAL_SESSION.post(SEARCH_URL, data={"keyword": keyword})
    try:
        return response.json()  # Returns a list of dicts
    except ValueError:
        return None


def _curses_menu(stdscr, options):
    """Display a simple curses menu to select an option with scrolling support."""
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)

    selected = 0
    top = 0

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        display_height = h - 2  # leave room for borders

        # Adjust top for scrolling
        if selected < top:
            top = selected
        elif selected >= top + display_height:
            top = selected - display_height + 1

        # Display visible options
        for idx in range(top, min(top + display_height, len(options))):
            option = options[idx]
            title = (
                option.get("title", "Unknown Title")
                .replace("<em>", "")
                .replace("</em>", "")
            )
            title = title[: w - 4]  # clip to width
            y = idx - top + 1
            x = 2
            if idx == selected:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(y, x, title)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(y, x, title)

        stdscr.refresh()
        key = stdscr.getch()

        if key in [curses.KEY_UP, ord("k")]:
            selected = (selected - 1) % len(options)
        elif key in [curses.KEY_DOWN, ord("j")]:
            selected = (selected + 1) % len(options)
        elif key in [curses.KEY_ENTER, ord("\n")]:
            return options[selected]


def search():
    """Prompt user for a search keyword and return a single series URL using a curses menu."""
    display_ascii_art()

    use_random = os.getenv("ANIWORLD_RANDOM_ANIME", "0") == "1"

    if use_random:
        # Get random anime directly
        result = random_anime()
        if result:
            logger.debug(f"Random anime selected: {result}")
            return result
        else:
            logger.error("Failed to get random anime. Please try again.")
            return None

    while True:
        keyword = input("\nSearch for a series: ").strip()
        if not keyword:
            logger.error("No keyword entered, aborting search.")
            return None

        results = query(keyword)

        if not results:
            logger.error("No results found. Please try again.")
            continue

        # Ensure results is always a list
        if isinstance(results, dict):
            results = [results]
        elif isinstance(results, str):
            # random_anime() could return a single URL string
            return results

        logger.debug(results)

        # Precompile regex to match only streaming links
        stream_pattern = re.compile(r"^/anime/stream/[a-zA-Z0-9\-]+/?$", re.IGNORECASE)

        # Filter results
        stream_results = [
            item for item in results if stream_pattern.match(item.get("link") or "")
        ]

        if not stream_results:
            logger.error("No streamable series found. Please try again.")
            continue

        # Auto-select if only one result
        if len(stream_results) == 1:
            selected_item = stream_results[0]
            title = selected_item.get("title") or selected_item.get(
                "name", "Unknown Title"
            )
            logger.debug(f"Auto-selected: {title}")
            return f"https://aniworld.to{selected_item['link']}"

        # Show curses menu if multiple results
        def menu_wrapper(stdscr):
            curses.start_color()
            curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
            selected_item = _curses_menu(stdscr, stream_results)
            return f"https://aniworld.to{selected_item['link']}"

        return curses.wrapper(menu_wrapper)
