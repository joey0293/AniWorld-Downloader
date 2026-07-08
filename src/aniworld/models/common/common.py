import re
from typing import Tuple

import ffmpeg

from ...config import Audio, Subtitles

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
