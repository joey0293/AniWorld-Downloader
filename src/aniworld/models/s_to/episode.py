import os
import re
from pathlib import Path

from ...config import (
    GLOBAL_SESSION,
    NAMING_TEMPLATE,
    SERIENSTREAM_EPISODE_PATTERN,
    logger,
)
from ..common import check_downloaded


class SerienstreamEpisode:
    """
    Represents a single episode of an Serienstream series.

    Parameters:
        url:                Required. The Serienstream URL for this episode, e.g.,
                            https://serienstream.to/serie/american-horror-story-die-dunkle-seite-in-dir/staffel-1/episode-1
        series:             The parent series object.
        season:             The parent season object this episode belongs to.
        episode_number:     Optional. The episode index within the season; generated when creating a season object.
        title_de:           Optional. The German episode title; generated when creating a season object.
        title_en:           Optional. The English episode title; generated when creating a season object.
        selected_path:      Optional. The chosen path; provided in cases such as using a menu.
        selected_language:  Optional. The chosen language; provided in cases such as using a menu.
        selected_provider:  Optional. The chosen provider; provided in cases such as using a menu.

    Attributes (Example):
        url:                    "https://serienstream.to/serie/american-horror-story-die-dunkle-seite-in-dir/staffel-1/episode-1"
        series:                 <SerienstreamSeries object>
        season:                 <SerienstreamSeason object>

        title_de:               "Neuanfang"
        title_en:               "Pilot"
        episode_number:         1
        provider_data:          TODO: ProviderData({(<Audio.GERMAN: 'German'>, <Subtitles.NONE: 'None'>): {'VOE': 'https://aniworld.to/redirect/2526098', 'Filemoon': 'https://aniworld.to/redirect/2883363', 'Vidmoly': 'https://aniworld.to/redirect/3028732'}, (<Audio.JAPANESE: 'Japanese'>, <Subtitles.ENGLISH: 'English'>): {'VOE': 'https://aniworld.to/redirect/1791080', 'Filemoon': 'https://aniworld.to/redirect/2883251', 'Vidmoly': 'https://aniworld.to/redirect/3674098'}, (<Audio.JAPANESE: 'Japanese'>, <Subtitles.GERMAN: 'German'>): {'VOE': 'https://aniworld.to/redirect/1791211', 'Filemoon': 'https://aniworld.to/redirect/2883481', 'Vidmoly': 'https://aniworld.to/redirect/3028797'}})

        selected_path:          Downloads
        selected_language:      "German Dub"
        selected_provider:      "VOE"

        redirect_url:           "TODO"
        provider_url:           "TODO"
        stream_url:             "TODO"

        self._base_folder:      Downloads/American Horror Story (2011) [imdbid-tt1844624]
        self._folder_path:      Downloads/American Horror Story (2011) [imdbid-tt1844624]/Season 1
        self._file_name:        American Horror Story S1E1
        self._file_extension:   mkv
        self._episode_path:     Downloads/American Horror Story (2011) [imdbid-tt1844624]/Season 1/American Horror Story S1E1.mkv

        is_downloaded           {'exists': False, 'video_langs': set(), 'audio_langs': set()}

        _html:                  "<!doctype html>[...]"

    Methods:
        download()
        watch()
        syncplay()

    Attributes That Do Not Exists as on Aniworld:
        is_movie, skip_times
    """

    def __init__(
        self,
        url=None,
        series=None,
        season=None,
        episode_number=None,
        title_de=None,
        title_en=None,
        selected_path=None,
        selected_language=None,
        selected_provider=None,
    ):
        if not self.__is_valid_serienstream_episode_url(url):
            raise ValueError(f"Invalid Serienstream episode URL: {url}")

        self.url = url
        self._series = series
        self._season = season

        self.__episode_number = episode_number
        self.__title_de = title_de
        self.__title_en = title_en

        self.__selected_path_param = selected_path
        self.__selected_language_param = selected_language
        self.__selected_provider_param = selected_provider

        self.__provider_data = None

        self.__selected_path = None
        self.__selected_language = None
        self.__selected_provider = None

        self.__redirect_url = None
        self.__provider_url = None

        # https://jellyfin.org/docs/general/server/media/shows/#organization
        self.__base_folder = None
        self.__folder_path = None
        self.__file_name = None
        self.__file_extension = None
        self.__episode_path = None

        self.__is_downloaded = None

        self.__html = None

    # -----------------------------
    # STATIC METHODS
    # -----------------------------

    @staticmethod
    def __is_valid_serienstream_episode_url(url):
        return bool(SERIENSTREAM_EPISODE_PATTERN.match(url))

    # -----------------------------
    # PUBLIC PROPERTIES (lazy load)
    # -----------------------------

    @property
    def series(self):
        if self._series is None:
            from .series import SerienstreamSeries

            series_url = self.url.rsplit("/staffel-", 1)[0]
            self._series = SerienstreamSeries(url=series_url)
        return self._series

    @property
    def season(self):
        if self._season is None:
            from .season import SerienstreamSeason

            season_url = self.url.rsplit("/episode-", 1)[0]
            self._season = SerienstreamSeason(url=season_url)
        return self._season

    @property
    def episode_number(self):
        if self.__episode_number is None:
            self.__episode_number = self.__extract_episode_number()
        return self.__episode_number

    @property
    def title_de(self):
        if self.__title_de is None:
            self.__title_de = self.__extract_title_de()
        return self.__title_de

    @property
    def title_en(self):
        if self.__title_en is None:
            self.__title_en = self.__extract_title_en()
        return self.__title_en

    @property
    def provider_data(self):
        if self.__provider_data is None:
            self.__provider_data = "TODO"
        return self.__provider_data

    @property
    def selected_path(self):
        if self.__selected_path is None:
            self.__selected_path = self.__selected_path_param or os.getenv(
                "ANIWORLD_DOWNLOAD_PATH", str(Path.home() / "Downloads")
            )
        return self.__selected_path

    @property
    def selected_language(self):
        if self.__selected_language is None:
            self.__selected_language = self.__selected_language_param or os.getenv(
                "ANIWORLD_LANGUAGE", "German Dub"
            )
        return self.__selected_language

    @property
    def selected_provider(self):
        if self.__selected_provider is None:
            self.__selected_provider = self.__selected_provider_param or os.getenv(
                "ANIWORLD_PROVIDER", "VOE"
            )
        return self.__selected_provider

    @property
    def redirect_url(self):
        if self.__redirect_url is None:
            self.__redirect_url = "TODO"
        return self.__redirect_url

    @property
    def provider_url(self):
        if self.__provider_url is None:
            self.__provider_url = "TODO"
        return self.__provider_url

    @property
    def stream_url(self):
        return "TODO"

    # TODO: add this into a common base class
    @property
    def _base_folder(self):
        if self.__base_folder is None:
            series_folder_template = NAMING_TEMPLATE.split("/")[0]
            folder_str = series_folder_template.format(
                title=self.series.title_cleaned,
                year=self.series.release_year,
                imdbid=self.series.imdb,
                season=f"{self.season.season_number}",
                episode=f"{self.episode_number}",
            )
            self.__base_folder = Path(self.selected_path) / folder_str
        return self.__base_folder

    @property
    def _folder_path(self):
        if self.__folder_path is None:
            try:
                season_folder_template = NAMING_TEMPLATE.split("/")[1]
            except IndexError:
                season_folder_template = f"Season {self.season.season_number:02d}"
            folder_str = season_folder_template.format(
                title=self.series.title_cleaned,
                year=self.series.release_year,
                imdbid=self.series.imdb,
                season=f"{self.season.season_number}",
                episode=f"{self.episode_number}",
            )
            self.__folder_path = self._base_folder / folder_str
        return self.__folder_path

    @property
    def _file_name(self):
        if self.__file_name is None:
            try:
                file_template = NAMING_TEMPLATE.split("/")[-1]
            except IndexError:
                file_template = f"{self.series.title_cleaned} S{self.season.season_number:02d}E{self.episode_number:02d}.mkv"

            # Remove extension
            if "." in file_template:
                file_template = ".".join(file_template.split(".")[:-1])

            # Replace %style% with {style} for compatibility
            file_template = file_template.replace("%title%", "{title}")
            file_template = file_template.replace("%year%", "{year}")
            file_template = file_template.replace("%imdbid%", "{imdbid}")
            file_template = file_template.replace("%season%", "{season}")
            file_template = file_template.replace("%episode%", "{episode}")

            self.__file_name = file_template.format(
                title=self.series.title_cleaned,
                year=self.series.release_year,
                imdbid=self.series.imdb,
                season=f"{self.season.season_number}",
                episode=f"{self.episode_number}",
            )
        return self.__file_name

    @property
    def _file_extension(self):
        if self.__file_extension is None:
            try:
                ext = NAMING_TEMPLATE.split("/")[-1].split(".")[-1]
                self.__file_extension = ext if ext else "mkv"
            except IndexError:
                self.__file_extension = "mkv"
        return self.__file_extension

    @property
    def _episode_path(self):
        if self.__episode_path is None:
            self.__episode_path = (
                self._folder_path / f"{self._file_name}.{self._file_extension}"
            )
        return self.__episode_path

    # END

    @property
    def is_downloaded(self):
        if self.__is_downloaded is None:
            self.__is_downloaded = check_downloaded(self._episode_path)
        return self.__is_downloaded

    @property
    def _html(self):
        if self.__html is None:
            logger.debug(f"fetching ({self.url})...")
            resp = GLOBAL_SESSION.get(self.url)
            self.__html = resp.text
        return self.__html

    # -----------------------------
    # PRIVATE EXTRACTION FUNCTIONS
    # -----------------------------

    def __extract_episode_number(self):
        """
        https://serienstream.to/serie/american-horror-story-die-dunkle-seite-in-dir/staffel-1/episode-1
        """

        return int(self.url.rstrip("/").split("-")[-1])

    def __extract_title_de(self):
        """
        <h2 class="h4 mb-1">S01E01: Neuanfang (Pilot) </h2>

        without parantheses
        """

        pattern = r"S\d{2}E\d{2}:\s(.*?)(\s\(|</h2>)"
        match = re.search(pattern, self._html)

        if match:
            return match.group(1).strip()

        return ""

    def __extract_title_en(self):
        """
        <h2 class="h4 mb-1">S01E01: Neuanfang (Pilot) </h2>

        in parantheses
        """

        pattern = r"S\d{2}E\d{2}:\s.*\((.*?)\)"
        match = re.search(pattern, self._html)

        if match:
            return match.group(1).strip()

        return ""

    # -----------------------------
    # PUBLIC METHODS
    # -----------------------------

    def download(self):
        print(f"Downloading episode from {self.url}...")

    def watch(self):
        print(f"Watching episode from {self.url}...")

    def syncplay(self):
        print(f"Syncplaying episode from {self.url}...")
