import re
from collections import defaultdict
from enum import Enum
from typing import Tuple
from urllib.parse import urlparse
# import time

from ...config import logger, GLOBAL_SESSION


class Audio(Enum):
    """
    Available audio language options:

        - JAPANESE: Japanese dubbed audio
        - GERMAN:   German dubbed audio
        - ENGLISH:  English dubbed audio

    Required source for each option:

        Japanese Dub -> Source: German Sub, English Sub
        German Dub   -> Source: German Dub
        English Dub  -> Source: English Dub
    """

    JAPANESE = "Japanese"
    GERMAN = "German"
    ENGLISH = "English"


class Subtitles(Enum):
    """
    Available subtitle language options:

        - NONE:    No subtitles
        - GERMAN:  German subtitles
        - ENGLISH: English subtitles

    Required source for each option:

        German Sub   -> Source: German Sub
        English Sub  -> Source: English Sub
    """

    NONE = "None"
    GERMAN = "German"
    ENGLISH = "English"


class ProviderData:
    """
    Container for provider URLs grouped by language settings.

    The internal structure is:

        dict[(Audio, Subtitles)][provider_name] -> url

    Meaning:
    - The key is a tuple of (Audio, Subtitles)
    - The value is a dictionary mapping provider names to their URLs
    """

    def __init__(self, data):
        self._data = data

    def __str__(self):
        lines = []

        for (audio, subtitles), providers in sorted(
            self._data.items(), key=lambda item: (item[0][0].value, item[0][1].value)
        ):
            header = f"{audio.value} audio"
            if subtitles != Subtitles.NONE:
                header += f" + {subtitles.value} subtitles"

            lines.append(header)

            for provider, url in providers.items():
                lines.append(f"  - {provider:<8} -> {url}")

            lines.append("")

        return "\n".join(lines).rstrip()

    def __repr__(self):
        return f"{self.__class__.__name__}({self._data!r})"

    # Accept a tuple directly
    def get(self, lang_tuple: Tuple[Audio, Subtitles]):
        return self._data.get(lang_tuple, {})

    # Behave like a dictionary
    def __getitem__(self, lang_tuple: Tuple[Audio, Subtitles]):
        return self._data[lang_tuple]


