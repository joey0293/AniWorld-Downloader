import os

from aniworld.models import AniworldEpisode

episode = AniworldEpisode(
    "https://aniworld.to/anime/stream/prison-school/staffel-1/episode-1"
)

# Enable AniSkip feature
os.environ["ANIWORLD_USE_ANISKIP"] = "1"

# episode.watch()
print(episode.stream_url)
print(episode.stream_url)
