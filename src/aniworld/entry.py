from .models import AniworldSeries, Audio, Subtitles
from .arguments import parse_args
from .logger import get_logger

logger = get_logger(__name__)


def aniworld():
    args = parse_args()

    logger.debug(f"Fetching series from URL: {args.url}")
    series = AniworldSeries(args.url)

    episode = series.seasons[0].episodes[0]

    print(episode.url)
    print(episode.title_de)
    print(episode.provider_data)

    result = episode.provider_link((Audio.JAPANESE, Subtitles.GERMAN), "Filemoon")
    print(result)


if __name__ == "__main__":
    aniworld()
