import re

import niquests

# Precompiled regex patterns
FILE_LINK_PATTERN = re.compile(r'file:\s*"(https?://[^"]+)"')
IMAGE_LINK_PATTERN = re.compile(r'image\s*:\s*"([^"]+\.jpg)"')

# Fixed headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Android 15; Mobile; rv:132.0) Gecko/132.0 Firefox/132.0"
}


def _fetch_page(url: str) -> str:
    """Fetch HTML content of a page using niquests synchronously."""
    try:
        response = niquests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.text
    except Exception as e:
        raise ValueError(f"Failed to fetch page {url}: {e}") from e


def get_direct_link_from_vidmoly(embed_url: str) -> str:
    """
    Extract direct video link from Vidmoly embed page using only regex.
    """
    html = _fetch_page(embed_url)

    match = FILE_LINK_PATTERN.search(html)
    if match:
        return match.group(1)

    raise ValueError("No direct video link found in Vidmoly page.")


def get_preview_image_link_from_vidmoly(embed_url: str) -> str:
    """
    Extract preview image URL from Vidmoly embed page using only regex.
    """
    html = _fetch_page(embed_url)

    match = IMAGE_LINK_PATTERN.search(html)
    if match:
        return match.group(1)

    raise ValueError("No preview image found in Vidmoly page.")


if __name__ == "__main__":
    # Tested on 2026/01 -> NOT WORKING
    # https://vidmoly.net/embed-px1a5pm0f0e8.html

    # logging.basicConfig(level=logging.DEBUG)

    link = input("Enter Vidmoly Link: ").strip()
    if not link:
        print("Error: No link provided")
        exit(1)

    print('Note: --referer "https://vidmoly.to"')

    try:
        direct_link = get_direct_link_from_vidmoly(link)
        video_link = direct_link
        preview_link = direct_link
        print("Direct link:", video_link)
        print("Preview image:", preview_link)
    except ValueError as e:
        print("Error:", e)
