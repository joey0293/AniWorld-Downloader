import curses
import json
import os
import sys
from enum import Enum
from pathlib import Path

import npyscreen

from .config import SUPPORTED_PROVIDERS, VERSION, logger
from .models.aniworld_to.episode import LANG_KEY_MAP

# TODO: use urls from AniworldSeries object instead
urls = tuple(
    f"https://aniworld.to/anime/stream/highschool-dxd/staffel-1/episode-{i}"
    for i in range(1, 13)
)


# ============================================================
# Patch: Fix for Python 3.14+ buffer overflow in npyscreen
# ============================================================
if sys.version_info >= (3, 14):
    import npyscreen.proto_fm_screen_area as _npyscreen_area

    def _patched_max_physical(self):
        try:
            return (curses.LINES - 1, curses.COLS - 1)
        except Exception:
            size = os.get_terminal_size(fallback=(80, 24))
            return (size.lines - 1, size.columns - 1)

    _npyscreen_area.ScreenArea._max_physical = _patched_max_physical


# ============================================================
# Theme
# ============================================================
class CustomTheme(npyscreen.ThemeManager):
    """Color reference: https://npyscreen.readthedocs.io/color.html"""

    default_colors = {
        "DEFAULT": "WHITE_BLACK",
        "FORMDEFAULT": "MAGENTA_BLACK",  # WHITE_BLACK
        "NO_EDIT": "BLUE_BLACK",
        "STANDOUT": "CYAN_BLACK",
        "CURSOR": "WHITE_BLACK",
        "CURSOR_INVERSE": "BLACK_WHITE",
        "LABEL": "CYAN_BLACK",  # GREEN_BLACK
        "LABELBOLD": "CYAN_BLACK",  # WHITE_BLACK
        "CONTROL": "GREEN_BLACK",  # YELLOW_BLACK
        "IMPORTANT": "GREEN_BLACK",
        "SAFE": "GREEN_BLACK",
        "WARNING": "YELLOW_BLACK",
        "DANGER": "RED_BLACK",
        "CRITICAL": "BLACK_RED",
        "GOOD": "GREEN_BLACK",
        "GOODHL": "GREEN_BLACK",
        "VERYGOOD": "BLACK_GREEN",
        "CAUTION": "YELLOW_BLACK",
        "CAUTIONHL": "BLACK_YELLOW",
    }


# ============================================================
# Base Form with Quit Handlers
# ============================================================
class QuitForm(npyscreen.Form):
    def set_up_handlers(self):
        super().set_up_handlers()

        # Quit on Ctrl‑C
        self.add_handlers(
            {
                curses.ascii.ETX: self.exit_editing,
            }
        )

        # Quit on 'q'
        self.add_handlers(
            {
                ord("q"): self.exit_editing,
            }
        )


# ============================================================
#
# ============================================================
class Action(Enum):
    """
    asd
    """

    DOWNLOAD = "Download"
    WATCH = "Watch"
    SYNCPLAY = "Syncplay"


# ============================================================
# Application
# ============================================================
class MenuApp(npyscreen.NPSApp):
    def main(self):
        npyscreen.setTheme(CustomTheme)

        F = QuitForm(name=f"AniWorld-Downloader v.{VERSION}")

        # Track vertical position
        y = 2  # leave space for form title

        # --- Action ---
        action_height = 4
        action = F.add(
            npyscreen.TitleSelectOne,
            name="Action",
            values=[Action.DOWNLOAD.value, Action.WATCH.value, Action.SYNCPLAY.value],
            value=[0],
            max_height=action_height,
            rely=y,
            scroll_exit=True,
        )
        y += action_height

        # --- Path ---
        path_height = 2
        path = F.add(
            npyscreen.TitleFilenameCombo,
            name="Path",
            value=Path.home() / "Downloads",
            rely=y,
            max_height=path_height,
        )
        y += path_height

        # --- Language ---
        language_height = len(LANG_KEY_MAP) + 1
        language = F.add(
            npyscreen.TitleSelectOne,
            name="Language",
            values=list(("German Dub", "English Sub", "German Sub")),
            value=[0],
            max_height=language_height,
            rely=y,
            scroll_exit=True,
        )
        y += language_height

        # --- Provider ---
        provider_height = len(SUPPORTED_PROVIDERS) + 1
        provider = F.add(
            npyscreen.TitleSelectOne,
            name="Provider",
            values=list(SUPPORTED_PROVIDERS),
            value=[0],
            max_height=provider_height,
            rely=y,
            scroll_exit=True,
        )
        y += provider_height

        # --- Episodes ---
        term_height = curses.LINES
        remaining_height = term_height - y - 2
        min_episode_height = 4
        episode_height = max(min_episode_height, remaining_height)

        episodes = F.add(
            npyscreen.TitleMultiSelect,
            name="Episodes",
            values=list(urls),
            rely=y,
            max_height=episode_height,
            scroll_exit=True,
        )

        # --- Edit the form ---
        F.edit()

        # --- After editing, get all selected values ---
        selected_action = (
            action.get_selected_objects()[0] if action.get_selected_objects() else None
        )
        selected_path = path.value
        selected_language = (
            language.get_selected_objects()[0]
            if language.get_selected_objects()
            else None
        )
        selected_provider = (
            provider.get_selected_objects()[0]
            if provider.get_selected_objects()
            else None
        )
        selected_episodes = (
            [episodes.values[i] for i in episodes.value] if episodes.value else []
        )

        # --- Return and print ---
        self.result = {
            "action": selected_action,
            "path": selected_path,
            "language": selected_language,
            "provider": selected_provider,
            "episodes": selected_episodes,
        }


# ============================================================
# Entry Point
# ============================================================
def app():
    app_instance = MenuApp()
    app_instance.run()

    # Prepare a copy of result for logging, convert Path to string
    log_result = dict(app_instance.result)
    if isinstance(log_result.get("path"), Path):
        log_result["path"] = str(log_result["path"])

    # Log JSON with leading newline
    logger.debug("Menu Selection Output\n" + json.dumps(log_result, indent=4))


if __name__ == "__main__":
    app()
