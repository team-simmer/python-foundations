"""Test Lesson 9's exercises and checks end to end, on macOS or Windows.

Sets up every exercise the way a student would, with uv, in a fresh folder in the user folder. Runs each
check from its URL on the solution and on common mistakes, and compares the scripts' output with the
expected output on the topic pages. On Windows, it also records what PowerShell prints for the steps
the videos show, for the recording notes.

It also checks the text the videos show on screen from uv, Python and the shell (the "On screen" lines),
so a new uv release that changes a message the videos show turns the run red.

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

# The Python version the course pins, as in the checks. To move the course to a new version, change it
# here, in every check and in lesson-checks.yml, and change NEWER to a version above it.
PYTHON = "3.13"
# A newer Python that a student may already have, for the requires-python trap in Topic 9.3
NEWER = "3.14"
# An older Python, for "the wrong Python" in Topic 9.1
OLDER = "3.12"

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


def on_screen(shot, output, *wanted):
    """Like expect(), for text a video shows. If it fails, the video no longer matches what students see."""
    expect(f"On screen, {shot}", output, *wanted)


def check(name, script, folder, *wanted, python=None):
    command = ["uv", "run"] + (["--python", python] if python else []) + [f"{BASE}/{script}"]
    expect(name, run(command, folder)[1], *wanted)


def observe(title, command, folder, shell=None):
    """Record what a command prints, for the recording notes."""
    code, output = run(command, folder)
    observed.append((title, shell or " ".join(command), code, output))
    return output


def new_project(name, *init_options):
    folder = ROOT / name
    shutil.rmtree(folder, ignore_errors=True)
    run(["uv", "init", *init_options, name], ROOT)
    return folder


def topic_9_1():
    check("9.1 check passes", "check_python.py", ROOT, "Everything matches", python=PYTHON)
    check("9.1 check notices another Python", "check_python.py", ROOT, f"not {PYTHON}", python=OLDER)

    # Beat 5 installs Python on a computer that doesn't have it yet. Install it again into an empty folder.
    fresh = ROOT / "fresh-python"
    environment = dict(ENVIRONMENT, UV_PYTHON_INSTALL_DIR=str(fresh / "python"), UV_PYTHON_BIN_DIR=str(fresh / "bin"))
    finished = subprocess.run(["uv", "python", "install", PYTHON], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", env=environment)
    on_screen("9.1 beat 5: uv python install", finished.stdout + finished.stderr, f"Installed Python {PYTHON}.")
    shutil.rmtree(fresh, ignore_errors=True)

    on_screen("9.1 beat 7: uv --version at the >>> prompt", run(["uv", "run", "--python", PYTHON, "python", "-c", "uv --version"], ROOT)[1], "NameError: name 'uv' is not defined")


def topic_9_2():
    url = "https://store.teamsimmer.com/sale/summersale?utm_source=google&utm_medium=cpc&utm_campaign=2024_ca_search_summersale#details"
    video = ROOT / "url_parts.py"
    video.write_text("import sys\nfrom urllib.parse import urlsplit\n\nprint(sys.argv)\n", encoding="utf-8")
    on_screen("9.2 beat 4: sys.argv", run(["uv", "run", "url_parts.py", "hello"], ROOT)[1], "['url_parts.py', 'hello']")
    video.write_text("import sys\nfrom urllib.parse import urlsplit\n\nparts = urlsplit(sys.argv[1])\nprint(parts.path)\n", encoding="utf-8")
    on_screen("9.2 beat 7: no URL", run(["uv", "run", "url_parts.py"], ROOT)[1], "IndexError: list index out of range")
    unquoted = "uv run url_parts.py https://store.teamsimmer.com/sale/summersale?utm_source=google&utm_medium=cpc"
    if WINDOWS:
        on_screen("9.2 beat 5: unquoted URL in Windows PowerShell", observe("Unquoted URL in Windows PowerShell 5.1", ["powershell", "-NoProfile", "-Command", unquoted], ROOT, shell=f"PS> {unquoted}"), "The ampersand (&) character is not allowed.")
        if shutil.which("pwsh"):
            on_screen("9.2 beat 5: unquoted URL in PowerShell 7", observe("Unquoted URL in PowerShell 7", ["pwsh", "-NoProfile", "-Command", unquoted], ROOT, shell=f"pwsh> {unquoted}"), "utm_medium=cpc", "is not recognized")
    else:
        on_screen("9.2 beat 5: unquoted URL in zsh", observe("Unquoted URL in zsh", ["zsh", "-c", unquoted], ROOT, shell=f"zsh% {unquoted}"), "zsh:1: no matches found:")
    video.write_text(
        'import sys\nfrom urllib.parse import urlsplit\n\nif len(sys.argv) != 2:\n    sys.exit("Usage: uv run url_parts.py URL")\n\n'
        'parts = urlsplit(sys.argv[1])\nprint(f"host: {parts.netloc}")\nprint(f"path: {parts.path}")\nprint(f"fragment: {parts.fragment}")\n',
        encoding="utf-8",
    )
    on_screen("9.2 beat 6: the parts of a quoted URL", run(["uv", "run", "url_parts.py", url], ROOT)[1], "host: store.teamsimmer.com\npath: /sale/summersale\nfragment: details")
    code, output = run(["uv", "run", "url_parts.py"], ROOT)
    on_screen("9.2 beat 7: the usage line", f"{code}\n{output}", "1\nUsage: uv run url_parts.py URL")
    video.unlink()

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


def topic_9_3_video():
    """The site-names project from Topic 9.3's video, step by step."""
    shutil.rmtree(ROOT / "site-names", ignore_errors=True)
    on_screen("9.3 beat 1: uv init", run(["uv", "init", "--no-package", "--python", PYTHON, "site-names"], ROOT)[1], "Initialized project `site-names`")
    folder = ROOT / "site-names"
    files = sorted(path.name for path in folder.iterdir() if path.name != ".git")
    on_screen("9.3 beat 2: the files uv made", " ".join(files), ".gitignore", ".python-version", "README.md", "main.py", "pyproject.toml")
    on_screen("9.3 beat 2: requires-python", (folder / "pyproject.toml").read_text(encoding="utf-8"), f'requires-python = ">={PYTHON}"', "dependencies = []")
    on_screen("9.3 beat 2: .python-version", (folder / ".python-version").read_text(encoding="utf-8"), PYTHON)
    on_screen("9.3 beat 8: .venv in .gitignore", (folder / ".gitignore").read_text(encoding="utf-8"), ".venv")

    other = new_project("other-project", "--no-package")
    on_screen("9.3 beat 3: the pin that's refused", run(["uv", "python", "pin", PYTHON], other)[1],
              f"error: The requested Python version `{PYTHON}` is incompatible with the project `requires-python` value of `>={NEWER}`.")
    pyproject = other / "pyproject.toml"
    pyproject.write_text(pyproject.read_text(encoding="utf-8").replace(f">={NEWER}", f">={PYTHON}"), encoding="utf-8")
    on_screen("9.3 beat 3: the pin after fixing requires-python", run(["uv", "python", "pin", PYTHON], other)[1], f"Updated `.python-version` from `{NEWER}` -> `{PYTHON}`")
    shutil.rmtree(other)

    on_screen("9.3 beat 4: the first uv run", run(["uv", "run", "main.py"], folder)[1], f"Using CPython {PYTHON}.", "Creating virtual environment at: .venv", "Hello from site-names!")
    (folder / "main.py").write_text(
        'import tldextract\n\nhostnames = ["lm.facebook.com", "www.pinterest.co.uk", "uk.style.yahoo.com", "giftguide.example"]\n'
        "print([tldextract.extract(hostname).domain for hostname in hostnames])\n",
        encoding="utf-8",
    )
    on_screen("9.3 beat 5: before uv add", run(["uv", "run", "main.py"], folder)[1], "ModuleNotFoundError: No module named 'tldextract'")
    added = run(["uv", "add", "tldextract"], folder)[1]
    on_screen("9.3 beat 6: uv add", added, "Resolved 9 packages", "+ certifi==", "+ tldextract==", "+ urllib3==")
    on_screen("9.3 beat 6: the dependency in pyproject.toml", (folder / "pyproject.toml").read_text(encoding="utf-8"), '"tldextract>=')
    on_screen("9.3 beat 6: main.py after uv add", run(["uv", "run", "main.py"], folder)[1], "['facebook', 'pinterest', 'yahoo', 'example']")

    python = "python" if WINDOWS else "python3"
    code, output = run([python, "main.py"], folder)
    if code is not None:
        on_screen(f"9.3 beat 7: {python} main.py", output, "ModuleNotFoundError: No module named 'tldextract'")

    shutil.rmtree(folder / ".venv")
    on_screen("9.3 beat 8: uv sync", observe("uv sync after deleting .venv", ["uv", "sync"], folder), "Creating virtual environment at: .venv", "Installed 8 packages")
    shutil.rmtree(folder)


