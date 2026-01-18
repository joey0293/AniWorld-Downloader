from aniworld.models import AniworldSeries, Audio, Subtitles

"""
from .series import AniworldSeries
series = AniworldSeries("https://aniworld.to/anime/stream/goblin-slayer")
    print(series.url)
    print(series.title)
    print(series.description)
    print(series.genres)
    print(series.release_year)
    print(series.poster_url)
    print(series.directors)
    print(series.actors)
    print(series.producer)
    print(series.country)
    print(series.age_rating)
    print(series.rating)
    print(series.seasons)

    input(f"\n{'=' * 40}\nENTER TO QUIT\n{'=' * 40}\n")
"""

"""
series = AniworldSeries("https://aniworld.to/anime/stream/highschool-dxd")
print(f"Testing Series: {series.title}")
print(f"Series URL: {series.url}")
print(f"Has movies: {series.has_movies}")
print(f"Number of seasons: {len(series.seasons)}")

print("\n--- Testing Seasons ---")
for i, season in enumerate(series.seasons, 1):
    print(f"\nSeason {i}:")
    print(f"  URL: {season.url}")
    # print(f"  Season Number: {season.season_number}")
    # print(f"  Episode Count: {season.episode_count}")
    # print(f"  Episodes: {len(season.episodes)} objects")
    if season.episodes:
        print(f"  First Episode: {season.episodes[0].title_de}")
        print(f"  First Episode: {season.episodes[0].language}")

"""

"""

TODO:
- Copy provider extractors from next
- Add .watch() .download() and .syncplay() function

"""

series = AniworldSeries("https://aniworld.to/anime/stream/highschool-dxd")

episode = series.seasons[0].episodes[0]

print(episode.url)
print(episode.title_de)
print(episode.provider_data)

result = episode.provider_link((Audio.JAPANESE, Subtitles.GERMAN), "Filemoon")
print(result)

print(episode._base_folder)
print(episode._folder_path)
print(episode._file_name)
print(episode._episode_path)

episode.download()
print(episode.is_downloaded)
