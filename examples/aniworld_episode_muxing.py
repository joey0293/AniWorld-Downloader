"""
Example: Episode Muxing

This example demonstrates how to download **all language variations**
for a single episode into one MKV file.

Important note:
- If you select subtitles, they will be burned into the video stream.
- That means the video has to be re-downloaded for each subtitle track.
"""

from aniworld.models import AniworldEpisode

url = "https://aniworld.to/anime/stream/my-life-as-inukai-sans-dog/staffel-1/episode-4"

# ----------------------------
# Language variations
# ----------------------------
variations = [
    ("German Dub", "VOE"),  # German audio, no subtitles
    ("English Sub", "VOE"),  # Japanese audio, English subtitles
    ("German Sub", "VOE"),  # Japanese audio, German subtitles
]

print("\nDownloading all available variations into a single MKV file...\n")

for language, provider in variations:
    print(f"Downloading: {language} via {provider}")

    episode = AniworldEpisode(
        url=url, selected_language=language, selected_provider=provider
    )

    # Download will mux everything into one MKV file
    episode.download()

print("\nDone!")
