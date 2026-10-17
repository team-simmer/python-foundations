"""Check your work for Topic 9.1: uv and Python 3.13 are installed.

Run it from any folder with:
uv run --python 3.13 https://raw.githubusercontent.com/team-simmer/python-foundations/main/lesson-09/check_python.py

It only reads which Python is running it and which uv started it. It doesn't change anything.
"""

import os
import subprocess
import sys
from pathlib import Path

# The Python version the course pins. Change it here, in every check, in test_checks.py and in lesson-checks.yml.
PYTHON = "3.13"

def uv_version():
    """Return uv's version as a tuple of numbers, or None if this script wasn't started by uv."""
    uv = os.environ.get("UV")
    if not uv:
        return None
    try:
        output = subprocess.run([uv, "--version"], capture_output=True, text=True).stdout
    except OSError:
        return None
    # The output looks like: uv 0.13.1 (62faed335 2026-10-13 aarch64-apple-darwin)
    parts = output.split()
    if len(parts) < 2:
        return None
    return tuple(int(part) for part in parts[1].split(".") if part.isdigit())


def check_your_work():
    results = []

    version = uv_version()
    if version is None:
        results.append((False, "This script wasn't started by uv. Run it with the uv run command from the exercise, not with python."))
    elif version < (0, 13):
        shown = ".".join(str(part) for part in version)
        results.append((False, f"uv is version {shown}. The course uses 0.13 or newer. Update it with: uv self update"))
    else:
        shown = ".".join(str(part) for part in version)
        results.append((True, f"uv {shown} is installed."))

    running = f"{sys.version_info.major}.{sys.version_info.minor}"
    if running == PYTHON:
        results.append((True, f"Python {sys.version.split()[0]} is running this check."))
    else:
        results.append((False, f"Python {running} is running this check, not {PYTHON}. Install it with uv python install {PYTHON}, and keep --python {PYTHON} in the uv run command."))

    home = Path(sys.base_prefix)
    if home.name.startswith(f"cpython-{PYTHON}"):
        results.append((True, f"This Python {PYTHON} was installed by uv."))
    elif running == PYTHON:
        results.append((False, f"This Python {PYTHON} is at {home}, so it wasn't installed by uv. Run uv python install {PYTHON}, then run this check again."))

    for passed, message in results:
        print(("✅ " if passed else "❌ ") + message)
    if all(passed for passed, message in results):
        print(f"\nEverything matches. Python {PYTHON} and uv are ready for the next topic.")
    else:
        print("\nFix the first ❌, then run this check again.")


# A terminal that can't show ✅ and ❌ gets a ? instead of an error.
sys.stdout.reconfigure(errors="replace")
check_your_work()
