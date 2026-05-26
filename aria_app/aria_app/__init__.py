import os
import sys

# Make `src/` importable (workflows, agents, utils live there).
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SRC = os.path.join(_PROJECT_ROOT, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from .aria_app import app  # noqa: E402,F401
