import argparse
import logging
import os
import sys

from .anime4k import anime4k
from .config import ACTION_METHODS, LANG_LABELS, SUPPORTED_PROVIDERS, VERSION
from .logger import get_logger

logger = get_logger(__name__)

EXAMPLES = r"""

Command-Line Arguments Example

AniWorld Downloader provides command-line options for downloading and streaming anime without relying on the interactive menu.


Example 1: Download a Single Episode (default action)

To download episode 1 of "Demon Slayer: Kimetsu no Yaiba":

aniworld https://aniworld.to/anime/stream/demon-slayer-kimetsu-no-yaiba/staffel-1/episode-1


Example 2: Download Multiple Episodes (default action)

To download multiple episodes of "Demon Slayer":

aniworld \
  https://aniworld.to/anime/stream/demon-slayer-kimetsu-no-yaiba/staffel-1/episode-1 \
  https://aniworld.to/anime/stream/demon-slayer-kimetsu-no-yaiba/staffel-1/episode-2


Example 3: Watch Episodes with Aniskip

To watch an episode while skipping intros and outros:

aniworld --action Watch --aniskip \
  https://aniworld.to/anime/stream/demon-slayer-kimetsu-no-yaiba/staffel-1/episode-1


Example 4: Syncplay with Friends (+ Keep Watching)

To Syncplay a specific episode with friends:

aniworld --action Syncplay --keep-watching \
  --syncplay-host syncplay.pl:8998 \
  --syncplay-room "MyRoom" \
  --syncplay-username "phoenixthrush" \
  https://aniworld.to/anime/stream/demon-slayer-kimetsu-no-yaiba/staffel-1/episode-1


Language Options for Syncplay

You can select different languages for yourself and your friends:

For German Dub:
aniworld --action Syncplay --keep-watching --language "German Dub" --aniskip \
  --syncplay-host syncplay.pl:8998 --syncplay-room "MyRoom" --syncplay-username "phoenixthrush" \
  https://aniworld.to/anime/stream/demon-slayer-kimetsu-no-yaiba/staffel-1/episode-1

For English Sub:
aniworld --action Syncplay --keep-watching --language "English Sub" --aniskip \
  --syncplay-host syncplay.pl:8998 --syncplay-room "MyRoom" --syncplay-username "phoenixthrush" \
  https://aniworld.to/anime/stream/demon-slayer-kimetsu-no-yaiba/staffel-1/episode-1

To restrict access, set a password for the room:

aniworld --action Syncplay --keep-watching --language "English Sub" --aniskip \
  --syncplay-host syncplay.pl:8998 --syncplay-room "MyRoom" --syncplay-username "phoenixthrush" \
  --syncplay-password beans \
  https://aniworld.to/anime/stream/demon-slayer-kimetsu-no-yaiba/staffel-1/episode-1


Example 5: Download with Specific Provider and Language (default action)

To download using the VOE provider with English subtitles:

aniworld --provider VOE --language "English Sub" \
  https://aniworld.to/anime/stream/demon-slayer-kimetsu-no-yaiba/staffel-1/episode-1


Example 6: Use an Episode File (default action)

You can download episodes listed in a text file. Below is an example of a text file (test.txt):

# The whole anime
https://aniworld.to/anime/stream/alya-sometimes-hides-her-feelings-in-russian

# The whole Season 2
https://aniworld.to/anime/stream/demon-slayer-kimetsu-no-yaiba/staffel-2

# Only Season 3 Episode 13
https://aniworld.to/anime/stream/kaguya-sama-love-is-war/staffel-3/episode-13

To download the URLs specified in the file, use:

aniworld --episode-file test.txt --language "German Dub"


Example 7: Use a custom provider URL

Download a provider page URL directly (resolved to a direct media URL and saved via ffmpeg).
Important: you must specify --provider so the right extractor (and headers) are used.

aniworld --provider VOE --provider-url https://voe.sx/e/ayginbzzb6bi


Notes

- --aniskip and --keep-watching can be combined with Watch and Syncplay.
- URLs are positional arguments, so you can paste one or many at the end of the command.
"""