def topic_9_3():
    folder = new_project("referral-report", "--no-package", "--python", PYTHON)
    run(["uv", "add", "tldextract"], folder)
    (folder / "main.py").write_text(REFERRAL_MAIN, encoding="utf-8")
    expect("9.3 main.py output", run(["uv", "run", "main.py"], folder)[1], "{'pinterest': 507, 'instagram': 205, 'facebook': 239, 'reddit': 153, 'linktr': 64}")
    check("9.3 check passes", "check_project.py", folder, "Everything matches")
    shutil.rmtree(folder / ".venv")
    run(["uv", "sync"], folder)
    check("9.3 check passes after uv sync", "check_project.py", folder, "Everything matches")

    run(["uv", "python", "pin", NEWER], folder)
    check("9.3 check notices the wrong pin", "check_project.py", folder, f".python-version says {NEWER}")
    run(["uv", "python", "pin", PYTHON], folder)
    check("9.3 check notices the wrong folder", "check_project.py", ROOT, "There's no pyproject.toml")

    # With a newer Python installed, uv init without --python writes requires-python for it,
    # and uv python pin is refused.
    trap = new_project("referral-report-trap", "--no-package")
    expect("9.3 uv init without --python picks the newest Python", (trap / "pyproject.toml").read_text(encoding="utf-8"), f'requires-python = ">={NEWER}"')
    check("9.3 check explains the requires-python trap", "check_project.py", trap, "change requires-python")
    shutil.rmtree(trap)

    packaged = new_project("packaged-project")
    check("9.3 check notices a packaged project", "check_project.py", packaged, "src folder")
    shutil.rmtree(packaged)


def final_exercise():
    folder = new_project("campaign-tools", "--no-package", "--python", PYTHON)
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


def recording_notes():
    """Record what the terminal prints for other steps the videos show."""
    observe("uv --version", ["uv", "--version"], ROOT)
    observe("uv python list --only-installed", ["uv", "python", "list", "--only-installed"], ROOT)


def report():
    lines = ["## Lesson 9 checks", "", f"{sys.platform}, Python {sys.version.split()[0]}, checks from {BASE}", ""]
    for name, passed, output in results:
        lines.append(f"- {'✅' if passed else '❌'} {name}")
        if not passed and name.startswith("On screen"):
            lines.append("  The video shows different text from what students now see. Update the topic file, and re-record the shot if it matters.")
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
    run(["uv", "python", "install", OLDER, PYTHON, NEWER], ROOT)
    topic_9_1()
    topic_9_2()
    topic_9_3_video()
    topic_9_3()
    final_exercise()
    recording_notes()
    sys.exit(0 if report() else 1)


main()
