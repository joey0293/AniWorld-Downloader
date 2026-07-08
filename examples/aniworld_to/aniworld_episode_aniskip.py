import os

from aniworld.models import AniworldEpisode

episode = AniworldEpisode(
    "https://aniworld.to/anime/stream/highschool-dxd/staffel-1/episode-1"
)

# Enable AniSkip feature
os.environ["ANIWORLD_ANISKIP"] = "1"

# Watch the episode with AniSkip enabled
episode.watch()
