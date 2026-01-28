from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Pattern, Type

from .config import (
    ANIWORLD_EPISODE_PATTERN,
    ANIWORLD_SEASON_PATTERN,
    ANIWORLD_SERIES_PATTERN,
    HANIME_TV_SERIES_PATTERN,
)
from .models import (
    AniworldEpisode,
    AniworldSeason,
    AniworldSeries,
    HanimeTVEpisode,
)


@dataclass(frozen=True)
class Provider:
    name: str
    series_pattern: Optional[Pattern[str]] = None
    season_pattern: Optional[Pattern[str]] = None
    episode_pattern: Optional[Pattern[str]] = None

    series_cls: Optional[Type] = None
    season_cls: Optional[Type] = None
    episode_cls: Optional[Type] = None


PROVIDERS = [
    Provider(
        name="AniWorld",
        series_pattern=ANIWORLD_SERIES_PATTERN,
        season_pattern=ANIWORLD_SEASON_PATTERN,
        episode_pattern=ANIWORLD_EPISODE_PATTERN,
        series_cls=AniworldSeries,
        season_cls=AniworldSeason,
        episode_cls=AniworldEpisode,
    ),
    Provider(
        name="HanimeTV",
        episode_pattern=HANIME_TV_SERIES_PATTERN,
        episode_cls=HanimeTVEpisode,
    ),
]


def resolve_provider(url: str) -> Provider:
    for provider in PROVIDERS:
        if provider.series_pattern and provider.series_pattern.fullmatch(url):
            return provider
        if provider.season_pattern and provider.season_pattern.fullmatch(url):
            return provider
        if provider.episode_pattern and provider.episode_pattern.fullmatch(url):
            return provider

    raise ValueError(f"Unsupported URL: {url}")
