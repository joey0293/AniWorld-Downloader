from aniworld.models import SerienstreamEpisode

episode_url = "https://serienstream.to/serie/american-horror-story-die-dunkle-seite-in-dir/staffel-1/episode-1"

episode = SerienstreamEpisode(episode_url)

print("=== EPISODE INFO ===")
print(f"Episode URL: {episode.url}")
print(f"Series: {episode.series}")
print(f"Season: {episode.season}")
print(f"Title DE: {episode.title_de}")
print(f"Title EN: {episode.title_en}")
print(f"Episode Number: {episode.episode_number}")
print(f"Provider Data: {episode.provider_data}")
print(f"Selected Path: {episode.selected_path}")
print(f"Selected Language: {episode.selected_language}")
print(f"Selected Provider: {episode.selected_provider}")
print(f"Redirect URL: {episode.redirect_url}")
print(f"Provider URL: {episode.provider_url}")
print(f"Stream URL: {episode.stream_url}")
print(f"Base Folder: {episode._base_folder}")
print(f"Folder Path: {episode._folder_path}")
print(f"File Name: {episode._file_name}")
print(f"File Extension: {episode._file_extension}")
print(f"Episode Path: {episode._episode_path}")
print(f"Is Downloaded: {episode.is_downloaded}")
