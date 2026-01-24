import os
import re
import shutil
import subprocess
from pathlib import Path

PLATFORM = "Windows"  # override platform.system() for development/testing

try:
    from .config import GLOBAL_SESSION
    from .logger import get_logger
except ImportError:
    from aniworld.config import GLOBAL_SESSION
    from aniworld.logger import get_logger


# -----------------------------
# Helpers
# -----------------------------
def _find_github_asset_url(assets, pattern):
    """Helper to find the first asset URL matching the given regex pattern"""
    for asset in assets:
        url = asset.get("browser_download_url")
        if url and pattern.search(url):
            return url
    return None


def _get_github_release_assets(api_url):
    """Fetch release assets from a GitHub API URL"""
    resp = GLOBAL_SESSION.get(api_url)
    resp.raise_for_status()
    return resp.json().get("assets", [])


# -----------------------------
# MPV
# -----------------------------
def get_mpv_release_urls():
    """Fetch URLs for the latest Windows MPV releases (v3 and non-v3)."""
    api_url = (
        "https://api.github.com/repos/shinchiro/mpv-winbuild-cmake/releases/latest"
    )
    assets = _get_github_release_assets(api_url)

    v3_pattern = re.compile(r"mpv-x86_64-v3-\d{8}-git-[a-f0-9]+\.7z$", re.IGNORECASE)
    non_v3_pattern = re.compile(
        r"mpv-x86_64-(?!v3-)\d{8}-git-[a-f0-9]+\.7z$", re.IGNORECASE
    )

    return _find_github_asset_url(assets, v3_pattern), _find_github_asset_url(
        assets, non_v3_pattern
    )


def get_mpv_windows_url():
    """Get Windows MPV URL (currently non-v3 by default)."""
    return get_mpv_release_urls()[1]  # TODO: add config to choose v3 vs non-v3


# -----------------------------
# Syncplay
# -----------------------------
def get_syncplay_release_url():
    """Fetch the URL for the latest Windows Syncplay portable ZIP release."""
    api_url = "https://api.github.com/repos/Syncplay/syncplay/releases/latest"
    assets = _get_github_release_assets(api_url)

    portable_pattern = re.compile(
        r"Syncplay[_-]\d+(?:\.\d+)*_Portable\.zip$", re.IGNORECASE
    )
    return _find_github_asset_url(assets, portable_pattern)


def get_syncplay_windows_url():
    """Get Windows Syncplay URL"""
    return get_syncplay_release_url()


# -----------------------------
# Dependencies
# -----------------------------
deps = {
    "mpv": {
        "Windows": {"package": "mpv.net", "url": None},
        "Linux": {"package": "mpv"},
        "Darwin": {"package": "mpv"},
    },
    "syncplay": {
        "Windows": {"package": "Syncplay.Syncplay", "url": None},
        "Linux": {"package": "syncplay"},
        "Darwin": {"package": "syncplay"},
    },
    "iina": {"Darwin": {"package": "iina"}},
    "7z": {"Windows": {"url": "https://7-zip.org/a/7zr.exe"}},
}


# -----------------------------
# Dependency Manager
# -----------------------------
# TODO: I dont like this
# TODO: currently only downloads 7z
class DependencyManager:
    """Manage binaries with system package manager or direct download."""

    def __init__(self, install_folder=None):
        self.deps = deps
        self.install_folder = Path(
            install_folder
            or os.getenv(
                "ANIWORLD_INSTALL_FOLDER", Path.home() / ".aniworld"
            )  # TODO: .aniworld/<package_name>/<package_name>.exe
        )
        self.install_folder.mkdir(parents=True, exist_ok=True)

        self.logger = get_logger(__name__)
        self.logger.debug(f"Dependency folder: {self.install_folder}")

    def fetch_binary(self, name):
        """Fetch binary: system-wide -> local folder -> package manager -> download"""
        dep_info = self.deps.get(name, {}).get(PLATFORM, {})
        url = dep_info.get("url")

        # Lazy resolution for MPV Windows URL
        if name == "mpv" and PLATFORM == "Windows" and not url:
            url = get_mpv_windows_url()
            dep_info["url"] = url  # cache it

        if not url:
            raise RuntimeError(f"Cannot locate or install {name} for {PLATFORM}.")

        # Derive filename from URL extension instead of hardcoding
        file_name = Path(url).name
        local_path = self.install_folder / file_name

        # Check system-wide install (only for known binaries with standard names)
        sys_path = shutil.which(name)
        if sys_path:
            self.logger.debug(f"{name} found system-wide at {sys_path}")
            return Path(sys_path)

        # Check local folder
        if local_path.exists():
            self.logger.debug(f"{name} found in {self.install_folder}")
            return local_path

        # Try package manager
        if self._install_with_package_manager(name):
            if local_path.exists():
                return local_path
            sys_path_after = shutil.which(name)
            if sys_path_after:
                return Path(sys_path_after)

        # Download fallback
        self.logger.debug(f"Downloading {name} for {PLATFORM} from {url}...")
        resp = GLOBAL_SESSION.get(url, stream=True)
        resp.raise_for_status()

        with open(local_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        if PLATFORM != "Windows":
            local_path.chmod(0o755)

        self.logger.debug(f"{name} downloaded to {local_path}")
        return local_path

    def _install_with_package_manager(self, name):
        """Install binary via system package manager if available."""
        dep_info = self.deps.get(name, {}).get(PLATFORM, {})
        pkg_name = dep_info.get("package")
        if not pkg_name:
            return False

        try:
            if PLATFORM == "Windows":
                subprocess.run(
                    ["winget", "install", "-e", "--id", pkg_name, "-h"], check=True
                )
            elif PLATFORM == "Darwin":
                subprocess.run(["brew", "install", pkg_name], check=True)
            else:
                if shutil.which("apt"):
                    subprocess.run(["sudo", "apt", "update"], check=True)
                    subprocess.run(
                        ["sudo", "apt", "install", "-y", pkg_name], check=True
                    )
                elif shutil.which("pacman"):
                    subprocess.run(["sudo", "pacman", "-Sy", pkg_name], check=True)
                else:
                    return False

            self.logger.debug(f"{name} installed via package manager on {PLATFORM}")
            return True

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.debug(f"Package manager failed for {name} on {PLATFORM}: {e}")
            return False


def get_player_path():
    manager = DependencyManager()
    use_iina = os.getenv("ANIWORLD_USE_IINA") == "1"
    use_aniskip = os.getenv("ANIWORLD_USE_ANISKIP") == "1"

    if PLATFORM == "Darwin" and use_iina and not use_aniskip:
        return manager.fetch_binary("iina")

    return manager.fetch_binary("mpv")


# TODO: implement syncplay instead of mpv
def get_syncplay_path():
    manager = DependencyManager()
    return manager.fetch_binary("mpv")


# -----------------------------
# Testing
# -----------------------------
if __name__ == "__main__":
    print(get_player_path())
    print(get_syncplay_path())
