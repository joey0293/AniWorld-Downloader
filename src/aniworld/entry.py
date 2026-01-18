# from .models import AniworldSeries, Audio, Subtitles
from .arguments import parse_args
from .logger import get_logger
from .menu import app
from .search import search

logger = get_logger(__name__)
logger.debug("")


def aniworld():
    args = parse_args()

    if args.url:
        url = args.url
    else:
        url = search()

    app(url=url)


if __name__ == "__main__":
    aniworld()
