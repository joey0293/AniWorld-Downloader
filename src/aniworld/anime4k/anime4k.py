import os
import sys
import urllib.request
from pathlib import Path

try:
    from ..common import get_latest_github_release, unzip
    from ..config import ANIWORLD_CONFIG_DIR, logger
except ImportError:
    from aniworld.common import get_latest_github_release, unzip
    from aniworld.config import ANIWORLD_CONFIG_DIR, logger


def anime4k():
    """
    Download the latest Anime4K GLSL assets to ANIWORLD_CONFIG_DIR/Anime4K
    Automatically selects platform-specific files.
    """
    repo = "Tama47/Anime4K"
    release = get_latest_github_release(repo)

    # Define download URLs per platform
    urls = []
    if sys.platform.startswith("win"):
        urls = [
            f"https://github.com/{repo}/releases/download/{release}/GLSL_Windows_Low-end.zip",
            f"https://github.com/{repo}/releases/download/{release}/GLSL_Windows_High-end.zip",
        ]
    elif sys.platform.startswith("linux"):
        urls = [
            f"https://github.com/{repo}/releases/download/{release}/GLSL_Mac_Linux_Low-end.zip",
            f"https://github.com/{repo}/releases/download/{release}/GLSL_Mac_Linux_High-end.zip",
        ]
    elif sys.platform.startswith("darwin"):  # macOS
        urls = [
            f"https://github.com/{repo}/releases/download/{release}/GLSL_Mac_Linux_Low-end.zip",
            f"https://github.com/{repo}/releases/download/{release}/GLSL_Mac_Linux_High-end.zip",
        ]
    else:
        raise RuntimeError(f"Unsupported platform: {sys.platform}")

    # Create target directory
    target_dir = Path(ANIWORLD_CONFIG_DIR) / "Anime4K"
    target_dir.mkdir(parents=True, exist_ok=True)

    # Download and extract each file if not already done
    for url in urls:
        filename = Path(url).name
        extracted_dir = target_dir / filename.replace(".zip", "")

        if extracted_dir.exists():
            logger.debug(
                f"{extracted_dir} already exists, skipping download and extraction."
            )
            continue

        filepath = target_dir / filename
        logger.debug(f"Downloading {filename}...")
        urllib.request.urlretrieve(url, filepath)
        logger.debug(f"Anime4K assets downloaded to {target_dir}")

        unzip(filepath, extracted_dir)

        macosx_dir = extracted_dir / "__MACOSX"
        if macosx_dir.exists():
            os.rmdir(macosx_dir)

        os.remove(filepath)


if __name__ == "__main__":
    anime4k()
