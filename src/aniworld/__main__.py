# ========================
# Nuitka project configuration
# ========================

# Basic flags
# nuitka-project: --static-libpython=no
# nuitka-project: --follow-imports
# nuitka-project: --assume-yes-for-downloads
# nuitka-project: --python-flag=-m

# Include data files
# nuitka-project: --include-data-file=src/aniworld/.env.example=aniworld/.env.example
# nuitka-project: --include-data-file=src/aniworld/ascii/ASCII.txt=aniworld/ascii/ASCII.txt
# nuitka-project: --include-data-file=src/aniworld/aniskip/scripts/aniskip.lua=aniworld/aniskip/scripts/aniskip.lua
# nuitka-project: --include-data-file=src/aniworld/aniskip/scripts/autoexit.lua=aniworld/aniskip/scripts/autoexit.lua
# nuitka-project: --include-data-file=src/aniworld/aniskip/scripts/autostart.lua=aniworld/aniskip/scripts/autostart.lua

# Platform-specific flags
# nuitka-project-if: {OS} == "Darwin":
#    nuitka-project: --standalone
#    nuitka-project: --macos-create-app-bundle
#    nuitka-project: --macos-app-name=AniWorld
#    nuitka-project: --macos-app-icon=src/aniworld/nuitka/icon.webp

# nuitka-project-if: {OS} in ("Windows", "Linux", "FreeBSD"):
#    nuitka-project: --onefile
#    nuitka-project: --console=force
#    nuitka-project: --windows-icon-from-ico=src/aniworld/nuitka/icon.webp

# ========================
# Python entrypoint
# ========================

import sys

from .entry import aniworld

sys.exit(aniworld())
