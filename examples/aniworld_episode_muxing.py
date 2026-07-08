from aniworld.models import AniworldEpisode

url = "https://aniworld.to/anime/stream/my-life-as-inukai-sans-dog/staffel-1/episode-4"

# German Dub: means Audio.GERMAN + Subtitles.NONE
AniworldEpisode(url, selected_language="German Dub", selected_provider="VOE").download()

# German Sub: means Audio.JAPANESE + Subtitles.GERMAN
AniworldEpisode(url, selected_language="German Sub", selected_provider="VOE").download()

# English Sub: means Audio.JAPANESE + Subtitles.ENGLISH
AniworldEpisode(
    url, selected_language="English Sub", selected_provider="VOE"
).download()
