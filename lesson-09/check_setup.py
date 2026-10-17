"""Check your work for the Lesson 9 final exercise: the campaign-tools project.

Run it from the project's folder:
uv run https://raw.githubusercontent.com/team-simmer/python-foundations/main/lesson-09/check_setup.py

It reads the project's files, checks which Python and packages it runs with, and runs parse_utm.py
with test URLs. It doesn't change anything.
"""

import importlib.util
import os
import subprocess
import sys
import tomllib
from pathlib import Path

PROJECT = "campaign-tools"
SCRIPT = "parse_utm.py"
USAGE = "Usage: uv run parse_utm.py URL"
CASES = [
    (
        "https://store.teamsimmer.com/sale/blackfriday?utm_source=google&utm_medium=cpc&utm_campaign=2025_us_search_blackfriday&utm_content=text+link#size-guide",
        ["path: /sale/blackfriday", "utm_source: google", "utm_medium: cpc", "utm_campaign: 2025_us_search_blackfriday", "utm_content: text link"],
    ),
    (
        "https://store.teamsimmer.com/c/accessories?utm_source=instagram&utm_medium=paid_social&utm_campaign=2024_us_instagram_prospecting&utm_source=newsletter#details",
        ["path: /c/accessories", "utm_source: instagram", "utm_medium: paid_social", "utm_campaign: 2024_us_instagram_prospecting"],
    ),
    (
        "https://store.teamsimmer.com/new-arrivals",
        ["path: /new-arrivals", "No UTM parameters"],
    ),
    (
        "https://store.teamsimmer.com/c/jeans?utm_source=google&utm_medium=cpc&UTM_CAMPAIGN=2025_us_search_shopping",
        ["path: /c/jeans", "utm_source: google", "utm_medium: cpc", "utm_campaign: 2025_us_search_shopping"],
    ),
    (
        "https://store.teamsimmer.com/c/shoes?utm_source=youtube&utm_medium=video&utm_campaign=2024_ca_youtube_awareness&utm_content=hero%20banner",
        ["path: /c/shoes", "utm_source: youtube", "utm_medium: video", "utm_campaign: 2024_ca_youtube_awareness", "utm_content: hero banner"],
    ),
]