class AniworldEpisode:
    """
    Represents a single episode (or movie entry) of an AniWorld anime series.

    Parameters:
        series:                 Parent series object.
        season:                 Parent season object this episode belongs to.
        url:                    Required. The AniWorld URL for this episode, e.g.
                                https://aniworld.to/anime/stream/highschool-dxd/staffel-1/episode-1
        episode_number:         Episode index within the season. Movies may use a special numbering.
        title_de:               German episode title.
        title_en:               English episode title, if available.

    Attributes (Example):
        series:                 <AniworldSeries object>
        season:                 <AniworldSeason object>
        url:                    https://aniworld.to/anime/stream/highschool-dxd/staffel-1/episode-1
        episode_number:         1
        title_de:               "Wir machen einen Ausflug ans Meer!"
        title_en:               "Going Sunbathing [Special]"

        provider_data:          For example: dict[(Audio, Subtitles)][provider_name]

        available_languages:    TODO -> implement
        available_providers:    TODO -> implement
        selected_language:      (Audio.JAPANESE, Subtitles.GERMAN)
        selected_provider:      Filemoon

        provider_link():        For example: provider_link((Audio.JAPANESE, Subtitles.GERMAN), "Filemoon")

        _is_movie:              False
        _html:                  <!doctype html> ...
    """

    def __init__(
        self,
        url=None,
        series=None,
        season=None,
        episode_number=None,
        title_de=None,
        title_en=None,
    ):
        self._series = series
        self._season = season
        self.url = url

        self.title_de = title_de
        self.title_en = title_en
        self.episode_number = episode_number

        self.__provider_data = None

        self.selected_language = (
            Audio.JAPANESE,
            Subtitles.GERMAN,
        )  # TODO: defaults for now
        self.selected_provider = "Filemoon"  # TODO: defaults for now

        self.__is_movie = None

        self.__html = None

    @property
    def season(self):
        if self._season is None:
            if not self.url:
                raise ValueError("Episode URL is required to auto-generate season")

            from .season import AniworldSeason

            if self.is_movie:
                # https://aniworld.to/anime/stream/masamune-kuns-revenge/filme
                movie_match = re.search(
                    r"^(https://aniworld\.to/anime/stream/[^/]+/filme)",
                    self.url,
                )
                if not movie_match:
                    raise ValueError(
                        f"Could not extract movie season from URL: {self.url}"
                    )
                season_url = movie_match.group(1)
            else:
                # https://aniworld.to/anime/stream/masamune-kuns-revenge/staffel-1
                season_match = re.search(
                    r"^(https://aniworld\.to/anime/stream/[^/]+/staffel-\d+)",
                    self.url,
                )
                if not season_match:
                    raise ValueError(f"Could not extract season from URL: {self.url}")
                season_url = season_match.group(1)

            self._season = AniworldSeason(season_url, series=self.series)

        return self._season

    @property
    def _html(self):
        if self.__html is None:
            logger.debug(f"fetching ({self.url})...")
            resp = GLOBAL_SESSION.get(self.url)
            self.__html = resp.text
        return self.__html

    @property
    def provider_data(self) -> ProviderData:
        if self.__provider_data is None:
            raw = self.__extract_provider_data()
            self.__provider_data = ProviderData(raw)
        return self.__provider_data

    @property
    def is_movie(self):
        if self.__is_movie is None:
            self.__is_movie = self.__extract_is_movie()
        return self.__is_movie

    def provider_link(self, language=None, provider=None):
        """
        Get the provider URL for a given language and provider name.

        Args:
            language: tuple (Audio, Subtitles). Defaults to self.selected_language.
            provider: str, provider name. Defaults to self.selected_provider.

        Returns:
            str URL if found, else None
        """
        if language is None:
            language = self.selected_language
        if provider is None:
            provider = self.selected_provider

        # Find matching key by comparing enum values instead of instances
        # This handles cases where enum instances might be different due to import/identity issues
        matching_key = None
        for key in self.provider_data._data.keys():
            if key[0].value == language[0].value and key[1].value == language[1].value:
                matching_key = key
                break

        # Use matching key if found, otherwise try direct lookup
        if matching_key:
            provider_dict = self.provider_data._data[matching_key]
        else:
            provider_dict = self.provider_data.get(language)
            if not provider_dict:
                return None

        return provider_dict.get(provider)

    def download(self):
        print(f"[DOWNLOADING] {self.url}")

        for _ in range(3):
            print(".", end="", flush=True)
            # time.sleep(0.1)

        print()

    def watch(self):
        print(f"[WATCHING] {self.url}")

        for _ in range(3):
            print(".", end="", flush=True)
            # time.sleep(0.1)

        print()

    def syncplay(self):
        print(f"[SYNCPLAYING] {self.url}")

        for _ in range(3):
            print(".", end="", flush=True)
            # time.sleep(0.1)

        print()

    # -----------------------------
    # Extraction helpers
    # -----------------------------

    def __extract_provider_data(self):
        """
        Extract provider links grouped by (Audio, Subtitles).

        Returns:
            dict[(Audio, Subtitles)][provider_name]
        """

        """
        <ul class="row">
            <li class="col-md-3 col-xs-12 col-sm-6 episodeLink2738955" data-lang-key="1" data-link-id="2738955" data-link-target="/redirect/2738955" data-external-embed="false">
                <div class="generateInlinePlayer">
                    <a class="watchEpisode" itemprop="url" href="/redirect/2738955" target="_blank">
                        <i class="icon VOE" title="Hoster VOE"></i>
                        <h4>VOE</h4>
                        <div class="hosterSiteVideoButton">Video öffnen</div>
                    </a>
                    <span>
                    </span>
                </div>
            </li>
            <li class="col-md-3 col-xs-12 col-sm-6 episodeLink2892597" data-lang-key="1" data-link-id="2892597" data-link-target="/redirect/2892597" data-external-embed="false">
                <div>
                    <a class="watchEpisode" itemprop="url" href="/redirect/2892597" target="_blank">
                        <i class="icon Filemoon" title="Hoster Filemoon"></i>
                        <h4>Filemoon</h4>
                        <div class="hosterSiteVideoButton">Video öffnen</div>
                    </a>
                    <span>
                    </span>
                </div>
            </li>
            <li class="col-md-3 col-xs-12 col-sm-6 episodeLink3033759" data-lang-key="1" data-link-id="3033759" data-link-target="/redirect/3033759" data-external-embed="false">
                <div>
                    <a class="watchEpisode" itemprop="url" href="/redirect/3033759" target="_blank">
                        <i class="icon Vidmoly" title="Hoster Vidmoly"></i>
                        <h4>Vidmoly</h4>
                        <div class="hosterSiteVideoButton">Video öffnen</div>
                    </a>
                    <span>
                    </span>
                </div>
            </li>
            <li class="col-md-3 col-xs-12 col-sm-6 episodeLink2739118" data-lang-key="2" data-link-id="2739118" data-link-target="/redirect/2739118" data-external-embed="false" style="display: none;">
                <div class="generateInlinePlayer">
                    <a class="watchEpisode" itemprop="url" href="/redirect/2739118" target="_blank">
                        <i class="icon VOE" title="Hoster VOE"></i>
                        <h4>VOE</h4>
                        <div class="hosterSiteVideoButton">Video öffnen</div>
                    </a>
                    <span>
                    </span>
                </div>
            </li>
            <li class="col-md-3 col-xs-12 col-sm-6 episodeLink2892472" data-lang-key="2" data-link-id="2892472" data-link-target="/redirect/2892472" data-external-embed="false" style="display: none;">
                <div>
                    <a class="watchEpisode" itemprop="url" href="/redirect/2892472" target="_blank">
                        <i class="icon Filemoon" title="Hoster Filemoon"></i>
                        <h4>Filemoon</h4>
                        <div class="hosterSiteVideoButton">Video öffnen</div>
                    </a>
                    <span>
                    </span>
                </div>
            </li>
            <li class="col-md-3 col-xs-12 col-sm-6 episodeLink3682431" data-lang-key="2" data-link-id="3682431" data-link-target="/redirect/3682431" data-external-embed="false" style="display: none;">
                <div>
                    <a class="watchEpisode" itemprop="url" href="/redirect/3682431" target="_blank">
                        <i class="icon Vidmoly" title="Hoster Vidmoly"></i>
                        <h4>Vidmoly</h4>
                        <div class="hosterSiteVideoButton">Video öffnen</div>
                    </a>
                    <span>
                    </span>
                </div>
            </li>
            <li class="col-md-3 col-xs-12 col-sm-6 episodeLink2738802" data-lang-key="3" data-link-id="2738802" data-link-target="/redirect/2738802" data-external-embed="false" style="display: none;">
                <div class="generateInlinePlayer">
                    <a class="watchEpisode" itemprop="url" href="/redirect/2738802" target="_blank">
                        <i class="icon VOE" title="Hoster VOE"></i>
                        <h4>VOE</h4>
                        <div class="hosterSiteVideoButton">Video öffnen</div>
                    </a>
                    <span>
                    </span>
                </div>
            </li>
            <li class="col-md-3 col-xs-12 col-sm-6 episodeLink3595798" data-lang-key="3" data-link-id="3595798" data-link-target="/redirect/3595798" data-external-embed="false" style="display: none;">
                <div>
                    <a class="watchEpisode" itemprop="url" href="/redirect/3595798" target="_blank">
                        <i class="icon Filemoon" title="Hoster Filemoon"></i>
                        <h4>Filemoon</h4>
                        <div class="hosterSiteVideoButton">Video öffnen</div>
                    </a>
                    <span>
                    </span>
                </div>
            </li>
            <li class="col-md-3 col-xs-12 col-sm-6 episodeLink3682483" data-lang-key="3" data-link-id="3682483" data-link-target="/redirect/3682483" data-external-embed="false" style="display: none;">
                <div>
                    <a class="watchEpisode" itemprop="url" href="/redirect/3682483" target="_blank">
                        <i class="icon Vidmoly" title="Hoster Vidmoly"></i>
                        <h4>Vidmoly</h4>
                        <div class="hosterSiteVideoButton">Video öffnen</div>
                    </a>
                    <span>
                    </span>
                </div>
            </li>
        </ul>
        """

        # Map site-specific language keys to semantic meaning
        LANG_KEY_MAP = {
            "1": (Audio.GERMAN, Subtitles.NONE),  # German Dub
            "2": (Audio.JAPANESE, Subtitles.ENGLISH),  # English Sub
            "3": (Audio.JAPANESE, Subtitles.GERMAN),  # German Sub
        }

        result = defaultdict(dict)

        # Pattern to find <li data-lang-key="...">...</li>
        li_pattern = re.compile(
            r'<li\s+[^>]*data-lang-key="(?P<key>\d+)"[^>]*>(?P<content>.*?)</li>',
            re.DOTALL,
        )
        # Pattern to find <h4>Provider</h4>
        h4_pattern = re.compile(r"<h4>(.*?)</h4>", re.DOTALL)
        # Pattern to find <a class="watchEpisode" href="...">
        a_pattern = re.compile(
            r'<a\s+[^>]*class="watchEpisode"[^>]*href="([^"]+)"', re.DOTALL
        )

        for match in li_pattern.finditer(self._html):
            lang_key = match.group("key")
            if lang_key not in LANG_KEY_MAP:
                continue

            audio, subtitles = LANG_KEY_MAP[lang_key]
            content = match.group("content")

            # Extract provider name
            h4_match = h4_pattern.search(content)
            if not h4_match:
                continue
            provider = h4_match.group(1).strip()

            # Extract URL
            a_match = a_pattern.search(content)
            if not a_match:
                continue
            href = a_match.group(1)

            # Build absolute URL
            parsed_url = urlparse(self.url)
            domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            url = f"{domain}{href}"

            result[(audio, subtitles)][provider] = url

        return dict(result)

    def __extract_provider_link(self):
        """
        Get the provider URL for a given language and provider name.

        Returns:
            str URL if found, else None
        """
        audio, subtitles = self.selected_language  # unpack the tuple
        provider_dict = self.provider_data.get(audio, subtitles)

        if not provider_dict:
            return None

        return provider_dict.get(self.selected_provider)

    def __extract_is_movie(self):
        """
        Determine whether the current URL points to a movie page.

        Returns:
            bool: True if the URL matches the movie pattern, otherwise False.
        """
        pattern = r"^https://aniworld\.to/anime/stream/[^/]+/filme/film-\d+/?$"
        return re.match(pattern, self.url) is not None
