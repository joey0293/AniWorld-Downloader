from aniworld.models import SerienstreamSeason

season_url = "https://serienstream.to/serie/american-horror-story-die-dunkle-seite-in-dir/staffel-1"

season = SerienstreamSeason(season_url)

print("=== SEASON INFO ===")
print(f"Season URL: {season.url}")
print(f"Series Title: {season.series.title}")
print(f"Season Number: {season.season_number}")
print(f"Episode Count: {season.episode_count}")
print(f"Episodes: {season.episodes}")

season.download()
