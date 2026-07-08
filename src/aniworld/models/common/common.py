import os
import re
import subprocess
from typing import Tuple

import ffmpeg

from ...autodeps import get_player_path, get_syncplay_path
from ...config import (
    INVERSE_LANG_LABELS,
    LANG_CODE_MAP,
    LANG_KEY_MAP,
    PROVIDER_HEADERS_D,
    PROVIDER_HEADERS_W,
    Audio,
    Subtitles,
    get_video_codec,
    logger,
)

# Precompile regex for forbidden filename characters
FORBIDDEN_CHARS = re.compile(r'[<>:"/\\|?*]')


def clean_title(title: str) -> str:
    """Clean a string to make it safe for use as a filename."""
    return FORBIDDEN_CHARS.sub("_", title).strip()


def check_downloaded(episode_path):
    result = {
        "exists": False,
        "video_langs": set(),
        "audio_langs": set(),
    }

    if not episode_path.exists():
        return result

    result["exists"] = True

    try:
        probe = ffmpeg.probe(episode_path)
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


# -----------------------------------------------------------------------------
# Episode actions (moved from models/*/episode.py)
# -----------------------------------------------------------------------------


def download(self):
    """Download required audio/video streams for an episode (AniWorld + s.to)."""

    check = check_downloaded(self._episode_path)

    headers = PROVIDER_HEADERS_D.get(self.selected_provider, {})
    input_kwargs = {}
    if headers:
        header_list = [f"{k}: {v}" for k, v in headers.items()]
        input_kwargs["headers"] = "\r\n".join(header_list) + "\r\n"

    url = (getattr(self, "url", "") or "").lower()
    is_serienstream = ("serienstream.to" in url) or ("s.to" in url)

    if is_serienstream and hasattr(self, "_normalize_language"):
        # s.to: only audio selection (no subtitle variants)
        audio_enum, sub_enum = self._normalize_language(self.selected_language)
        audio_code = {"German": "deu", "English": "eng"}.get(
            getattr(audio_enum, "value", None)
        )
        if not audio_code:
            raise ValueError(
                f"Unsupported audio language for serienstream.to: {audio_enum}"
            )
        wants_clean_video = True
        sub_video_code = None
    else:
        # aniworld.to
        selected_key = INVERSE_LANG_LABELS[self.selected_language]
        audio_enum, sub_enum = LANG_KEY_MAP[selected_key]

        audio_code = LANG_CODE_MAP[audio_enum]
        wants_clean_video = sub_enum == Subtitles.NONE
        sub_video_code = None if wants_clean_video else LANG_CODE_MAP[sub_enum]

    has_video = bool(check["video_langs"])
    has_audio = audio_code in check["audio_langs"]

    need_audio = not has_audio
    if not has_video:
        need_video = True
    elif not wants_clean_video:
        need_video = sub_video_code not in check["video_langs"]
    else:
        need_video = False

    if not need_audio and not need_video:
        logger.debug(f"[SKIPPED] {self._file_name}")
        return

    os.makedirs(self._folder_path, exist_ok=True)

    full_stream_needed = need_audio and need_video

    temp_audio = self._episode_path.with_suffix(".temp_audio.mkv")
    temp_video = self._episode_path.with_suffix(".temp_video.mkv")
    temp_full = self._episode_path.with_suffix(".temp_full.mkv")

    if full_stream_needed:
        logger.debug("[DOWNLOADING] full preset (audio + video together)")

        stream_metadata = {"metadata:s:a:0": f"language={audio_code}"}
        if (not wants_clean_video) and sub_video_code:
            stream_metadata["metadata:s:v:0"] = f"language={sub_video_code}"

        video_codec = get_video_codec()
        ffmpeg.input(self.stream_url, **input_kwargs).output(
            str(temp_full),
            vcodec=video_codec,
            acodec=video_codec,
            **stream_metadata,
        ).run()

        if self._episode_path.exists():
            inputs = [
                ffmpeg.input(str(self._episode_path)),
                ffmpeg.input(str(temp_full)),
            ]
            output_path = self._episode_path.with_suffix(".new.mkv")
            ffmpeg.output(*inputs, str(output_path), c="copy").run()
            os.replace(output_path, self._episode_path)
        else:
            os.replace(temp_full, self._episode_path)

        if temp_full.exists():
            temp_full.unlink()
        return

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

    logger.debug("[MUXING] combining streams")
    inputs = (
        [ffmpeg.input(str(self._episode_path))] if self._episode_path.exists() else []
    )

    if need_audio:
        inputs.append(ffmpeg.input(str(temp_audio)))
    if need_video:
        inputs.append(ffmpeg.input(str(temp_video)))

    output_path = self._episode_path.with_suffix(".new.mkv")
    ffmpeg.output(*inputs, str(output_path), c="copy").run()
    os.replace(output_path, self._episode_path)

    for f in (temp_audio, temp_video):
        if f.exists():
            f.unlink()


