"""Test Lesson 9's exercises and checks end to end, on macOS or Windows.

Sets up every exercise the way a student would, with uv, in a fresh folder in the user folder. Runs each
check from its URL on the solution and on common mistakes, and compares the scripts' output with the
expected output on the topic pages. On Windows, it also records what PowerShell prints for the steps
the videos show, for the recording notes.

Run it with: uv run --python 3.13 test_checks.py BASE_URL
BASE_URL is where the checks are published, such as
https://raw.githubusercontent.com/team-simmer/python-foundations/main/lesson-09

Exits with 1 if anything doesn't match. In GitHub Actions, it also writes a summary of the run.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

BASE = sys.argv[1].rstrip("/")
ROOT = Path.home() / "simmer-python-test"
WINDOWS = os.name == "nt"
ENVIRONMENT = dict(os.environ, PYTHONIOENCODING="utf-8")
results = []
observed = []

UTM_FUNCTION = '''import sys
from urllib.parse import parse_qs, urlsplit


def utm_params(url):
    """Return the URL's UTM parameters, with lowercase names and the first value of each."""
    params = {}
    for name, values in parse_qs(urlsplit(url).query).items():
        name = name.lower()
        if name.startswith("utm_") and name not in params:
            params[name] = values[0]
    return params


if len(sys.argv) != 2:
    sys.exit("Usage: uv run parse_utm.py URL")

'''

PARSE_UTM = UTM_FUNCTION + '''params = utm_params(sys.argv[1])
if params == {}:
    print("No UTM parameters")
for name, value in params.items():
    print(f"{name}: {value}")
'''

PARSE_UTM_FINAL = UTM_FUNCTION + '''url = sys.argv[1]
print(f"path: {urlsplit(url).path}")
params = utm_params(url)
if params == {}:
    print("No UTM parameters")
for name, value in params.items():
    print(f"{name}: {value}")
'''

REFERRAL_MAIN = '''import tldextract

# Referring hostnames and sessions, from the link tracking tool's export for May 2025
referrals = [
    ("www.pinterest.com", 318),
    ("L.Instagram.com", 205),
    ("www.pinterest.ca", 126),
    ("m.facebook.com", 143),
    ("out.reddit.com", 87),
    ("lm.facebook.com", 96),
    ("linktr.ee", 64),
    ("www.reddit.com", 54),
    ("pinterest.com", 41),
    ("www.pinterest.co.uk", 22),
    ("old.reddit.com", 12),
]


def site_name(hostname):
    return tldextract.extract(hostname).domain.lower()


sessions_by_site = {}
for hostname, sessions in referrals:
    site = site_name(hostname)
    sessions_by_site[site] = sessions_by_site.get(site, 0) + sessions
