import logging
import random
import re
import time
import warnings
from urllib.parse import urljoin

import niquests
from urllib3.exceptions import InsecureRequestWarning

warnings.simplefilter("ignore", InsecureRequestWarning)

DOODSTREAM_BASE_URL = "https://dood.li"
RANDOM_STRING_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
PASS_MD5_PATTERN = r"\$\.get\('([^']*\/pass_md5\/[^']*)'"
TOKEN_PATTERN = r"token=([a-zA-Z0-9]+)"


def _get_headers() -> dict:
    """Return headers for Doodstream requests."""
    return {
        "User-Agent": "Mozilla/5.0 (Android 15; Mobile; rv:132.0) Gecko/132.0 Firefox/132.0",
        "Referer": f"{DOODSTREAM_BASE_URL}/",
    }


def _extract_regex(pattern: str, content: str, name: str, url: str) -> str:
    """Extract a regex match or raise ValueError."""
    match = re.search(pattern, content)
    if not match:
        raise ValueError(f"{name} not found in {url}")
    return match.group(1)


def _generate_random_string(length: int = 10) -> str:
    """Generate a random alphanumeric string."""
    return "".join(random.choices(RANDOM_STRING_CHARS, k=length))


def get_direct_link_from_doodstream(embed_url: str) -> str:
    """
    Extract direct video link from a Doodstream embed URL using niquests (sync).

    Args:
        embed_url: Doodstream embed URL.

    Returns:
        Direct video link.
    """
    if not embed_url:
        raise ValueError("Embed URL cannot be empty")

    logging.info(f"Extracting direct link from: {embed_url}")
    headers = _get_headers()

    # Fetch embed page synchronously
    logging.debug("Fetching embed page content...")
    response = niquests.get(embed_url, headers=headers, verify=False)
    text = response.text

    # Extract pass_md5 URL and token
    pass_md5_url = _extract_regex(PASS_MD5_PATTERN, text, "pass_md5 URL", embed_url)
    if not pass_md5_url.startswith("http"):
        pass_md5_url = urljoin(DOODSTREAM_BASE_URL, pass_md5_url)

    token = _extract_regex(TOKEN_PATTERN, text, "token", embed_url)

    # Get video base URL
    logging.debug("Fetching video base URL from pass_md5 endpoint...")
    md5_response = niquests.get(pass_md5_url, headers=headers, verify=False)
    video_base_url = md5_response.text.strip()
    if not video_base_url:
        raise ValueError(f"Empty video base URL from {pass_md5_url}")

    # Build final direct link
    random_string = _generate_random_string(10)
    expiry = int(time.time())
    direct_link = f"{video_base_url}{random_string}?token={token}&expiry={expiry}"

    logging.info("Successfully extracted Doodstream direct link")
    return direct_link


def get_preview_image_link_from_doodstream(embed_url: str) -> str:
    pass


if __name__ == "__main__":
    # Tested on 2026/01 -> WORKING
    # logging.basicConfig(level=logging.DEBUG)
    try:
        # https://doodsearch.site
        link = input("Enter Doodstream Link: ").strip()
        if not link:
            print("Error: No link provided")
            exit(1)

        result = get_direct_link_from_doodstream(link)
        print(f"mpv --http-header-fields='Referer: https://dood.li/' '{result}'")

    except Exception as err:
        print(f"Error: {err}")
        exit(1)