def watch(self):
    """Watch the current episode with provider headers."""

    print(f"[WATCHING] {self._file_name}")

    headers = PROVIDER_HEADERS_W.get(self.selected_provider, {})
    cmd = [str(get_player_path()), self.stream_url]

    # AniSkip: AniWorld only; ignore for s.to
    aniskip_enabled = os.getenv("ANIWORLD_USE_ANISKIP", "0") == "1"
    if aniskip_enabled and hasattr(self, "skip_times"):
        skip_times = self.skip_times
    else:
        skip_times = None

    if skip_times:
        from ...aniskip import build_mpv_flags, setup_aniskip

        setup_aniskip()
        skip_flags = build_mpv_flags(skip_times).split()
        cmd.extend(skip_flags)
        logger.debug(f"[SKIP TIMES FOUND]: {skip_flags}")

    cmd.extend(
        ["--no-ytdl", "--fs", "--quiet", f"--force-media-title={self._file_name}"]
    )

    if headers:
        header_args = [f"{k}: {v}" for k, v in headers.items()]
        cmd.append("--http-header-fields=" + ",".join(header_args))

    print(" ".join(cmd))
    subprocess.run(cmd)


def syncplay(self):
    """Syncplay the current episode (AniWorld) or fall back to watch (s.to)."""

    # s.to currently has no dedicated syncplay implementation
    if not hasattr(self, "skip_times"):
        return self.watch()

    print(f"[Syncplaying] {self._file_name}")

    headers = PROVIDER_HEADERS_W.get(self.selected_provider, {})

    cmd = [
        str(get_syncplay_path()),
        "--no-gui",
        "--no-store",
        "--host",
        os.getenv("SYNCPLAY_HOST", "syncplay.pl:8997"),
        "--room",
        os.getenv("SYNCPLAY_ROOM", "AniWorld-Downloader-Room"),
        "--name",
        os.getenv("SYNCPLAY_USERNAME", "AniWorld-Downloader"),
        "--player-path",
        "IINA" if os.getenv("ANIWORLD_USE_IINA") else "mpv",
    ]

    cmd.append("--")
    cmd.append(self.stream_url)

    aniskip_enabled = os.getenv("ANIWORLD_USE_ANISKIP", "0") == "1"
    skip_times = self.skip_times if aniskip_enabled else None

    if skip_times:
        from ...aniskip import build_mpv_flags, setup_aniskip

        setup_aniskip()
        skip_flags = build_mpv_flags(skip_times).split()
        cmd.extend(skip_flags)
        logger.debug(f"[SKIP TIMES FOUND]: {skip_flags}")

    cmd.extend(
        ["--no-ytdl", "--fs", "--quiet", f"--force-media-title={self._file_name}"]
    )

    if headers:
        header_args = [f"{k}: {v}" for k, v in headers.items()]
        cmd.append("--http-header-fields=" + ",".join(header_args))

    print(" ".join(cmd))
    subprocess.run(cmd)