print(sessions_by_site)
'''

TOPIC_URLS = {
    "https://store.teamsimmer.com/c/jeans?utm_source=google&utm_medium=cpc&UTM_CAMPAIGN=2025_us_search_shopping":
        "utm_source: google\nutm_medium: cpc\nutm_campaign: 2025_us_search_shopping",
    "https://store.teamsimmer.com/new-arrivals?utm_source=newsletter&utm_medium=email&utm_campaign=2025_us_email_newsletter&utm_content=story+ad":
        "utm_source: newsletter\nutm_medium: email\nutm_campaign: 2025_us_email_newsletter\nutm_content: story ad",
    "https://store.teamsimmer.com/c/outerwear":
        "No UTM parameters",
}

FINAL_URLS = {
    "https://store.teamsimmer.com/sale/blackfriday?utm_source=google&utm_medium=cpc&utm_campaign=2025_us_search_blackfriday&utm_content=text+link#size-guide":
        "path: /sale/blackfriday\nutm_source: google\nutm_medium: cpc\nutm_campaign: 2025_us_search_blackfriday\nutm_content: text link",
    "https://store.teamsimmer.com/c/accessories?utm_source=instagram&utm_medium=paid_social&utm_campaign=2024_us_instagram_prospecting&utm_source=newsletter#details":
        "path: /c/accessories\nutm_source: instagram\nutm_medium: paid_social\nutm_campaign: 2024_us_instagram_prospecting",
    "https://store.teamsimmer.com/new-arrivals":
        "path: /new-arrivals\nNo UTM parameters",
}


def run(command, folder):
    """Run a command in a folder, and return its exit code and everything it printed."""
    try:
        finished = subprocess.run(command, cwd=folder, capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENVIRONMENT, timeout=600)
    except FileNotFoundError:
        return None, f"{command[0]} isn't installed"
    return finished.returncode, (finished.stdout + finished.stderr).strip()


def expect(name, output, *wanted):
    """Record whether the output has every one of the wanted texts in it."""
    missing = [text for text in wanted if text not in output]
    results.append((name, not missing, output if missing else ""))


def check(name, script, folder, *wanted, python=None):
    command = ["uv", "run"] + (["--python", python] if python else []) + [f"{BASE}/{script}"]
    expect(name, run(command, folder)[1], *wanted)


def observe(title, command, folder, shell=None):
    """Record what a command prints, for the recording notes."""
    code, output = run(command, folder)
    observed.append((title, shell or " ".join(command), code, output))


def new_project(name, *init_options):
    folder = ROOT / name
    shutil.rmtree(folder, ignore_errors=True)
    run(["uv", "init", *init_options, name], ROOT)
    return folder


def topic_9_1():
    check("9.1 check passes", "check_python.py", ROOT, "Everything matches", python="3.13")
    check("9.1 check notices another Python", "check_python.py", ROOT, "not 3.13", python="3.12")


def topic_9_2():
    script = ROOT / "parse_utm.py"
    script.write_text(PARSE_UTM, encoding="utf-8")
    for url, expected in TOPIC_URLS.items():
        expect(f"9.2 parse_utm.py output for {url}", run(["uv", "run", "parse_utm.py", url], ROOT)[1], expected)
    code, output = run(["uv", "run", "parse_utm.py"], ROOT)
    expect("9.2 parse_utm.py without a URL", f"{code}\n{output}", "1\nUsage: uv run parse_utm.py URL")
    check("9.2 check passes", "check_parse_utm.py", ROOT, "Everything matches")

    script.write_text(PARSE_UTM.replace("for name, value in params.items():", "print(params)\nfor name, value in []:"), encoding="utf-8")
    check("9.2 check notices a printed dictionary", "check_parse_utm.py", ROOT, "That's the dictionary itself")
    script.write_text(PARSE_UTM.replace("if len(sys.argv) != 2:", "if False:"), encoding="utf-8")
    check("9.2 check notices an IndexError", "check_parse_utm.py", ROOT, "IndexError")
    script.rename(ROOT / "parse_utm.py.txt")
    check("9.2 check notices .txt", "check_parse_utm.py", ROOT, "parse_utm.py.txt")
    (ROOT / "parse_utm.py.txt").rename(script)
    script.write_text(PARSE_UTM, encoding="utf-8")


def topic_9_3():
    folder = new_project("referral-report", "--no-package", "--python", "3.13")
    run(["uv", "add", "tldextract"], folder)
    (folder / "main.py").write_text(REFERRAL_MAIN, encoding="utf-8")
    expect("9.3 main.py output", run(["uv", "run", "main.py"], folder)[1], "{'pinterest': 507, 'instagram': 205, 'facebook': 239, 'reddit': 153, 'linktr': 64}")
    check("9.3 check passes", "check_project.py", folder, "Everything matches")
    shutil.rmtree(folder / ".venv")
    observe("uv sync after deleting .venv", ["uv", "sync"], folder)
    check("9.3 check passes after uv sync", "check_project.py", folder, "Everything matches")

    run(["uv", "python", "pin", "3.14"], folder)
    check("9.3 check notices the wrong pin", "check_project.py", folder, ".python-version says 3.14")
    run(["uv", "python", "pin", "3.13"], folder)
    check("9.3 check notices the wrong folder", "check_project.py", ROOT, "There's no pyproject.toml")

    # With a newer Python installed, uv init without --python writes requires-python for it,
    # and uv python pin 3.13 is refused.
    trap = new_project("referral-report-trap", "--no-package")
    expect("9.3 uv init without --python picks the newest Python", (trap / "pyproject.toml").read_text(encoding="utf-8"), 'requires-python = ">=3.14"')
    observe("uv python pin 3.13 in a project created for 3.14", ["uv", "python", "pin", "3.13"], trap)
    check("9.3 check explains the requires-python trap", "check_project.py", trap, "change requires-python")
    shutil.rmtree(trap)

    packaged = new_project("packaged-project")
    check("9.3 check notices a packaged project", "check_project.py", packaged, "src folder")
    shutil.rmtree(packaged)


def final_exercise():
    folder = new_project("campaign-tools", "--no-package", "--python", "3.13")
    run(["uv", "add", "tldextract"], folder)
    lock = (folder / "uv.lock").read_text(encoding="utf-8")
    entry = lock[lock.index('\nname = "tldextract"'):].split("\n[[package]]")[0]
    expect("final: tldextract's four dependencies in uv.lock", entry, '"filelock"', '"idna"', '"requests"', '"requests-file"')
    (folder / "parse_utm.py").write_text(PARSE_UTM_FINAL, encoding="utf-8")
    for url, expected in FINAL_URLS.items():
        expect(f"final: parse_utm.py output for {url}", run(["uv", "run", "parse_utm.py", url], folder)[1], expected)
    check("final: check passes", "check_setup.py", folder, "Everything matches")
    shutil.rmtree(folder / ".venv")
    run(["uv", "sync"], folder)
    check("final: check passes after uv sync", "check_setup.py", folder, "Everything matches")

    observe("The project's Python", ["uv", "run", "python", "-c", "import sys; print(sys.executable)"], folder)
    observe("python main.py outside uv", ["python", "-c", "import tldextract"], folder, shell="python main.py (importing tldextract)")
    return folder


def recording_notes(folder):
    """Record what the terminal prints for the steps the videos show."""
    observe("uv --version", ["uv", "--version"], ROOT)
    observe("uv python list --only-installed", ["uv", "python", "list", "--only-installed"], ROOT)
    url = "https://store.teamsimmer.com/sale/summersale?utm_source=google&utm_medium=cpc"
    if WINDOWS:
        for shell in ("powershell", "pwsh"):
            if shutil.which(shell):
                line = f"uv run parse_utm.py {url}"
                observe(f"Unquoted URL in {shell}", [shell, "-NoProfile", "-Command", line], folder, shell=f"{shell}> {line}")
        observe("Python REPL: uv --version at >>>", ["uv", "run", "--python", "3.13", "python", "-c", "uv --version"], ROOT, shell=">>> uv --version")
    else:
        line = f"uv run parse_utm.py {url}"
        observe("Unquoted URL in zsh", ["zsh", "-c", line], folder, shell=f"zsh% {line}")


def report():
    lines = ["## Lesson 9 checks", "", f"{sys.platform}, Python {sys.version.split()[0]}, checks from {BASE}", ""]
    for name, passed, output in results:
        lines.append(f"- {'✅' if passed else '❌'} {name}")
        if not passed:
            lines += ["", "```text", output, "```", ""]
    lines += ["", "## What the terminal prints", ""]
    for title, shell, code, output in observed:
        lines += [f"### {title}", "", "```text", f"> {shell}", output, f"(exit code {code})", "```", ""]
    text = "\n".join(lines)
    print(text)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as file:
            file.write(text + "\n")
    return all(passed for name, passed, output in results)


def main():
    sys.stdout.reconfigure(errors="replace")
    shutil.rmtree(ROOT, ignore_errors=True)
    ROOT.mkdir()
    # 3.14 stands for a newer Python that a student may already have. 3.12 is the wrong Python in 9.1.
    run(["uv", "python", "install", "3.12", "3.13", "3.14"], ROOT)
    topic_9_1()
    topic_9_2()
    topic_9_3()
    folder = final_exercise()
    recording_notes(folder)
    sys.exit(0 if report() else 1)


main()