def run(*arguments):
    """Run the student's script with the arguments, and return its exit code, output and errors."""
    environment = dict(os.environ, PYTHONIOENCODING="utf-8")
    finished = subprocess.run(
        [sys.executable, SCRIPT, *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
        timeout=60,
    )
    return finished.returncode, finished.stdout, finished.stderr


def last_line(text):
    lines = [line for line in text.strip().splitlines() if line.strip()]
    return lines[-1] if lines else ""


def hint(got, expected):
    """Return the likely mistake behind a wrong output."""
    text = "\n".join(got)
    if not got:
        return " Your script printed nothing. In a script, only print() shows anything."
    if not got[0].startswith("path: "):
        return " The first line should be the URL's path: print(f\"path: {urlsplit(url).path}\")."
    if got[0] != expected[0]:
        return " Print only the path, urlsplit(url).path: without the host, the query or the fragment."
    if "{" in text:
        return " That's the dictionary itself. Print one line per parameter: for name, value in params.items(): print(f\"{name}: {value}\")."
    if any(line.lower().startswith("utm_") and not line.startswith("utm_") for line in got):
        return " Some names have capitals. Lowercase each name in utm_params()."
    if "#" in text:
        return " A value still has the fragment (#...) in it. Read the query with urlsplit(url).query and parse_qs()."
    if "%20" in text or "+" in text:
        return " A value is still encoded. parse_qs() decodes %20 and + to spaces."
    if "utm_source: newsletter" in got:
        return " When a name appears twice, keep the first value."
    return ""


def check_project(folder, results):
    """Check the project's files, its Python and tldextract. Return False if there's no project here."""
    pyproject = folder / "pyproject.toml"
    if not pyproject.is_file():
        print(f"❌ There's no pyproject.toml in {folder}. Use cd to go to the {PROJECT} folder, then run this check again.")
        return False
    try:
        project = tomllib.loads(pyproject.read_text(encoding="utf-8")).get("project", {})
    except tomllib.TOMLDecodeError as error:
        print(f"❌ pyproject.toml can't be read: {error}. Undo your changes to it, or create the project again.")
        return False

    if project.get("name") == PROJECT:
        results.append((True, f"This is the {PROJECT} project."))
    else:
        results.append((False, f"This project is called {project.get('name')!r}, not {PROJECT!r}. Create it with the name {PROJECT}."))

    pin = folder / ".python-version"
    pinned = pin.read_text(encoding="utf-8").strip() if pin.is_file() else None
    running = (sys.version_info.major, sys.version_info.minor)
    if pinned != "3.13":
        message = f"The project should be pinned to Python 3.13, but .python-version says {pinned}." if pinned else "There's no .python-version file. Pin the project to Python 3.13."
        if pinned and not str(project.get("requires-python", "")).startswith(">=3.13"):
            message += f" The project was created for Python {pinned}, so its requires-python doesn't allow 3.13 either."
        results.append((False, message))
    elif running != (3, 13):
        results.append((False, f"The project is pinned to 3.13, but Python {running[0]}.{running[1]} is running it. Run the check with uv run from the {PROJECT} folder."))
    else:
        results.append((True, f"The project is pinned to Python 3.13, and Python {sys.version.split()[0]} runs it."))

    venv = folder / ".venv"
    dependencies = [str(item).lower().replace("_", "-") for item in project.get("dependencies", [])]
    declared = any(item.startswith("tldextract") for item in dependencies)
    lock = folder / "uv.lock"
    locked = lock.is_file() and 'name = "tldextract"' in lock.read_text(encoding="utf-8")
    spec = importlib.util.find_spec("tldextract")
    if not declared:
        if spec is not None:
            results.append((False, "tldextract is installed, but it isn't in pyproject.toml, so uv sync would remove it. Add it with uv add, not pip install."))
        else:
            results.append((False, "tldextract isn't in the project's dependencies in pyproject.toml. Add it with uv add."))
    elif not locked:
        results.append((False, "tldextract is in pyproject.toml, but not in uv.lock. Run uv lock, or add the package again with uv add."))
    else:
        results.append((True, "tldextract is in pyproject.toml and uv.lock."))

    if Path(sys.prefix).resolve() != venv.resolve():
        results.append((False, f"The check isn't running in this project's .venv, but in {sys.prefix}. Run it with uv run from the {PROJECT} folder."))
    elif spec is None or spec.origin is None:
        results.append((False, "tldextract can't be imported in the project's .venv. Run uv sync to install the packages in uv.lock."))
    elif Path(spec.origin).resolve().is_relative_to(venv.resolve()):
        results.append((True, "tldextract imports from the project's .venv."))
    else:
        results.append((False, f"tldextract imports from {spec.origin}, which isn't in this project's .venv."))
    return True


def check_script(folder, results):
    if not (folder / SCRIPT).is_file():
        results.append((False, f"There's no {SCRIPT} in the project's folder. Save it next to pyproject.toml."))
        return

    wrong = []
    for url, expected in CASES:
        code, output, errors = run(url)
        if code != 0:
            wrong.append(f"With {url}, {SCRIPT} stopped with an error: {last_line(errors)}")
            continue
        got = [line.strip() for line in output.strip().splitlines() if line.strip()]
        if got != expected:
            message = f"For {url}, {SCRIPT} should print:\n      " + "\n      ".join(expected) + "\n   but it printed:\n      " + ("\n      ".join(got) or "(nothing)")
            reason = hint(got, expected).strip()
            wrong.append(message + ("\n   " + reason if reason else ""))
    if not wrong:
        results.append((True, f"{SCRIPT} prints the right path and UTM parameters for all {len(CASES)} test URLs."))
    else:
        results.append((False, wrong[0]))
        if len(wrong) > 1:
            results.append((False, f"{len(wrong) - 1} more test URL(s) give the wrong output too. Fix the first one, then run this check again."))

    code, output, errors = run()
    shown = (output + errors).strip()
    if code == 0:
        results.append((False, f"Without a URL, {SCRIPT} should stop with \"{USAGE}\", but it finished normally. Use sys.exit()."))
    elif "IndexError" in errors:
        results.append((False, f"Without a URL, {SCRIPT} stops with an IndexError. Check len(sys.argv) first, and stop with sys.exit(\"{USAGE}\")."))
    elif last_line(shown) != USAGE:
        results.append((False, f"Without a URL, {SCRIPT} should print \"{USAGE}\", but it printed {last_line(shown)!r}."))
    else:
        results.append((True, f"Without a URL, {SCRIPT} stops and shows how to use it."))


def check_your_work():
    folder = Path.cwd()
    results = []
    if not check_project(folder, results):
        return
    check_script(folder, results)

    for passed, message in results:
        print(("✅ " if passed else "❌ ") + message)
    if all(passed for passed, message in results):
        print("\nEverything matches. If you haven't yet: delete .venv, run uv sync, and run this check again.")
    else:
        print("\nFix the first ❌, then run this check again.")


# A terminal that can't show ✅ and ❌ gets a ? instead of an error.
sys.stdout.reconfigure(errors="replace")
check_your_work()
