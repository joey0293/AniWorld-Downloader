"""
Example: AniWorld Series usage

This example demonstrates:
- Loading a series
- Inspecting series metadata
- Listing seasons and episode counts
- Showing a sample episode
- Download / Watch / Syncplay
"""

from aniworld.models import AniworldSeries

# ----------------------------
# 1. Load the series
# ----------------------------
series_url = "https://aniworld.to/anime/stream/highschool-dxd"
series = AniworldSeries(series_url)

print("\n" + "=" * 60)
print(f"SERIES OVERVIEW — {series.title}")
print("=" * 60 + "\n")

# ----------------------------
# 2. Series metadata
# ----------------------------
fields = {
    "URL": series.url,
    "Title": series.title,
    "Description": series.description,
    "Genres": ", ".join(series.genres),
    "Release Years": series.release_year,
    "Poster URL": series.poster_url,
    "Directors": ", ".join(series.directors),
    "Actors": ", ".join(series.actors),
    "Producer": series.producer,
    "Country": series.country,
    "Age Rating": series.age_rating,
    "Rating": series.rating,
    "IMDb": getattr(series, "imbd", None),
    "Has Movies": series.has_movies,
    "Season Count": series.season_count,
}

max_key_len = max(len(k) for k in fields.keys())
for key, value in fields.items():
    print(f"{key:<{max_key_len}} : {value}")

print("\n" + "-" * 60)
print("SEASONS")
print("-" * 60)

# ----------------------------
# 3. Season listing
# ----------------------------
for season in series.seasons:
    if season.are_movies:
        label = "Movies"
    else:
        label = f"Season {season.season_number}"

    print(f"\n{label}")
    print(f"  URL       : {season.url}")
    print(f"  Episodes  : {season.episode_count}")

    # show first episode as a sample
    if season.episodes:
        ep = season.episodes[0]
        print("  First episode:")
        print(f"    #{ep.episode_number} - {ep.title_en} / {ep.title_de}")

print("\n" + "=" * 60)

# ----------------------------
# 4. Optional actions
# ----------------------------
# Uncomment to enable:
# series.download()
# series.watch()
# series.syncplay()
