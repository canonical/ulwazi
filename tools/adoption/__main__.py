"""Run the adoption tool with ``python -m tools.adoption``."""

import sys

from tools.adoption.cli import main

if __name__ == "__main__":
    sys.exit(main())
