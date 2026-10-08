"""Allow ``python -m gh_pages_sync`` and serve as the PyInstaller entry point."""

import sys

from gh_pages_sync.cli import main

if __name__ == "__main__":
    sys.exit(main())