def parse_args():
    parser = argparse.ArgumentParser(
        prog="aniworld",
        description=(
            "AniWorld Downloader is a cross-platform tool for streaming and "
            "downloading anime from aniworld.to, as well as movies and series "
            "from s.to. It runs on Windows, macOS, and Linux, providing a "
            "seamless experience for offline viewing or instant playback."
        ),
        epilog=EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # =========================
    # General / Core options
    # =========================
    general = parser.add_argument_group("General Options")
    general.add_argument("--debug", action="store_true", help="Enable debug logging")
    general.add_argument(
        "--version",
        action="store_true",
        help="Show version information and exit",
    )
    general.add_argument(
        "--no-menu",
        action="store_true",
        help="Disable interactive menu",
    )

    # =========================
    # Playback / Download options
    # =========================
    playback = parser.add_argument_group("Playback & Download Options")
    playback.add_argument(
        "--action",
        choices=sorted(ACTION_METHODS.keys()),
        help="Choose action method",
    )
    playback.add_argument(
        "--language",
        choices=sorted(LANG_LABELS.values()),
        help="Choose language",
    )
    playback.add_argument(
        "--provider",
        choices=sorted(SUPPORTED_PROVIDERS),
        help="Choose provider",
    )

    playback.add_argument(
        "--aniskip",
        action="store_true",
        help="Skip intros/outros when watching (AniSkip integration)",
    )
    playback.add_argument(
        "--keep-watching",
        action="store_true",
        help="Automatically continue with the next episode",
    )

    # =========================
    # Discovery / Random
    # =========================
    discovery = parser.add_argument_group("Discovery Options")
    discovery.add_argument(
        "--random-anime",
        action="store_true",
        help="Fetch a random anime series",
    )

    # =========================
    # Anime4K
    # =========================
    a4k = parser.add_argument_group("Anime4K Options")
    a4k.add_argument(
        "--anime4k",
        choices=["High", "Low", "Remove"],
        help="Enable Anime4K upscaling with specified mode",
    )

    # =========================
    # Input sources
    # =========================
    inputs = parser.add_argument_group("Input Options")
    inputs.add_argument(
        "--episode-file",
        help="Path to a text file containing episode URLs (one URL per line)",
    )
    inputs.add_argument(
        "url",
        nargs="*",
        help="URLs of series, season, or episodes",
    )

    # =========================
    # Provider direct URL (custom)
    # =========================
    provider = parser.add_argument_group("Provider URL Options")
    provider.add_argument(
        "--provider-url",
        help="Custom provider URL",
    )

    # =========================
    # Syncplay (only meaningful with --action Syncplay)
    # =========================
    syncplay = parser.add_argument_group(
        "Syncplay Options (requires --action Syncplay)"
    )
    syncplay.add_argument(
        "--syncplay-host",
        help="Specify the Syncplay server host",
    )
    syncplay.add_argument(
        "--syncplay-room",
        help="Specify the Syncplay room name",
    )
    syncplay.add_argument(
        "--syncplay-username",
        help="Specify the Syncplay username",
    )
    syncplay.add_argument(
        "--syncplay-password",
        help="Specify the Syncplay password (if required)",
    )

    args = parser.parse_args()

    if args.language:
        os.environ["ANIWORLD_LANGUAGE"] = args.language

    if args.provider:
        os.environ["ANIWORLD_PROVIDER"] = args.provider

    if args.random_anime:
        os.environ["ANIWORLD_RANDOM_ANIME"] = "1"

    if args.no_menu:
        os.environ["ANIWORLD_NO_MENU"] = "1"

    if args.aniskip:
        os.environ["ANIWORLD_ANISKIP"] = "1"

    if args.keep_watching:
        os.environ["ANIWORLD_KEEP_WATCHING"] = "1"

    if args.anime4k:
        mode = args.anime4k.lower()
        logger.debug(f"Anime4K upscaling set to: {mode}")
        anime4k(mode)

    if args.debug:
        os.environ["ANIWORLD_DEBUG_MODE"] = "1"

        logging.getLogger().setLevel(logging.DEBUG)
        for name in logging.Logger.manager.loggerDict:
            logging.getLogger(name).setLevel(logging.DEBUG)

        logger.debug("Debug mode enabled")

    if args.action == "Syncplay":
        if args.syncplay_host:
            os.environ["ANIWORLD_SYNCPLAY_HOST"] = args.syncplay_host
        if args.syncplay_room:
            os.environ["ANIWORLD_SYNCPLAY_ROOM"] = args.syncplay_room
        if args.syncplay_username:
            os.environ["ANIWORLD_SYNCPLAY_USERNAME"] = args.syncplay_username
        if args.syncplay_password:
            os.environ["ANIWORLD_SYNCPLAY_PASSWORD"] = args.syncplay_password

    if args.episode_file:
        try:
            with open(args.episode_file, "r") as f:
                for line in f:
                    u = line.strip()
                    if u:
                        args.url.append(u)
            logger.debug(f"Loaded {len(args.url)} URLs from {args.episode_file}")
        except Exception as e:
            logger.error(f"Failed to read episode file: {e}")
            sys.exit(1)

    if args.provider_url and args.provider:
        import ffmpeg

        from .config import PROVIDER_HEADERS_D
        from .extractors import provider_functions

        provider_key = (args.provider or "").strip()
        headers = PROVIDER_HEADERS_D.get(provider_key, {})

        headers_str = "".join(f"{k}: {v}\r\n" for k, v in headers.items())

        direct_link = provider_functions[
            f"get_direct_link_from_{provider_key.lower()}"
        ](args.provider_url)

        download_dir = os.getenv("ANIWORLD_DOWNLOAD_PATH", ".")
        output_path = os.path.join(download_dir, "input.mkv")

        (
            ffmpeg.input(
                direct_link,
                headers=headers_str if headers_str else None,
            )
            .output(
                output_path,
                c="copy",
                f="matroska",
            )
            .run()
        )

        sys.exit(0)

    if args.version:
        # TODO: add logic
        is_newest_version = True
        latest_version = VERSION

        version_message = (
            "You are on the latest version."
            if is_newest_version
            else f"Your version is outdated.\nPlease update to the latest version (v.{latest_version})."
        )

        cowsay = Rf"""______________________________
< AniWorld-Downloader v.{VERSION} >
------------------------------
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||

{version_message}"""

        print(cowsay.strip())
        sys.exit(0)

    return args
