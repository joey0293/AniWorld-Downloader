# from .models import AniworldSeries, Audio, Subtitles
from .arguments import parse_args
from .logger import get_logger
from .menu import app

logger = get_logger(__name__)


def aniworld():
    args = parse_args()

    app()


if __name__ == "__main__":
    aniworld()
