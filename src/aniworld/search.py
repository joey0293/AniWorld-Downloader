import curses

from .ascii import display_ascii_art
from .config import GLOBAL_SESSION

SEARCH_URL = "https://aniworld.to/ajax/search"


def query(keyword):
    """Send a search request to Aniworld with the given keyword."""
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept": "*/*",
        "Sec-Fetch-Site": "same-origin",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Sec-Fetch-Mode": "cors",
        "Origin": "https://aniworld.to",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/26.2 Safari/605.1.15",
        "Referer": "https://aniworld.to/search",
        "Sec-Fetch-Dest": "empty",
        "X-Requested-With": "XMLHttpRequest",
    }
    data = {"keyword": keyword}

    response = GLOBAL_SESSION.post(SEARCH_URL, headers=headers, data=data)
    return response.json()  # Returns a list of dicts


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

    keyword = input("\nSearch for a series: ").strip()
    if not keyword:
        print("No keyword entered, aborting search.")
        return None

    results = query(keyword)
    if not results:
        print("No results found.")
        return None

    # Filter results to only include links containing "/anime/stream/"
    stream_results = [
        item for item in results if "/anime/stream/" in item.get("link", "")
    ]
    if not stream_results:
        print("No streamable series found for that keyword.")
        return None

    def menu_wrapper(stdscr):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
        selected_item = _curses_menu(stdscr, stream_results)
        return f"https://aniworld.to{selected_item['link']}"

    return curses.wrapper(menu_wrapper)
