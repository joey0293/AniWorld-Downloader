import os
import shutil
import sys
from pathlib import Path

try:
    from ..common import get_latest_github_release, unzip
    from ..config import ANIWORLD_CONFIG_DIR, GLOBAL_SESSION, logger
except ImportError:
    from aniworld.common import get_latest_github_release, unzip
    from aniworld.config import ANIWORLD_CONFIG_DIR, GLOBAL_SESSION, logger


def get_anime4k_urls():
    """Return platform-specific Anime4K GLSL URLs."""
    repo = "Tama47/Anime4K"
    release = get_latest_github_release(repo)

    if sys.platform.startswith("win"):
        return [
            f"https://github.com/{repo}/releases/download/{release}/GLSL_Windows_Low-end.zip",
            f"https://github.com/{repo}/releases/download/{release}/GLSL_Windows_High-end.zip",
        ]
    elif sys.platform.startswith("linux") or sys.platform.startswith("darwin"):
        return [
            f"https://github.com/{repo}/releases/download/{release}/GLSL_Mac_Linux_Low-end.zip",
            f"https://github.com/{repo}/releases/download/{release}/GLSL_Mac_Linux_High-end.zip",
        ]
    else:
        raise RuntimeError(f"Unsupported platform: {sys.platform}")


def download_anime4k(target_dir=None):
    """Download Anime4K GLSL assets only if not already extracted."""
    target_dir = Path(target_dir or ANIWORLD_CONFIG_DIR) / "Anime4K"
    target_dir.mkdir(parents=True, exist_ok=True)

    urls = get_anime4k_urls()
    downloaded_files = []

    for url in urls:
        filename = Path(url).name
        extracted_dir = target_dir / Path(filename).stem  # folder after extraction

        # Skip download if extracted folder already exists
        if extracted_dir.exists():
            logger.debug(
                f"{extracted_dir} already exists, skipping download of {filename}."
            )
            downloaded_files.append(
                target_dir / filename
            )  # still include for extract_anime4k()
            continue

        # Download ZIP if extracted folder doesn't exist
        filepath = target_dir / filename
        logger.debug(f"Downloading {filename}...")
        with GLOBAL_SESSION.get(url, stream=True) as response:
            response.raise_for_status()
            with open(filepath, "wb") as f:
                shutil.copyfileobj(response.raw, f)
        logger.debug(f"Downloaded {filename} to {target_dir}")

        downloaded_files.append(filepath)

    return downloaded_files


def extract_anime4k(files, target_dir=None):
    """Extract downloaded zip files and clean up."""
    target_dir = Path(target_dir or ANIWORLD_CONFIG_DIR) / "Anime4K"

    extracted_dirs = []
    for filepath in files:
        extracted_dir = target_dir / filepath.stem
        if extracted_dir.exists():
            logger.debug(f"{extracted_dir} already exists, skipping extraction.")
        else:
            unzip(filepath, extracted_dir)
            macosx_dir = extracted_dir / "__MACOSX"
            if macosx_dir.exists():
                shutil.rmtree(macosx_dir)
            logger.debug(f"Extracted {filepath.name} to {extracted_dir}")
        filepath.unlink(missing_ok=True)
        extracted_dirs.append(extracted_dir)

    return extracted_dirs


# TODO: implement iina
def setup_anime4k():
    """
    Sets up Anime4K shaders and MPV configuration:
    - Copies shaders to MPV's shaders directory
    - Copies mpv.conf and input.conf from each extracted folder if they don't exist
    """

    # Determine MPV config path
    if sys.platform.startswith("win"):
        mpv_config_dir = Path(os.environ.get("APPDATA", "")) / "mpv"
    else:
        mpv_config_dir = Path.home() / ".config" / "mpv"

    mpv_shaders_dir = mpv_config_dir / "shaders"
    mpv_shaders_dir.mkdir(parents=True, exist_ok=True)

    # Source extracted Anime4K folders
    source_dir = Path(ANIWORLD_CONFIG_DIR) / "Anime4K"
    if not source_dir.exists():
        raise FileNotFoundError(
            f"{source_dir} does not exist. Run download/extract first."
        )

    for extracted_folder in source_dir.iterdir():
        if extracted_folder.is_dir():
            # Copy shaders
            shaders_dir = extracted_folder / "shaders"
            if shaders_dir.exists():
                for shader_file in shaders_dir.iterdir():
                    dst_file = mpv_shaders_dir / shader_file.name
                    if dst_file.exists():
                        logger.debug(f"{dst_file} already exists, skipping copy.")
                        continue
                    shutil.copy(shader_file, dst_file)
                    logger.debug(f"Copied shader {shader_file} to {dst_file}")

            # Copy config files
            for conf_file_name in ("mpv.conf", "input.conf"):
                src_conf_file = extracted_folder / conf_file_name
                dst_conf_file = mpv_config_dir / conf_file_name
                if src_conf_file.exists():
                    if dst_conf_file.exists():
                        logger.debug(f"{dst_conf_file} already exists, skipping copy.")
                    else:
                        shutil.copy(src_conf_file, dst_conf_file)
                        logger.info(f"Copied {src_conf_file} to {dst_conf_file}")
                else:
                    logger.debug(f"{src_conf_file} does not exist, skipping.")

    logger.info(f"Anime4K setup complete in {mpv_config_dir}")


def aniskip():
    downloaded_files = download_anime4k()
    extract_anime4k(downloaded_files)
    setup_anime4k()


if __name__ == "__main__":
    aniskip()
