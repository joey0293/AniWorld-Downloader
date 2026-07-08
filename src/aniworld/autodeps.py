import os
import platform
import shutil
import subprocess
from pathlib import Path


class DependencyManager:
    """Manage binaries with package manager"""

    def __init__(self, app_name="AniWorld", deps=None, install_folder=None):
        """Initialize manager with deps and folder"""
        self.app_name = app_name
        self.deps = deps or {}
        self.install_folder = Path(
            install_folder
            or os.getenv("ANIWORLD_INSTALL_FOLDER", Path.home() / ".aniworld")
        )
        self.install_folder.mkdir(parents=True, exist_ok=True)

        from .config import logger

        logger.debug(f"Dependency folder: {self.install_folder}")

    def fetch_binary(self, name):
        from .config import logger

        """Fetch binary: system-wide -> aniworld folder -> install/download"""
        system = platform.system()
        binary_name = f"{name}.exe" if system == "Windows" else name

        # Check system-wide install
        sys_path = shutil.which(binary_name)
        if sys_path:
            logger.debug(f"{name} found system-wide at {sys_path}")
            return Path(sys_path)

        # Check .aniworld folder
        local_path = self.install_folder / binary_name
        if local_path.exists():
            logger.debug(f"{name} found in {self.install_folder}")
            return local_path

        # Install via package manager or download fallback
        # Package managers on Linux may install globally; return cached if exists
        if self._install_with_package_manager(name, system):
            if local_path.exists():
                return local_path
            sys_path_after = shutil.which(binary_name)
            if sys_path_after:
                return Path(sys_path_after)

        # Fallback download
        dep_info = self.deps.get(name, {}).get(system, {})
        url = dep_info.get("url")
        if url:
            logger.debug(f"Downloading {name} for {system} from {url}...")

            from .config import GLOBAL_SESSION

            r = GLOBAL_SESSION.get(url, stream=True)
            r.raise_for_status()
            with open(local_path, "wb") as f:
                shutil.copyfileobj(r.raw, f)
            if system != "Windows":
                local_path.chmod(0o755)
            logger.debug(f"{name} downloaded to {local_path}")
            return local_path

        raise RuntimeError(f"Cannot locate or install {name} for {system}.")

    def _install_with_package_manager(self, name, system):
        from .config import logger

        """Install binary via system package manager if available"""
        dep_info = self.deps.get(name, {}).get(system, {})
        pkg_name = dep_info.get("package")
        if not pkg_name:
            return False

        try:
            if system == "Windows":
                subprocess.run(
                    ["winget", "install", "-e", "--id", pkg_name, "-h"], check=True
                )
            elif system == "Darwin":
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
            logger.debug(f"{name} installed via package manager on {system}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.debug(f"Package manager failed for {name} on {system}: {e}")
            return False
