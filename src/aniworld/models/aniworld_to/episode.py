import os
import re
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Tuple
from urllib.parse import urlparse

import ffmpeg

from ...autodeps import get_player_path
from ...config import (
    ANIWORLD_EPISODE_PATTERN,
    GLOBAL_SESSION,
    INVERSE_LANG_LABELS,
    LANG_CODE_MAP,
    LANG_KEY_MAP,
    LANG_LABELS,
    NAMING_TEMPLATE,
    PROVIDER_HEADERS_D,
    PROVIDER_HEADERS_W,
    Audio,
    Subtitles,
    get_video_codec,
    logger,
)
from ...extractors import provider_functions


class ProviderData:
    """
    Container for provider URLs grouped by language settings.

    The internal structure is:

        dict[(Audio, Subtitles)][provider_name]

    Meaning:
    - The key is a tuple of (Audio, Subtitles)
    - The value is a dictionary mapping provider names to their URLs
    """

    def __init__(self, data):
        self._data = data

    def __str__(self):
        # return f"{self.__class__.__name__}({self._data!r})"
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
        url:                Required. The AniWorld URL for this episode, e.g.,
                            https://aniworld.to/anime/stream/highschool-dxd/staffel-1/episode-1
        series:             The parent series object.
        season:             The parent season object this episode belongs to.
        episode_number:     Optional. The episode index within the season; generated when creating a season object.
        title_de:           Optional. The German episode title; generated when creating a season object.
        title_en:           Optional. The English episode title; generated when creating a season object.
        selected_path:      Optional. The chosen path; provided in cases such as using a menu.
        selected_language:  Optional. The chosen language; provided in cases such as using a menu.
        selected_provider:  Optional. The chosen provider; provided in cases such as using a menu.

    Attributes (Example):
        url:                    "https://aniworld.to/anime/stream/highschool-dxd/staffel-1/episode-1"
        series:                 <AniworldSeries object>
        season:                 <AniworldSeason object>

        title_de:               "Ich habe endlich eine Freundin!"
        title_en:               "I Got a Girlfriend!"
        episode_number:         1
        provider_data:          ProviderData({(<Audio.GERMAN: 'German'>, <Subtitles.NONE: 'None'>): {'VOE': 'https://aniworld.to/redirect/2526098', 'Filemoon': 'https://aniworld.to/redirect/2883363', 'Vidmoly': 'https://aniworld.to/redirect/3028732'}, (<Audio.JAPANESE: 'Japanese'>, <Subtitles.ENGLISH: 'English'>): {'VOE': 'https://aniworld.to/redirect/1791080', 'Filemoon': 'https://aniworld.to/redirect/2883251', 'Vidmoly': 'https://aniworld.to/redirect/3674098'}, (<Audio.JAPANESE: 'Japanese'>, <Subtitles.GERMAN: 'German'>): {'VOE': 'https://aniworld.to/redirect/1791211', 'Filemoon': 'https://aniworld.to/redirect/2883481', 'Vidmoly': 'https://aniworld.to/redirect/3028797'}})

        selected_path:          "/Users/phoenixthrush/Downloads"
        selected_language:      "German Dub"
        selected_provider:      "VOE"

        redirect_url:           "https://aniworld.to/redirect/2526098"
        provider_url:           "https://voe.sx/e/brrfb6svahr0"
        stream_url:             "https://cdn-9hkqbevdlsunmsrc.edgeon-bandwidth.com/engine/hls2-c/01/11265/brrfb6svahr0_,n,l,.urlset/master.m3u8?t=7H-ROabLHNhRW7YUk7ukuV3gtpx-WPTn0Lhl9ZYwqkk&s=1768754148&e=14400&f=56328906&node=j9A3uKlh9EJIvaW3p3v65VuzDBUEiinc24sqRscdXcg=&i=185.213&sp=2500&asn=39351&q=n,l&rq=F2b2aGFqiQE6hVBHR3zxjsqBxOeHRuB3Setre8LO"

        self._base_folder:      /Users/phoenixthrush/Downloads/Highschool DxD (2012-2018) [imdbid-tt2230051]
        self._folder_path:      /Users/phoenixthrush/Downloads/Highschool DxD (2012-2018) [imdbid-tt2230051]/Season 01
        self._file_name:        Highschool DxD S01E01
        self._file_extension:   mkv
        self._episode_path:     /Users/phoenixthrush/Downloads/Highschool DxD (2012-2018) [imdbid-tt2230051]/Season 01/Highschool DxD S01E01.mkv

        is_movie                false
        is_downloaded           true

        skip_times:             {'found': True, 'results': [{'interval': {'start_time': 123.014, 'end_time': 213.014}, 'skip_type': 'op', 'skip_id': '1fd0d19a-4332-479e-9e3d-03e9b293db6a', 'episode_length': 1422.0416}, {'interval': {'start_time': 1187.09, 'end_time': 1277.09}, 'skip_type': 'ed', 'skip_id': '17a28c6e-5104-4142-9334-b57dbd024425', 'episode_length': 1422.0416}]}

        _html:                  "<!doctype html>[...]"

    Methods:
        download()
        watch()
        syncplay()

        provider_link(language=None, provider=None)  # <Audio.GERMAN: 'German'>, <Subtitles.NONE: 'None'>)
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
        if not self.is_valid_aniworld_episode_url(url):
            raise ValueError(f"Invalid AniWorld episode URL: {url}")

        self.url = url

        self._series = series
        self._season = season

        self.__title_de = title_de
        self.__title_en = title_en
        self.__episode_number = episode_number

        self.__selected_path_param = selected_path
        self.__selected_language_param = selected_language
        self.__selected_provider_param = selected_provider

        self.__provider_data = None

        self.__selected_path = None
        self.__selected_language = None
        self.__selected_provider = None

        self.__redirect_url = None
        self.__provider_url = None
        self.__stream_url = None

        # https://jellyfin.org/docs/general/server/media/shows/#organization
        self.__base_folder = None
        self.__folder_path = None
        self.__file_name = None
        self.__file_extension = None
        self.__episode_path = None

        self.__is_movie = None
        self.__is_downloaded = None

        self.__skip_times = None

        self.__html = None

    @staticmethod
    def is_valid_aniworld_episode_url(url):
        """
        Checks if the URL is a valid AniWorld episode URL.
        """

        # https://aniworld.to/anime/stream/highschool-dxd/staffel-1/episode-1
        # or
        # https://aniworld.to/anime/stream/highschool-dxd/filme/film-1

        url = url.strip()

        return bool(ANIWORLD_EPISODE_PATTERN.match(url))

    @property
    def redirect_url(self):
        if self.__redirect_url is None:
            self.__redirect_url = self.provider_link(
                self.__get_language(), self.selected_provider
            )
        return self.__redirect_url

    @property
    def provider_url(self):
        if self.__provider_url is None:
            self.__provider_url = GLOBAL_SESSION.get(self.redirect_url).url
        return self.__provider_url

    @property
    def stream_url(self):
        if self.__stream_url is None:
            try:
                self.__stream_url = provider_functions[
                    f"get_direct_link_from_{self.selected_provider.lower()}"
                ](self.provider_url)
            except KeyError:
                raise ValueError(
                    f"The provider '{self.selected_provider}' is not yet implemented."
                )
        return self.__stream_url

    @property
    def _base_folder(self):
        if self.__base_folder is None:
            series_folder_template = NAMING_TEMPLATE.split("/")[0]
            folder_str = series_folder_template.format(
                title=self.series.title_cleaned,
                year=self.series.release_year,
                imdbid=self.series.imbd,
                season=f"{self.season.season_number:02d}",
                episode=f"{self.episode_number:02d}",
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
                imdbid=self.series.imbd,
                season=f"{self.season.season_number:02d}",
                episode=f"{self.episode_number:02d}",
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
                imdbid=self.series.imbd,
                season=f"{self.season.season_number:02d}",
                episode=f"{self.episode_number:02d}",
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
    def episode_number(self):
        if self.__episode_number is None:
            self.__episode_number = self.__extract_episode_number()
        return self.__episode_number

    @property
    def season(self):
        if self._season is None:
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

            self._season = AniworldSeason(season_url, series=self._series)

        return self._season

    @property
    def series(self):
        if self._series is None:
            from .series import AniworldSeries
            # Example URLs:
            # https://aniworld.to/anime/stream/highschool-dxd/staffel-1/episode-1
            # https://aniworld.to/anime/stream/highschool-dxd/filme/film-1

            # Regex to match up to /stream/<series-name>
            match = re.match(r"(https://aniworld\.to/anime/stream/[^/]+)", self.url)
            if match:
                series_url = match.group(1)
            else:
                # fallback to full URL if regex fails
                series_url = self.url

            self._series = AniworldSeries(series_url)

        return self._series

    @property
    def _html(self):
        if self.__html is None:
            logger.debug(f"fetching ({self.url})...")
            resp = GLOBAL_SESSION.get(self.url)
            self.__html = resp.text
        return self.__html

    @property
    def provider_data(self):
        if self.__provider_data is None:
            raw = self.__extract_provider_data()
            self.__provider_data = ProviderData(raw)
        return self.__provider_data

    # Load Configuration Values

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

    ###

    @property
    def is_movie(self):
        if self.__is_movie is None:
            self.__is_movie = self.__extract_is_movie()
        return self.__is_movie

    @property
    def is_downloaded(self):
        if self.__is_downloaded is None:
            self.__is_downloaded = self.__check_downloaded()
        return self.__is_downloaded

    @property
    def skip_times(self):
        if self.__skip_times is None:
            self.__skip_times = self.__extract_skip_times()
        return self.__skip_times

    def __extract_episode_number(self):
        """
        Extract episode number.

        Returns:
            int: Episode number if found, otherwise None.
        """

        match = re.search(r"\d+(?!.*\d)", self.url)
        return int(match.group()) if match else None

    def __extract_title_de(self):
        """
        Extract German title from the episode page.

        Returns:
            str or None: German title if found, otherwise None.
        """

        html = self._html
        if not html:
            return None

        german_match = re.search(
            r'<span[^>]*class="episodeGermanTitle"[^>]*>([^<]*)', html
        )

        if german_match:
            return german_match.group(1).strip()

        return None

    def __extract_title_en(self):
        """
        Extract English title from the episode page.

        Returns:
            str or None: English title if found, otherwise None.
        """

        html = self._html
        if not html:
            return None

        # Look for specific English title class
        english_match = re.search(
            r'<small[^>]*class="episodeEnglishTitle"[^>]*>([^<]*)', html
        )
        if english_match:
            return english_match.group(1).strip()

        return None

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

    def __get_language(self):
        # Look up the key in LANG_LABELS by value
        key = next(
            (k for k, v in LANG_LABELS.items() if v == self.selected_language), None
        )
        if key is None:
            return "Unknown"
        return LANG_KEY_MAP[key]

    def __check_downloaded(self):
        result = {
            "exists": False,
            "video_langs": set(),
            "audio_langs": set(),
        }

        if not self._episode_path.exists():
            return result

        result["exists"] = True

        try:
            probe = ffmpeg.probe(str(self._episode_path))
        except ffmpeg.Error:
            return result

        streams = probe.get("streams", [])

        for s in streams:
            lang = s.get("tags", {}).get("language", "und")
            if s.get("codec_type") == "video":
                result["video_langs"].add(lang)
            elif s.get("codec_type") == "audio":
                result["audio_langs"].add(lang)

        return result

    def download(self):
        """
        Download required audio/video streams for this episode.

        Supports:
        - Full preset download if neither audio nor video exists.
        - Partial download if only one stream is missing.
        - Reuses streams when possible to avoid duplicate downloads.
        """

        # ---------------------------------------------------------
        # 1) Check existing streams
        # ---------------------------------------------------------
        check = self.__check_downloaded()

        # ---------------------------------------------------------
        # 2) Prepare HTTP headers
        # ---------------------------------------------------------
        headers = PROVIDER_HEADERS_D.get(self.selected_provider, {})
        input_kwargs = {}
        if headers:
            header_list = [f"{k}: {v}" for k, v in headers.items()]
            input_kwargs["headers"] = "\r\n".join(header_list) + "\r\n"

        # ---------------------------------------------------------
        # 3) Resolve user language selection
        # ---------------------------------------------------------
        selected_key = INVERSE_LANG_LABELS[self.selected_language]
        audio_enum, sub_enum = LANG_KEY_MAP[selected_key]

        audio_code = LANG_CODE_MAP[audio_enum]
        wants_clean_video = sub_enum == Subtitles.NONE
        sub_video_code = None if wants_clean_video else LANG_CODE_MAP[sub_enum]

        # ---------------------------------------------------------
        # 4) Determine missing streams
        # ---------------------------------------------------------
        has_video = bool(check["video_langs"])
        has_audio = audio_code in check["audio_langs"]

        need_audio = not has_audio
        if not has_video:
            need_video = True
        elif not wants_clean_video:
            need_video = sub_video_code not in check["video_langs"]
        else:
            need_video = False

        # ---------------------------------------------------------
        # 5) Skip if nothing is missing
        # ---------------------------------------------------------
        if not need_audio and not need_video:
            logger.debug(f"[SKIPPED] {self._file_name}")
            return

        os.makedirs(self._folder_path, exist_ok=True)

        # ---------------------------------------------------------
        # 6) Decide if we can download a single full stream
        # ---------------------------------------------------------
        # Download single stream when both audio and video needed (includes all language configs)
        full_stream_needed = need_audio and need_video

        temp_audio = self._episode_path.with_suffix(".temp_audio.mkv")
        temp_video = self._episode_path.with_suffix(".temp_video.mkv")
        temp_full = self._episode_path.with_suffix(".temp_full.mkv")

        if full_stream_needed:
            logger.debug("[DOWNLOADING] full preset (audio + video together)")

            # Prepare per-stream metadata
            stream_metadata = {"metadata:s:a:0": f"language={audio_code}"}
            if not wants_clean_video:
                stream_metadata["metadata:s:v:0"] = f"language={sub_video_code}"

            # Download full stream
            video_codec = get_video_codec()
            ffmpeg.input(self.stream_url, **input_kwargs).output(
                str(temp_full),
                vcodec=video_codec,
                acodec=video_codec,
                **stream_metadata,
            ).run()

            # Mux into final file (or just move if file didn't exist before)
            if self._episode_path.exists():
                inputs = [
                    ffmpeg.input(str(self._episode_path)),
                    ffmpeg.input(str(temp_full)),
                ]
                output_path = self._episode_path.with_suffix(".new.mkv")
                ffmpeg.output(*inputs, str(output_path), c="copy").run()
                os.replace(output_path, self._episode_path)
            else:
                # First file, just move
                os.replace(temp_full, self._episode_path)

            # Cleanup
            if temp_full.exists():
                temp_full.unlink()
            return

        # ---------------------------------------------------------
        # 7) Partial downloads
        # ---------------------------------------------------------
        if need_audio:
            logger.debug("[DOWNLOADING] audio stream")
            video_codec = get_video_codec()
            ffmpeg.input(self.stream_url, **input_kwargs).output(
                str(temp_audio),
                acodec=video_codec,
                map="0:a:0?",
                **{"metadata:s:a:0": f"language={audio_code}"},
            ).run()

        if need_video:
            logger.debug("[DOWNLOADING] video stream")
            video_codec = get_video_codec()
            ffmpeg.input(self.stream_url, **input_kwargs).output(
                str(temp_video),
                vcodec=video_codec,
                map="0:v:0?",
                **(
                    {}
                    if wants_clean_video
                    else {"metadata:s:v:0": f"language={sub_video_code}"}
                ),
            ).run()

        # ---------------------------------------------------------
        # 8) Mux downloaded streams with existing file
        # ---------------------------------------------------------
        logger.debug("[MUXING] combining streams")
        inputs = (
            [ffmpeg.input(str(self._episode_path))]
            if self._episode_path.exists()
            else []
        )

        if need_audio:
            inputs.append(ffmpeg.input(str(temp_audio)))
        if need_video:
            inputs.append(ffmpeg.input(str(temp_video)))

        output_path = self._episode_path.with_suffix(".new.mkv")
        ffmpeg.output(*inputs, str(output_path), c="copy").run()
        os.replace(output_path, self._episode_path)

        # ---------------------------------------------------------
        # 9) Cleanup temporary files
        # ---------------------------------------------------------
        for f in (temp_audio, temp_video):
            if f.exists():
                f.unlink()

    def watch(self):
        """Watch the current episode with provider headers."""
        print(f"[WATCHING] {self._file_name}")

        # Get headers for the selected provider
        headers = PROVIDER_HEADERS_W.get(self.selected_provider, {})

        # Build command as list to avoid shell injection issues
        cmd = [str(get_player_path()), self.stream_url]

        # Check if aniskip is enabled
        aniskip_enabled = os.getenv("ANIWORLD_USE_ANISKIP", "0") == "1"
        logger.debug(f"[ANISKIP ENABLED]: {aniskip_enabled}")

        skip_times = self.skip_times if aniskip_enabled else None

        if skip_times:
            from ...aniskip import build_mpv_flags, setup_aniskip

            setup_aniskip()

            skip_flags = build_mpv_flags(skip_times).split()
            cmd.extend(skip_flags)
            logger.debug(f"[SKIP TIMES FOUND]: {skip_flags}")

        # Add mpv options
        cmd.extend(
            ["--no-ytdl", "--fs", "--quiet", f"--force-media-title={self._file_name}"]
        )

        # Add headers if present
        if headers:
            # Build header arguments properly escaped
            header_args = [f"{k}: {v}" for k, v in headers.items()]
            cmd.append("--http-header-fields=" + ",".join(header_args))

        # Print the command for reference
        print(" ".join(cmd))

        # Run the command using argument list (no shell)
        subprocess.run(cmd)

    # TODO: implement Syncplay
    def syncplay(self):
        self.watch()

    # -----------------------------
    # Extraction helpers
    # -----------------------------

    # TODO: extract thumbnail lazy loaded too
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

    def __extract_is_movie(self):
        """
        Determine whether the current URL points to a movie page.

        Returns:
            bool: True if the URL matches the movie pattern, otherwise False.
        """
        pattern = r"^https://aniworld\.to/anime/stream/[^/]+/filme/film-\d+/?$"
        return re.match(pattern, self.url) is not None

    def __extract_skip_times(self):
        if self.is_movie:
            return None

        from ...aniskip import get_skip_times

        mal_id = self.series.mal_id
        logger.debug(f"Fetching MAL IDs for series: {mal_id}")

        season_number = self.season.season_number - 1
        logger.debug(f"Using season number: {season_number + 1}")

        episode_number = self.episode_number
        logger.debug(f"Using episode number: {episode_number}")

        return get_skip_times(mal_id[season_number], episode_number)
