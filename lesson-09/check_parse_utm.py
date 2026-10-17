"""Check your work for Topic 9.2: parse_utm.py prints a URL's UTM parameters.

Run it from the folder that has parse_utm.py in it:
uv run https://raw.githubusercontent.com/team-simmer/python-foundations/main/lesson-09/check_parse_utm.py

It runs your script with test URLs and compares what it prints. It doesn't change anything.
"""

import os
import subprocess
import sys
from pathlib import Path

SCRIPT = "parse_utm.py"
USAGE = "Usage: uv run parse_utm.py URL"
CASES = [
    (
        "https://store.teamsimmer.com/c/jeans?utm_source=google&utm_medium=cpc&UTM_CAMPAIGN=2025_us_search_shopping",
        ["utm_source: google", "utm_medium: cpc", "utm_campaign: 2025_us_search_shopping"],
    ),
    (
        "https://store.teamsimmer.com/c/outerwear?utm_source=facebook&utm_medium=paid_social&utm_campaign=2025_ca_facebook_prospecting&utm_source=newsletter",
        ["utm_source: facebook", "utm_medium: paid_social", "utm_campaign: 2025_ca_facebook_prospecting"],
    ),
    (
        "https://store.teamsimmer.com/new-arrivals?utm_source=newsletter&utm_medium=email&utm_campaign=2025_us_email_newsletter&utm_content=story+ad",
        ["utm_source: newsletter", "utm_medium: email", "utm_campaign: 2025_us_email_newsletter", "utm_content: story ad"],
    ),
    (
        "https://store.teamsimmer.com/c/dresses?utm_source=facebook&utm_medium=paid_social&utm_campaign=2025_us_facebook_retargeting#details",
        ["utm_source: facebook", "utm_medium: paid_social", "utm_campaign: 2025_us_facebook_retargeting"],
    ),
    (
        "https://store.teamsimmer.com/c/pants?utm_source=google&utm_medium=display&utm_campaign=2025_us_display_prospecting&utm_content=hero%20banner",
        ["utm_source: google", "utm_medium: display", "utm_campaign: 2025_us_display_prospecting", "utm_content: hero banner"],
    ),
    (
        "https://store.teamsimmer.com/c/outerwear",
        ["No UTM parameters"],
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
        return " Your script printed nothing. In a script, only print() shows anything: a value on the last line isn't shown, as it is in a notebook."
    if "{" in text:
        return " That's the dictionary itself. Print one line per parameter: for name, value in params.items(): print(f\"{name}: {value}\")."
    if any(line.lower().startswith("utm_") and not line.startswith("utm_") for line in got):
        return " Some names have capitals. Lowercase each name in utm_params(), as in Topic 7.2."
    if "#" in text:
        return " A value still has the fragment (#...) in it. Read the query with urlsplit(url).query and parse_qs(), not by splitting the URL yourself."
    if "%20" in text or "+" in text:
        return " A value is still encoded. parse_qs() decodes %20 and + to spaces, so use it instead of splitting the query yourself."
    if "utm_source: newsletter" in got and "utm_source: facebook" in expected:
        return " When a name appears twice, keep the first value: add a name to the dictionary only if it isn't there yet."
    if len(got) > len(expected) and all(line in got for line in expected):
        return " There are extra lines. Print each parameter once, and nothing else."
    return ""


def check_your_work():
    results = []
    script = Path.cwd() / SCRIPT
    if not script.is_file():
        print(f"❌ There's no {SCRIPT} in {Path.cwd()}. Use cd to go to the folder that has your script in it, then run this check again.")
        if (Path.cwd() / (SCRIPT + ".txt")).is_file():
            print(f"   There's a {SCRIPT}.txt, though: your editor added .txt to the name. Rename the file to {SCRIPT}.")
        return

    wrong = []
    for url, expected in CASES:
        code, output, errors = run(url)
        if code != 0:
            wrong.append(f"With {url}, your script stopped with an error: {last_line(errors)}")
            continue
        got = [line.strip() for line in output.strip().splitlines() if line.strip()]
        if got != expected:
            message = f"For {url}, your script should print:\n      " + "\n      ".join(expected) + "\n   but it printed:\n      " + ("\n      ".join(got) or "(nothing)")
            reason = hint(got, expected).strip()
            wrong.append(message + ("\n   " + reason if reason else ""))
    if not wrong:
        results.append((True, f"{SCRIPT} prints the right UTM parameters for all {len(CASES)} test URLs."))
    else:
        results.append((False, wrong[0]))
        if len(wrong) > 1:
            results.append((False, f"{len(wrong) - 1} more test URL(s) give the wrong output too. Fix the first one, then run this check again."))

    code, output, errors = run()
    shown = (output + errors).strip()
    if code == 0:
        results.append((False, f"Without a URL, your script should stop with \"{USAGE}\", but it finished normally. Use sys.exit(\"{USAGE}\")."))
    elif "IndexError" in errors:
        results.append((False, f"Without a URL, your script stops with an IndexError. Check len(sys.argv) first, and stop with sys.exit(\"{USAGE}\")."))
    elif last_line(shown) != USAGE:
        results.append((False, f"Without a URL, your script should print \"{USAGE}\", but it printed {last_line(shown)!r}."))
    else:
        results.append((True, "Without a URL, your script stops and shows how to use it."))

    for passed, message in results:
        print(("✅ " if passed else "❌ ") + message)
    if all(passed for passed, message in results):
        print("\nEverything matches. Your UTM parser works from the terminal.")
    else:
        print("\nFix the first ❌, save the file, then run this check again.")


# A terminal that can't show ✅ and ❌ gets a ? instead of an error.
sys.stdout.reconfigure(errors="replace")
check_your_work()
