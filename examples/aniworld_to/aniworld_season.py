"""
Example: AniWorld Season usage

This example demonstrates:
- Loading a series
- Iterating seasons
- Accessing season metadata
- Inspecting episode objects inside a season
- Downloading / Watching / Syncplaying a whole season
"""

from aniworld.models import AniworldSeries

# ----------------------------
# 1. Load the series
# ----------------------------
series_url = "https://aniworld.to/anime/stream/highschool-dxd"
series = AniworldSeries(series_url)

print("\n" + "=" * 60)
print(f"SEASON OVERVIEW — {series.title}")
print("=" * 60)

# ----------------------------
# 2. Iterate all seasons
# ----------------------------
for season in series.seasons:
    # Basic season metadata
    print("\n" + "-" * 60)
    if season.are_movies:
        print("MOVIES")
    else:
        print(f"SEASON {season.season_number}")

    print("-" * 60)

    print("Season URL       :", season.url)
    print("Is movie season  :", season.are_movies)
    print("Season number    :", season.season_number)
    print("Episode count    :", season.episode_count)
    print("Episodes objects :", len(season.episodes))

    # ----------------------------
    # 3. Print episode overview
    # ----------------------------
    if season.episodes:
        print("\nEpisodes:")
        for ep in season.episodes:
            print(f"  #{ep.episode_number:02d} - {ep.title_en} / {ep.title_de}")

    # ----------------------------
    # 4. Detailed first episode (optional)
    # ----------------------------
    if season.episodes:
        ep = season.episodes[0]
        print("\nFirst episode details:")
        print("  URL           :", ep.url)
        print("  Title (DE)    :", ep.title_de)
        print("  Title (EN)    :", ep.title_en)
        print("  Episode       :", ep.episode_number)
        print("  Is movie      :", ep.is_movie)
        print("  Is downloaded :", ep.is_downloaded["exists"])

    print("\n" + "-" * 60)

print("\n" + "=" * 60 + "\n")

# ----------------------------
# 5. Optional: download / watch / syncplay
# ----------------------------
# Uncomment to enable:
# season.download()
# season.watch()
# season.syncplay()
