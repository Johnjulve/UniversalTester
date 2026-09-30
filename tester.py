#!/usr/bin/env python
"""
UniversalTester (testx) Entrypoint.
Delegates execution to the modular cli package.
"""
import os
import sys

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if _CURRENT_DIR not in sys.path:
    sys.path.insert(0, _CURRENT_DIR)

from cli.main import main


if __name__ == "__main__":
    sys.exit(main())
