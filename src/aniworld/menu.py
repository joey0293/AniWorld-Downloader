import curses
import json
import os
import sys
from enum import Enum
from pathlib import Path

import npyscreen

from .config import INVERSE_LANG_KEY_MAP, LANG_LABELS, VERSION, logger
from .models import AniworldEpisode, AniworldSeries

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
        "FORMDEFAULT": "MAGENTA_BLACK",
        "NO_EDIT": "BLUE_BLACK",
        "STANDOUT": "CYAN_BLACK",
        "CURSOR": "WHITE_BLACK",
        "CURSOR_INVERSE": "BLACK_WHITE",
        "LABEL": "CYAN_BLACK",
        "LABELBOLD": "CYAN_BLACK",
        "CONTROL": "GREEN_BLACK",
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
        self.add_handlers({curses.ascii.ETX: self.exit_editing})
        self.add_handlers({ord("q"): self.exit_editing})


# ============================================================
class Action(Enum):
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

        # ============================================================
        # Get Values for series
        # ============================================================

        # Load series
        series = AniworldSeries(self.url)

        languages = []
        providers = []
        episodes = []

        # Only use the first season and first episode for language/provider info
        first_season = series.seasons[0]
        first_episode = first_season.episodes[0]

        # All episode URLs
        for season in series.seasons:
            for episode in season.episodes:
                episodes.append(episode.url)

        # Extract provider names from first episode
        first_provider_dict = next(iter(first_episode.provider_data._data.values()))
        providers = tuple(first_provider_dict.keys())

        # Extract language labels from first episode
        for key in first_episode.provider_data._data.keys():
            site_key = INVERSE_LANG_KEY_MAP[key]
            label = LANG_LABELS[site_key]
            if label not in languages:
                languages.append(label)

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

        # --- Aniskip ---
        aniskip_height = 2
        aniskip = F.add(
            npyscreen.TitleMultiSelect,
            name="Aniskip",
            values=["Enabled"],
            max_height=aniskip_height,
            rely=y,
            scroll_exit=True,
        )

        # --- Function to update visibility based on action ---
        def update_visibility():
            selected = action.get_selected_objects()
            selected_action = selected[0] if selected else Action.DOWNLOAD.value

            if selected_action in [Action.WATCH.value, Action.SYNCPLAY.value]:
                path.hidden = True
                aniskip.hidden = False
            else:  # DOWNLOAD
                path.hidden = False
                aniskip.hidden = True

            # Refresh the form layout
            F.display()

        # Attach handler: update visibility when action changes
        action.when_value_edited = update_visibility

        # Initialize visibility
        update_visibility()

        # --- Language ---
        language_height = len(languages) + 1
        language = F.add(
            npyscreen.TitleSelectOne,
            name="Language",
            values=languages,
            value=[0],
            max_height=language_height,
            rely=y + 2,  # adjust position after path/aniskip
            scroll_exit=True,
        )

        # --- Provider ---
        provider_height = len(providers) + 1
        provider = F.add(
            npyscreen.TitleSelectOne,
            name="Provider",
            values=providers,
            value=[0],
            max_height=provider_height,
            rely=y + 2 + language_height,
            scroll_exit=True,
        )

        # --- Episodes ---
        term_height = curses.LINES
        remaining_height = term_height - (y + 2 + language_height + provider_height) - 2
        min_episode_height = 4
        episode_height = max(min_episode_height, remaining_height)

        episodes_widget = F.add(
            npyscreen.TitleMultiSelect,
            name="Episodes",
            values=episodes,
            rely=y + 2 + language_height + provider_height,
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
            [episodes_widget.values[i] for i in episodes_widget.value]
            if episodes_widget.value
            else []
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
def app(url):
    try:
        app_instance = MenuApp()
        app_instance.url = url
        app_instance.run()

        # Prepare a copy of result for logging, convert Path to string
        log_result = dict(app_instance.result)
        if isinstance(log_result.get("path"), Path):
            log_result["path"] = str(log_result["path"])

        # Log JSON with leading newline
        logger.debug("Menu Selection Output\n" + json.dumps(log_result, indent=4))

        # Map action names to methods
        action_methods = {
            "Download": "download",
            "Watch": "watch",
            "Syncplay": "syncplay",
        }

        action = app_instance.result.get("action")
        episodes = app_instance.result.get("episodes", [])
        selected_path = app_instance.result.get("path")
        selected_language = app_instance.result.get("language")
        selected_provider = app_instance.result.get("provider")

        if app_instance.result.get("aniskip"):
            os.environ["ANISKIP"] = "1"  # "Enabled"
        else:
            os.environ["ANISKIP"] = "0"

        if action in action_methods:
            method_name = action_methods[action]
            for episode_url in episodes:
                episode = AniworldEpisode(
                    url=episode_url,
                    selected_path=selected_path,
                    selected_language=selected_language,
                    selected_provider=selected_provider,
                )

                # Call the method dynamically
                getattr(episode, method_name)()
    except KeyboardInterrupt:
        pass
