"""Download a lesson 10 workbook and its data files into the project you run this in.

Run it in the exercise's project folder, with uv run and the exercise's name, as the topic page shows:

    uv run https://raw.githubusercontent.com/team-simmer/python-foundations/main/lesson-10/get_files.py 10.1

It downloads the workbook from Simmer's GitHub repository into the folder, and the data files from the
course's data store into a folder called data. It never replaces a file that's already there, so your
work is safe if you run it again, and it doesn't change anything else.
"""

import os
import sys
import tomllib
import urllib.request
from pathlib import Path

# Where the workbooks are. Simmer's tests set SIMMER_WORKBOOKS to test a new version before it's published.
WORKBOOKS = os.environ.get("SIMMER_WORKBOOKS", "https://raw.githubusercontent.com/team-simmer/python-foundations/main/lesson-10").rstrip("/")
DATA = "https://storage.googleapis.com/simmer-python-course-data/simmer-store/v1"

# The exercise's name: (the project it's done in, the workbook, the data files)
EXERCISES = {
    "10.1": ("referral-report", "10.1-source-medium.ipynb", ["sessions_export_2024_02.csv"]),
    "10.2": ("referral-report", "10.2-referral-hostnames.ipynb", ["sessions_export_2024_04.csv"]),
    "10.3": ("referral-report", "10.3-new-campaigns.ipynb", ["sessions_export_2025_02.csv", "sessions_export_2025_03.csv"]),
    "final": ("campaign-tools", "channel_report.ipynb", ["sessions_export_2024_01.csv"]),
}
USAGE = "Usage: uv run https://raw.githubusercontent.com/team-simmer/python-foundations/main/lesson-10/get_files.py EXERCISE\nEXERCISE is 10.1, 10.2, 10.3 or final."


def download(url, path):
    """Download url to path, unless the file is already there. Return what was done."""
    if path.exists():
        return f"Already there, not replaced: {path.relative_to(Path.cwd())}"
    path.parent.mkdir(exist_ok=True)
    partial = path.with_name(path.name + ".part")
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            partial.write_bytes(response.read())
    except OSError as error:
        partial.unlink(missing_ok=True)
        sys.exit(f"❌ Couldn't download {url}: {error}\n   Check your internet connection and run this again.")
    partial.rename(path)
    return f"✅ Downloaded {path.relative_to(Path.cwd())}"


def main():
    sys.stdout.reconfigure(errors="replace")
    if len(sys.argv) != 2 or sys.argv[1] not in EXERCISES:
        sys.exit(USAGE)
    project, workbook, data_files = EXERCISES[sys.argv[1]]

    folder = Path.cwd()
    pyproject = folder / "pyproject.toml"
    if not pyproject.exists():
        sys.exit(f"❌ {folder} isn't a project folder: it has no pyproject.toml. Nothing was downloaded.\n   Go to the project first: cd ~/simmer-python/{project}")
    name = tomllib.loads(pyproject.read_text(encoding="utf-8")).get("project", {}).get("name")
    if name != project:
        sys.exit(f"❌ This is the {name} project, but exercise {sys.argv[1]} is done in {project}. Nothing was downloaded.\n   Go to it first: cd ~/simmer-python/{project}")

    print(download(f"{WORKBOOKS}/{workbook}", folder / workbook))
    for data_file in data_files:
        print(download(f"{DATA}/{data_file}", folder / "data" / data_file))
    print(f"\nOpen {workbook} in the {project} project.")


main()
