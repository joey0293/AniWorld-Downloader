import base64
import binascii
import json
import re
from typing import Any, Dict, Optional

import niquests

# Precompiled regex patterns
REDIRECT_PATTERN = re.compile(r"https?://[^'\"<>]+")
B64_PATTERN = re.compile(r"var a168c='([^']+)'")
HLS_PATTERN = re.compile(r"'hls': '(?P<hls>[^']+)'")

# Junk replacement patterns
JUNK_PARTS = ["@$", "^^", "~@", "%?", "*~", "!!", "#&"]

# Fixed User-Agent
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Android 15; Mobile; rv:132.0) Gecko/132.0 Firefox/132.0"
}


def shift_letters(input_str: str) -> str:
    """Apply ROT13 to letters."""
    result = []
    for c in input_str:
        code = ord(c)
        if 65 <= code <= 90:  # Uppercase
            code = (code - 65 + 13) % 26 + 65
        elif 97 <= code <= 122:  # Lowercase
            code = (code - 97 + 13) % 26 + 97
        result.append(chr(code))
    return "".join(result)


def replace_junk(input_str: str) -> str:
    """Replace junk patterns with underscores."""
    for part in JUNK_PARTS:
        input_str = input_str.replace(part, "_")
    return input_str


def shift_back(s: str, n: int) -> str:
    """Shift characters back by n."""
    return "".join(chr(ord(c) - n) for c in s)


def decode_voe_string(encoded: str) -> Dict[str, Any]:
    """Decode VOE encoded string."""
    try:
        step1 = shift_letters(encoded)
        step2 = replace_junk(step1).replace("_", "")
        step3 = base64.b64decode(step2).decode()
        step4 = shift_back(step3, 3)
        step5 = base64.b64decode(step4[::-1]).decode()
        return json.loads(step5)
    except (binascii.Error, json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ValueError(f"Failed to decode VOE string: {e}") from e


def _fetch_page(url: str) -> str:
    """Fetch HTML page synchronously using niquests."""
    try:
        response = niquests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.text
    except Exception as e:
        raise ValueError(f"Failed to fetch page {url}: {e}") from e


def extract_voe_from_script(html: str) -> Optional[str]:
    """Extract VOE source URL from embedded script in HTML."""
    script_match = re.search(
        r'<script[^>]+type="application/json">(.+?)</script>', html, re.DOTALL
    )
    if script_match:
        content = script_match.group(1)
        # Remove possible leading/trailing chars
        content = content[2:-2] if len(content) > 4 else content
        try:
            decoded = decode_voe_string(content)
            return decoded.get("source")
        except ValueError:
            return None
    return None


def get_direct_link_from_voe(embed_url: str) -> str:
    """Extract direct video link from VOE embed page."""
    html = _fetch_page(embed_url)

    # Step 1: Find redirect URL
    redirect_match = REDIRECT_PATTERN.search(html)
    if not redirect_match:
        raise ValueError("No redirect URL found in VOE response.")

    redirect_url = redirect_match.group(0)
    html_redirect = _fetch_page(redirect_url)

    # Step 2: Try extraction from script
    extracted = extract_voe_from_script(html_redirect)
    if extracted:
        return extracted

    # Step 3: Try base64 encoded variable
    b64_match = B64_PATTERN.search(html_redirect)
    if b64_match:
        try:
            decoded = base64.b64decode(b64_match.group(1)).decode()[::-1]
            source = json.loads(decoded).get("source")
            if source:
                return source
        except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError):
            pass

    # Step 4: Try HLS extraction
    hls_match = HLS_PATTERN.search(html_redirect)
    if hls_match:
        try:
            return base64.b64decode(hls_match.group("hls")).decode()
        except (binascii.Error, UnicodeDecodeError):
            pass

    raise ValueError("No video source found using any extraction method.")


def get_preview_image_link_from_voe(embed_url: str) -> str:
    """Extract VOE preview image from the embed page."""
    html = _fetch_page(embed_url)

    redirect_match = REDIRECT_PATTERN.search(html)
    if not redirect_match:
        raise ValueError("No redirect URL found in VOE response.")

    redirect_url = redirect_match.group(0)
    # Construct storyboard image URL
    image_url = f"{redirect_url.replace('/e/', '/cache/')}_storyboard_L2.jpg"

    # Check if image is reachable
    try:
        head_resp = niquests.head(image_url, headers=HEADERS)
        head_resp.raise_for_status()
        if "image" in head_resp.headers.get("Content-Type", ""):
            return image_url
    except Exception as e:
        raise ValueError(f"Preview image not reachable: {e}") from e

    raise ValueError("Preview image not found or not reachable.")


if __name__ == "__main__":
    # Tested on 2026/01 -> NOT WORKING
    # https://voe.sx/e/ayginbzzb6bi

    # logging.basicConfig(level=logging.DEBUG)

    link = input("Enter VOE Link: ").strip()
    if not link:
        print("Error: No link provided")
        exit(1)

    try:
        direct_link = get_direct_link_from_voe(link)
        print("=" * 25)

        print("Direct link:", direct_link)
        print("=" * 25)

        print("Preview image:", direct_link)
        print("=" * 25)

        print(
            f'mpv --http-header-fields=User-Agent: "Mozilla/5.0 (Android 15; Mobile; rv:132.0) Gecko/132.0 Firefox/132.0" "{direct_link}"'
        )

        print("=" * 25)
    except ValueError as e:
        print("Error:", e)
