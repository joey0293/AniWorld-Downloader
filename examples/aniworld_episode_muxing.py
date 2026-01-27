from aniworld.models import AniworldEpisode

url = "https://aniworld.to/anime/stream/my-life-as-inukai-sans-dog/staffel-1/episode-3"

# German Dub: means Audio.GERMAN + Subtitles.NONE
# AniworldEpisode(url, selected_language="German Dub", selected_provider="VOE").download()

# German Sub: means Audio.JAPANESE + Subtitles.GERMAN
# TODO: fix this downloads audio first then video but should download once
AniworldEpisode(url, selected_language="German Sub", selected_provider="VOE").download()

# English Sub: means Audio.JAPANESE + Subtitles.ENGLISH
AniworldEpisode(
    url, selected_language="English Sub", selected_provider="VOE"
).download()
