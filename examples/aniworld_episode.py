"""
Example: AniWorld Episode usage

This example prints all available episode values and shows what you can do
with them.

You can use this file as a reference for:
- Accessing metadata
- Accessing provider data
- Generating provider links
- Downloading / Watching / Syncplay
"""

from aniworld.config import Audio, Subtitles
from aniworld.models import AniworldSeries

# ----------------------------
# 1. Load the series
# ----------------------------
series_url = "https://aniworld.to/anime/stream/highschool-dxd"
series = AniworldSeries(series_url)

print("=== SERIES INFO ===")
print("Title:", series.title)
print("Cleaned Title:", series.title_cleaned)
print("URL:", series.url)
print("Description:", series.description)
print("Genres:", series.genres)
print("Release year:", series.release_year)
print("Poster URL:", series.poster_url)
print("Directors:", series.directors)
print("Actors:", series.actors)
print("Producer:", series.producer)
print("Country:", series.country)
print("Age rating:", series.age_rating)
print("Rating:", series.rating)
print("Number of seasons:", len(series.seasons))
print("Has movies:", series.has_movies)
print()

# ----------------------------
# 2. Select first season and episode
# ----------------------------
season = series.seasons[0]
episode = season.episodes[0]

print("=== EPISODE INFO ===")
print("Episode URL:", episode.url)
print("Episode number:", episode.episode_number)
print("Title (DE):", episode.title_de)
print("Title (EN):", episode.title_en)
print("Is movie:", episode.is_movie)
print("Is downloaded:", episode.is_downloaded["exists"])
print("Skip times:", episode.skip_times)

print()

# ----------------------------
# 3. Provider data
# ----------------------------
print("Provider data:", episode.provider_data)
print()

# ----------------------------
# 4. Provider link
# ----------------------------
# Example: German audio + no subtitles, provider VOE
lang = (Audio.GERMAN, Subtitles.NONE)
provider_name = "VOE"

provider_link = episode.provider_link(language=lang, provider=provider_name)
print("Provider link:", provider_link)
print()

# ----------------------------
# 5. URL chain values
# ----------------------------
# These are computed from provider link / redirect
print("Redirect URL:", episode.redirect_url)
print("Provider URL:", episode.provider_url)
print("Stream URL:", episode.stream_url)
print()

# ----------------------------
# 6. File path helpers
# ----------------------------
print("Base folder:", episode._base_folder)
print("Folder path:", episode._folder_path)
print("File name:", episode._file_name)
print("File extension:", episode._file_extension)
print("Full episode path:", episode._episode_path)
print()

# ----------------------------
# 7. Actions
# ----------------------------
# Uncomment to enable:
# episode.download()
# episode.watch()
# episode.syncplay()
