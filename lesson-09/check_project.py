"""Check your work for Topic 9.3: the referral-report project and its main.py.

Run it from the project's folder:
uv run https://raw.githubusercontent.com/team-simmer/python-foundations/main/lesson-09/check_project.py

It reads the project's files, checks which Python and packages it runs with, and runs main.py.
It doesn't change anything.
"""

import ast
import importlib.util
import os
import subprocess
import sys
import tomllib
from pathlib import Path

# The Python version the course pins. Change it here, in every check, in test_checks.py and in lesson-checks.yml.
PYTHON = "3.13"
PROJECT = "referral-report"
EXPECTED = {"pinterest": 507, "instagram": 205, "facebook": 239, "reddit": 153, "linktr": 64}


def last_line(text):
    lines = [line for line in text.strip().splitlines() if line.strip()]
    return lines[-1] if lines else ""


def check_your_work():
    folder = Path.cwd()
    results = []

    pyproject = folder / "pyproject.toml"
    if not pyproject.is_file():
        print(f"❌ There's no pyproject.toml in {folder}. Use cd to go to the {PROJECT} folder, then run this check again.")
        return
    try:
        project = tomllib.loads(pyproject.read_text(encoding="utf-8")).get("project", {})
    except tomllib.TOMLDecodeError as error:
        print(f"❌ pyproject.toml can't be read: {error}. Undo your changes to it, or create the project again.")
        return

    if project.get("name") == PROJECT:
        results.append((True, f"This is the {PROJECT} project."))
    else:
        results.append((False, f"This project is called {project.get('name')!r}, not {PROJECT!r}. Create it with uv init --no-package --python {PYTHON} {PROJECT}, then cd {PROJECT}."))

    pin = folder / ".python-version"
    pinned = pin.read_text(encoding="utf-8").strip() if pin.is_file() else None
    if pinned is None:
        results.append((False, f"There's no .python-version file. Pin the version with uv python pin {PYTHON}."))
    elif pinned != PYTHON:
        message = f".python-version says {pinned}, not {PYTHON}. Pin the version with uv python pin {PYTHON}."
        if not str(project.get("requires-python", "")).startswith(f">={PYTHON}"):
            message += f" If uv says {PYTHON} is incompatible, the project was created for Python {pinned}: in pyproject.toml, change requires-python to \">={PYTHON}\", or create the project again with uv init --no-package --python {PYTHON} {PROJECT}."
        results.append((False, message))
    else:
        results.append((True, f"The project is pinned to Python {PYTHON}."))

    running = f"{sys.version_info.major}.{sys.version_info.minor}"
    if running == PYTHON:
        results.append((True, f"Python {sys.version.split()[0]} is running the project."))
    else:
        results.append((False, f"Python {running} is running the project, not {PYTHON}. Pin the version with uv python pin {PYTHON}, then run the check again: uv run sets up the project's .venv again for {PYTHON}."))

    venv = folder / ".venv"
    if Path(sys.prefix).resolve() == venv.resolve():
        results.append((True, "The check runs in the project's .venv."))
    else:
        results.append((False, f"The check isn't running in this project's .venv, but in {sys.prefix}. Run it with uv run from the {PROJECT} folder."))

    dependencies = [str(item).lower().replace("_", "-") for item in project.get("dependencies", [])]
    declared = any(item.startswith("tldextract") for item in dependencies)
    spec = importlib.util.find_spec("tldextract")
    if declared:
        results.append((True, "tldextract is in the project's dependencies in pyproject.toml."))
    elif spec is not None:
        results.append((False, "tldextract is installed in .venv, but it isn't in pyproject.toml, so uv sync would remove it. Add it with uv add tldextract, not pip install."))
    else:
        results.append((False, "tldextract isn't in the project's dependencies. Add it with uv add tldextract."))

    lock = folder / "uv.lock"
    if not lock.is_file():
        results.append((False, "There's no uv.lock. uv add creates it. If you deleted it, run uv lock."))
    elif 'name = "tldextract"' in lock.read_text(encoding="utf-8"):
        results.append((True, "uv.lock has the exact version of tldextract and every package it needs."))
    else:
        results.append((False, "uv.lock doesn't have tldextract in it. Add the package with uv add tldextract."))

    if spec is None or spec.origin is None:
        results.append((False, "tldextract can't be imported in the project's .venv. Run uv sync to install the packages in uv.lock."))
    elif Path(spec.origin).resolve().is_relative_to(venv.resolve()):
        results.append((True, "tldextract imports from the project's .venv."))
    else:
        results.append((False, f"tldextract imports from {spec.origin}, which isn't in this project's .venv. Run the check with uv run from the {PROJECT} folder."))

    main = folder / "main.py"
    if not main.is_file():
        if (folder / "src").is_dir():
            results.append((False, f"There's no main.py, but there's a src folder: the project was created without --no-package. Delete the {PROJECT} folder and create it again with uv init --no-package --python {PYTHON} {PROJECT}."))
        else:
            results.append((False, f"There's no main.py in the project. uv init --no-package --python {PYTHON} creates it."))
    else:
        environment = dict(os.environ, PYTHONIOENCODING="utf-8")
        finished = subprocess.run([sys.executable, "main.py"], capture_output=True, text=True, encoding="utf-8", env=environment, timeout=120)
        output = last_line(finished.stdout)
        try:
            totals = ast.literal_eval(output)
        except (ValueError, SyntaxError):
            totals = None
        if finished.returncode != 0:
            error = last_line(finished.stderr)
            message = f"main.py stopped with an error: {error}"
            if "ModuleNotFoundError" in error and "tldextract" in error:
                message += " Add tldextract with uv add tldextract, and run main.py with uv run main.py."
            results.append((False, message))
        elif output.startswith("Hello from"):
            results.append((False, "main.py still prints uv's greeting. Replace its code with your code from Topic 8.3, ending with print(sessions_by_site)."))
        elif totals == EXPECTED:
            results.append((True, "main.py prints the right sessions for every site."))
        elif not isinstance(totals, dict):
            results.append((False, f"main.py's last line should be the dictionary sessions_by_site, but it is {output!r}. End main.py with print(sessions_by_site)."))
        elif "co" in totals or "com" in totals:
            results.append((False, f"sessions_by_site has the key 'co' or 'com', which isn't a site. Use tldextract.extract(hostname).domain in site_name(). It is {totals!r}."))
        elif any(isinstance(key, str) and key != key.lower() for key in totals):
            results.append((False, f"sessions_by_site has names with capitals. Return the name in lowercase from site_name(). It is {totals!r}."))
        elif sum(value for value in totals.values() if isinstance(value, int)) == 11:
            results.append((False, "sessions_by_site counts hostnames, not sessions. Add each hostname's sessions to its site's total."))
        else:
            results.append((False, f"sessions_by_site should be {EXPECTED}, but it is {totals!r}."))

    for passed, message in results:
        print(("✅ " if passed else "❌ ") + message)
    if all(passed for passed, message in results):
        print("\nEverything matches. Now delete .venv, run uv sync and run this check again.")
    else:
        print("\nFix the first ❌, then run this check again.")


# A terminal that can't show ✅ and ❌ gets a ? instead of an error.
sys.stdout.reconfigure(errors="replace")
check_your_work()
