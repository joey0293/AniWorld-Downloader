from aniworld.models import AniworldSeries

series = AniworldSeries("https://aniworld.to/anime/stream/kaguya-sama-love-is-war")

print("\n" + "=" * 60)
print(f"SEASON OVERVIEW — {series.title}")
print("=" * 60)

for season in series.seasons:
    fields = {
        "URL": season.url,
        "Are Movies": season.are_movies,
        "Season Number": season.season_number,
        "Episode Count": season.episode_count,
        "Episodes": season.episodes,
    }

    if season.are_movies:
        print("\nMovies")
    else:
        print(f"\nSeason {season.season_number}")

    print("-" * 60)

    max_key_len = max(len(k) for k in fields.keys())
    for key, value in fields.items():
        print(f"{key:<{max_key_len}} : {value}")

    """
    # Show first episode if available
    if season.episodes:
        ep = season.episodes[0]

        print("\n  First Episode")
        print("  " + "-" * 56)

        ep_fields = {
            "URL": ep.url,
            "Title DE": ep.title_de,
            "Title EN": ep.title_en,
            "Episode #": ep.episode_number,
            "Language": ep.language,
            "Is Movie": ep.is_movie,
        }

        max_ep_key_len = max(len(k) for k in ep_fields.keys())
        for key, value in ep_fields.items():
            print(f"  {key:<{max_ep_key_len}} : {value}")

    print("\n" + "-" * 60)
    """

print("\n" + "=" * 60 + "\n")
