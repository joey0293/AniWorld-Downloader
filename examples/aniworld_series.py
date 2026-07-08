from aniworld.models import AniworldSeries

series = AniworldSeries("https://aniworld.to/anime/stream/highschool-dxd")

print("\n" + "=" * 60)
print(f"SERIES OVERVIEW — {series.title}")
print("=" * 60 + "\n")

fields = {
    "URL": series.url,
    "Title": series.title,
    "Description": series.description[:30],
    "Genres": ", ".join(series.genres),
    "Release Years": series.release_year,
    "Poster URL": series.poster_url,
    "Directors": ", ".join(series.directors),
    "Actors": ", ".join(series.actors) + " ...",
    "Producer": series.producer,
    "Country": series.country,
    "Age Rating": series.age_rating,
    "Rating": series.rating,
    "Has Movies": series.has_movies,
    "Season Count": series.season_count,
}

max_key_len = max(len(k) for k in fields.keys())
for key, value in fields.items():
    print(f"{key:<{max_key_len}} : {value}")

print("\n" + "-" * 60)
print("SEASONS")
print("-" * 60)

for i, season in enumerate(series.seasons, 1):
    if season.are_movies:
        print("\nMovies:")
    else:
        print(f"\nSeason {i}:")

    print(f"  URL: {season.url}")
    print(f"  Episodes: {season.episode_count}")

print("\n" + "=" * 60)
