"""Test lesson 10's workbooks, checks and the messages its videos show, end to end, on macOS or Windows.

Sets up the videos' and exercises' projects with uv in a fresh folder in the user folder, downloads every
workbook with get_files.py, and runs it with jupyter execute: as it's downloaded, with its solution and with
common mistakes, in the project's kernel and in the kernel of a JupyterLab started with uvx. The "Check your
work" cell's output is compared with what the topic pages say. On Windows, it also records the paths the
inserts in "Recording on Windows" show.

It also checks the text the videos show on screen (the "On screen" lines), so a new uv, JupyterLab or
ipykernel that changes a message the videos show turns the run red.

Run it with: uv run --python 3.13 test_notebooks.py BASE_URL
BASE_URL is where lesson 10's files are published, such as
https://raw.githubusercontent.com/team-simmer/python-foundations/main/lesson-10
The workbooks with their solutions filled in are in the solved folder next to this file.

Exits with 1 if anything doesn't match. In GitHub Actions, it also writes a summary of the run.
"""

import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

# The Python version the course pins, as in lesson 9.'s checks and lesson-checks.yml
PYTHON = "3.13"

BASE = sys.argv[1].rstrip("/")
SOLVED = Path(__file__).parent / "solved"
ROOT = Path.home() / "simmer-python-test-10"
WINDOWS = os.name == "nt"
ENVIRONMENT = dict(os.environ, PYTHONIOENCODING="utf-8", SIMMER_WORKBOOKS=BASE)
results = []
observed = []

VIDEO_CELLS = [
    "import sys\n\nprint(sys.executable)",
    'import csv\n\nCSV_PATH = "data/sessions_export_2024_03.csv"\n\nwith open(CSV_PATH, newline="", encoding="utf-8") as file:\n    rows = list(csv.DictReader(file))\nlen(rows)',
    'sessions_by_source_medium = {}\nfor row in rows:\n    key = (row["session_source"], row["session_medium"])\n    sessions_by_source_medium[key] = sessions_by_source_medium.get(key, 0) + int(row["sessions"])\nlen(sessions_by_source_medium)',
    'sessions_by_source_medium[("google", "cpc")]',
    'from collections import Counter\n\ntop_five = Counter(sessions_by_source_medium).most_common(5)\nfor (source, medium), sessions in top_five:\n    print(f"{source} / {medium}: {sessions}")',
    'sessions_by_source_medium[("Facebook", "paid_social")], sessions_by_source_medium[("fb", "paid_social")]',
    '{["google", "cpc"]: 1}',
    'from google.colab import drive\n\ndrive.mount("/content/drive")',
]

VIDEO_10_2_CELLS = [
    "import sys\n\nprint(sys.executable)",
    "%pip install tldextract",
    "import tldextract\n\n\ndef site_name(hostname):\n    return tldextract.extract(hostname).domain.lower()",
    'import csv\n\nwith open("data/sessions_export_2024_03.csv", newline="", encoding="utf-8") as file:\n    rows = list(csv.DictReader(file))\nreferral_hostnames = {row["session_source"] for row in rows if row["session_medium"] == "referral"}\nlen(referral_hostnames)',
    "sorted({site_name(hostname) for hostname in referral_hostnames})",
    'sorted({hostname for hostname in referral_hostnames if site_name(hostname) == "facebook"})',
]


def run(command, folder, environment=None):
    """Run a command in a folder, and return its exit code and everything it printed."""
    try:
        finished = subprocess.run(command, cwd=folder, capture_output=True, text=True, encoding="utf-8", errors="replace", env=environment or ENVIRONMENT, timeout=900)
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


def observe(title, command, folder, shell=None):
    """Record what a command prints, for the recording notes."""
    code, output = run(command, folder)
    observed.append((title, shell or " ".join(command), code, output))
    return output


def new_project(name, jupyterlab=True):
    folder = ROOT / name
    shutil.rmtree(folder, ignore_errors=True)
    run(["uv", "init", "--no-package", "--python", PYTHON, name], ROOT)
    run(["uv", "add", "tldextract"], folder)
    if jupyterlab:
        run(["uv", "add", "--dev", "jupyterlab"], folder)
    return folder


def write_notebook(path, sources):
    cells = [{"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": source} for source in sources]
    notebook = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3 (ipykernel)", "language": "python", "name": "python3"}}, "nbformat": 4, "nbformat_minor": 4}
    path.write_text(json.dumps(notebook, indent=1), encoding="utf-8")


def edit_notebook(source, target, replace=(), delete=()):
    """Copy a notebook, replacing text in its cells and leaving out the cells that contain any of delete."""
    notebook = json.loads(source.read_text(encoding="utf-8"))
    cells = []
    for cell in notebook["cells"]:
        text = "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
        if any(marker in text for marker in delete):
            continue
        for old, new in replace:
            text = text.replace(old, new)
        cell["source"] = text
        cells.append(cell)
    notebook["cells"] = cells
    target.write_text(json.dumps(notebook, indent=1, ensure_ascii=False), encoding="utf-8")


def text_of(value):
    return "".join(value) if isinstance(value, list) else value


def execute(folder, name, uvx=False, kernel=None, environment=None):
    """Run a notebook with jupyter execute, as Run All would, and return everything its cells printed."""
    command = (["uvx", "jupyter"] if uvx else ["uv", "run", "jupyter"]) + ["execute", "--allow-errors", name, f"--output={Path(name).stem}.out.ipynb"]
    if kernel:
        command.append(f"--kernel_name={kernel}")
    # On Windows, jupyter execute reads the notebook in the system's code page unless Python runs in UTF-8 mode.
    # JupyterLab and VS Code always read notebooks as UTF-8, so this only affects the test.
    code, log = run(command, folder, dict(environment or ENVIRONMENT, PYTHONUTF8="1"))
    executed = folder / f"{Path(name).stem}.out.ipynb"
    if not executed.exists():
        return f"jupyter execute didn't run the notebook (exit code {code}):\n{log}"
    texts = []
    for cell in json.loads(executed.read_text(encoding="utf-8"))["cells"]:
        for output in cell.get("outputs", []):
            if output["output_type"] == "stream":
                texts.append(text_of(output["text"]))
            elif output["output_type"] == "error":
                texts.append(f"{output['ename']}: {output['evalue']}")
            elif "text/plain" in output.get("data", {}):
                texts.append(text_of(output["data"]["text/plain"]))
    executed.unlink()
    return "\n".join(texts)


def get_files(folder, exercise):
    return run(["uv", "run", f"{BASE}/get_files.py", exercise], folder)[1]


def start_jupyter_lab(folder):
    """Start JupyterLab as the videos do, read what it prints until it's ready, stop it and return the output."""
    options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if WINDOWS else {"start_new_session": True}
    process = subprocess.Popen(["uv", "run", "jupyter", "lab", "--no-browser"], cwd=folder, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", env=ENVIRONMENT, **options)
    lines = []
    reader = threading.Thread(target=lambda: lines.extend(process.stdout), daemon=True)
    reader.start()
    deadline = time.time() + 180
    while time.time() < deadline and not any("Or copy and paste one of these URLs" in line for line in lines):
        time.sleep(1)
    time.sleep(3)
    if WINDOWS:
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True)
    else:
        os.killpg(process.pid, signal.SIGTERM)
    process.wait(timeout=60)
    return re.sub(r"token=[0-9a-f]+", "token=<token>", "".join(lines))


def videos():
    folder = new_project("site-names", jupyterlab=False)
    added = observe("uv add --dev jupyterlab", ["uv", "add", "--dev", "jupyterlab"], folder)
    on_screen("10.1 beat 1: uv add --dev jupyterlab", added, "+ jupyterlab==", "+ websocket-client==")
    on_screen("10.1 beat 1: pyproject.toml", (folder / "pyproject.toml").read_text(encoding="utf-8"), "[dependency-groups]\ndev = [\n    \"jupyterlab>=")
    started = start_jupyter_lab(folder)
    observed.append(("uv run jupyter lab", "uv run jupyter lab", None, started))
    on_screen("10.1 beat 2: JupyterLab's last lines", started, "Use Control-C to stop this server and shut down all kernels (twice to skip confirmation).", "http://localhost:8888/lab?token=", "Or copy and paste one of these URLs:")

    (folder / "data").mkdir()
    shutil.copy(ROOT / "data" / "sessions_export_2024_03.csv", folder / "data")
    write_notebook(folder / "source-medium.ipynb", VIDEO_CELLS)
    output = execute(folder, "source-medium.ipynb")
    observed.append(("The video's notebook in the project's kernel", "uv run jupyter execute source-medium.ipynb", None, output))
    venv_python = str(folder / ".venv" / ("Scripts" if WINDOWS else "bin") / ("python.exe" if WINDOWS else "python"))
    on_screen("10.1 beat 4: sys.executable", output, venv_python)
    on_screen("10.1 beat 6: len(rows)", output, "1936")
    on_screen("10.1 beat 7: tuple keys", output, "\n24\n", "11761")
    on_screen("10.1 beat 7: a list as a key", output, "TypeError: unhashable type: 'list'")
    on_screen("10.1 beat 8: the top five", output, "google / organic: 19823\n(direct) / (none): 13622\ngoogle / cpc: 11761\nfacebook / paid_social: 8843\nnewsletter / email: 8061", "(805, 699)")
    on_screen("10.1 beat 6: the Drive cell", output, "ModuleNotFoundError: No module named 'google'")

    on_screen("10.2 beat 1: uvx jupyter lab's warning", run(["uvx", "jupyter", "--version"], folder)[1], "warning: An executable named `jupyter` is not provided by package `jupyter` but is available via the dependency `jupyter-core`.")
    write_notebook(folder / "kernel.ipynb", VIDEO_10_2_CELLS)
    output = execute(folder, "kernel.ipynb", uvx=True)
    observed.append(("The 10.2 video's cells in a uvx JupyterLab's kernel", "uvx jupyter execute kernel.ipynb", None, output))
    on_screen("10.2 beat 2: import in uvx's kernel", output, "ModuleNotFoundError: No module named 'tldextract'")
    on_screen("10.2 beat 3: %pip in uvx's kernel", output, "No module named pip", "Note: you may need to restart the kernel to use updated packages.")
    on_screen("10.2 beat 4: uvx's kernel is in uv's cache", output.splitlines()[0] if output else "", "archive-v0")
    installed = observe("Register the project's kernel", ["uv", "run", "python", "-m", "ipykernel", "install", "--user", "--name", "site-names", "--display-name", "site-names"], folder)
    on_screen("10.2 beat 5: ipykernel install", installed, "Installed kernelspec site-names in")
    output = execute(folder, "kernel.ipynb", uvx=True, kernel="site-names")
    on_screen("10.2 beat 6: the project's kernel in uvx's JupyterLab", output, venv_python)
    on_screen("10.2 beat 7: set comprehensions", output, "\n11\n", "['example', 'facebook', 'instagram']", "['facebook.com', 'l.facebook.com', 'lm.facebook.com', 'm.facebook.com']")
    on_screen("10.2 beat 6: %pip in the project's kernel", output, "No module named pip")
    on_screen("10.2 beat 9: kernelspec list", observe("Registered kernels", ["uv", "run", "jupyter", "kernelspec", "list"], folder), "python3", "site-names")
    run(["uv", "run", "jupyter", "kernelspec", "remove", "-y", "site-names"], folder)


def topic_10_1():
    folder = new_project("referral-report")
    expect("get_files.py outside a project stops", get_files(ROOT, "10.1"), "isn't a project folder", "Nothing was downloaded")
    expect("get_files.py in the wrong project stops", get_files(ROOT / "site-names", "10.1"), "is done in referral-report")
    expect("get_files.py with no exercise shows its usage", run(["uv", "run", f"{BASE}/get_files.py"], folder)[1], "EXERCISE is 10.1, 10.2, 10.3 or final")
    downloaded = observe("get_files.py 10.1", ["uv", "run", f"{BASE}/get_files.py", "10.1"], folder)
    expect("10.1 get_files.py downloads the workbook and data", downloaded, "Downloaded 10.1-source-medium.ipynb", "sessions_export_2024_02.csv")
    expect("10.1 get_files.py never replaces a file", get_files(folder, "10.1"), "Already there, not replaced: 10.1-source-medium.ipynb")
    output = execute(folder, "10.1-source-medium.ipynb")
    expect("10.1 workbook as downloaded: the Drive cell fails and the check says why", output, "ModuleNotFoundError: No module named 'google'", "CSV_PATH is still Colab's path", "✅ The kernel is referral-report's .venv.")
    shutil.copy(SOLVED / "10.1-source-medium.ipynb", folder / "solved.ipynb")
    output = execute(folder, "solved.ipynb")
    expect("10.1 solution passes", output, "Everything matches", "google / organic: 18199\ngoogle / cpc: 12611\n(direct) / (none): 12313\nyoutube / video: 9856\nfacebook / paid_social: 6874")
    edit_notebook(folder / "solved.ipynb", folder / "mistake.ipynb", replace=[('key = (row["session_source"], row["session_medium"])', 'key = row["session_source"] + " / " + row["session_medium"]')])
    expect("10.1 check notices text keys", execute(folder, "mistake.ipynb"), "Use a tuple of the two values as the key")
    edit_notebook(folder / "solved.ipynb", folder / "mistake.ipynb", replace=[('CSV_PATH = "data/sessions_export_2024_02.csv"', f"CSV_PATH = {str(folder / 'data' / 'sessions_export_2024_02.csv')!r}")])
    expect("10.1 check notices an absolute path", execute(folder, "mistake.ipynb"), "which only works on your computer")
    edit_notebook(folder / "solved.ipynb", folder / "mistake.ipynb", replace=[("int(row[\"sessions\"])", "1")])
    expect("10.1 check notices counting rows", execute(folder, "mistake.ipynb"), "counts rows, not sessions")
    expect("10.1 check notices uvx's kernel", execute(folder, "solved.ipynb", uvx=True), "the Python of a JupyterLab started with uvx")
    (folder / "solved.ipynb").unlink()
    (folder / "mistake.ipynb").unlink()


def topic_10_2():
    folder = ROOT / "referral-report"
    expect("10.2 get_files.py downloads the workbook and data", get_files(folder, "10.2"), "Downloaded 10.2-referral-hostnames.ipynb", "sessions_export_2024_04.csv")
    output = execute(folder, "10.2-referral-hostnames.ipynb", uvx=True)
    observed.append(("The 10.2 workbook as downloaded, in a uvx JupyterLab's kernel", "uvx jupyter execute 10.2-referral-hostnames.ipynb", None, output))
    expect("10.2 workbook in uvx's kernel: %pip, the import and the check", output, "No module named pip", "ModuleNotFoundError: No module named 'tldextract'", "the Python of the JupyterLab you started with uvx", "There's no kernel called referral-report")
    run(["uv", "run", "python", "-m", "ipykernel", "install", "--user", "--name", "referral-report", "--display-name", "referral-report"], folder)
    shutil.copy(SOLVED / "10.2-referral-hostnames.ipynb", folder / "solved.ipynb")
    expect("10.2 solution passes in uvx's JupyterLab with the referral-report kernel", execute(folder, "solved.ipynb", uvx=True, kernel="referral-report"), "Everything matches", "✅ referral-report is registered as a kernel.", "'wardrobewire.example'")
    expect("10.2 solution passes in the project's kernel", execute(folder, "solved.ipynb"), "Everything matches")
    edit_notebook(folder / "solved.ipynb", folder / "mistake.ipynb", replace=[("facebook_hosts | instagram_hosts", "facebook_hosts & instagram_hosts")])
    expect("10.2 check notices & instead of |", execute(folder, "mistake.ipynb"), "Use |, the union")
    edit_notebook(folder / "solved.ipynb", folder / "mistake.ipynb", replace=[('referral_hostnames = {row["session_source"] for row in rows if row["session_medium"] == "referral"}', 'referral_hostnames = [row["session_source"] for row in rows if row["session_medium"] == "referral"]')])
    expect("10.2 check notices a list", execute(folder, "mistake.ipynb"), "Use curly braces instead of square brackets")
    edit_notebook(folder / "solved.ipynb", folder / "mistake.ipynb", replace=[("referral_hostnames - social_hosts", "social_hosts - referral_hostnames")])
    expect("10.2 check notices a difference the wrong way round", execute(folder, "mistake.ipynb"), "The order matters in a difference")
    run(["uv", "run", "jupyter", "kernelspec", "remove", "-y", "referral-report"], folder)
    expect("10.2 check notices a kernel that isn't registered", execute(folder, "solved.ipynb"), "There's no kernel called referral-report")
    (folder / "solved.ipynb").unlink()
    (folder / "mistake.ipynb").unlink()


def topic_10_3():
    folder = ROOT / "referral-report"
    expect("10.3 get_files.py downloads the workbook and data", get_files(folder, "10.3"), "Downloaded 10.3-new-campaigns.ipynb", "sessions_export_2025_02.csv", "sessions_export_2025_03.csv")
    shutil.copy(SOLVED / "10.3-new-campaigns.ipynb", folder / "solved.ipynb")
    expect("10.3 solution passes", execute(folder, "solved.ipynb"), "Everything matches", "'2025_us_search_springsale'", "\n20")
    expect("10.3 check notices JupyterLab", execute(folder, "solved.ipynb", environment=dict(ENVIRONMENT, JPY_SESSION_NAME="solved.ipynb")), "This exercise is for VS Code")
    edit_notebook(folder / "solved.ipynb", folder / "mistake.ipynb", replace=[("new_campaigns = march_campaigns - feb_campaigns", "new_campaigns = feb_campaigns - march_campaigns"), ("ended_campaigns = feb_campaigns - march_campaigns", "ended_campaigns = march_campaigns - feb_campaigns")])
    expect("10.3 check notices new and ended the wrong way round", execute(folder, "mistake.ipynb"), "the wrong way round")
    edit_notebook(folder / "solved.ipynb", folder / "mistake.ipynb", replace=[(" - NOT_CAMPAIGNS", "")])
    expect("10.3 check notices the values that aren't campaigns", execute(folder, "mistake.ipynb"), "still has the values that aren't campaigns")
    (folder / "solved.ipynb").unlink()
    (folder / "mistake.ipynb").unlink()


def final_exercise():
    folder = new_project("campaign-tools", jupyterlab=False)
    expect("Final: uv run jupyter lab before JupyterLab is added", run(["uv", "run", "jupyter", "lab", "--version"], folder)[1], "Failed to spawn: jupyter")
    run(["uv", "add", "--dev", "jupyterlab"], folder)
    expect("Final: get_files.py downloads the notebook and data", get_files(folder, "final"), "Downloaded channel_report.ipynb", "sessions_export_2024_01.csv")
    output = execute(folder, "channel_report.ipynb")
    expect("Final: the notebook as downloaded fails in the Colab cells", output, "No module named pip", "ModuleNotFoundError: No module named 'google'", "CSV_PATH is still Colab's path")
    edit_notebook(folder / "channel_report.ipynb", folder / "solved.ipynb", delete=["%pip install", "google.colab import"], replace=[('"/content/drive/MyDrive/simmer-python/sessions_export_2024_01.csv"', '"data/sessions_export_2024_01.csv"')])
    output = execute(folder, "solved.ipynb")
    expect("Final: the solution passes", output, "Everything matches", "{'Referral': 2655, 'Organic Social': 4640}", "✅ This is the campaign-tools project, with JupyterLab as a development dependency.")
    expect("Final: the check names JupyterLab", execute(folder, "solved.ipynb", environment=dict(ENVIRONMENT, JPY_SESSION_NAME="solved.ipynb")), "✅ This notebook runs in JupyterLab.", "Everything matches in JupyterLab.")
    expect("Final: the check notices uvx's kernel", execute(folder, "solved.ipynb", uvx=True), "the Python of a JupyterLab started with uvx")
    edit_notebook(folder / "channel_report.ipynb", folder / "mistake.ipynb", delete=["%pip install", "google.colab import"])
    expect("Final: the check notices the Drive path", execute(folder, "mistake.ipynb"), "CSV_PATH is still Colab's path")
    run(["uv", "remove", "--dev", "jupyterlab"], folder)
    run(["uv", "add", "jupyterlab"], folder)
    expect("Final: the check notices JupyterLab as an ordinary dependency", execute(folder, "solved.ipynb"), "JupyterLab isn't a development dependency")
    (folder / "solved.ipynb").unlink()
    (folder / "mistake.ipynb").unlink()


def report():
    lines = ["## Lesson 10 notebooks", "", f"{sys.platform}, Python {sys.version.split()[0]}, files from {BASE}", ""]
    for name, passed, output in results:
        lines.append(f"- {'✅' if passed else '❌'} {name}")
        if not passed and name.startswith("On screen"):
            lines.append("  The video shows different text from what students now see. Update the topic file, and re-record the shot if it matters.")
        if not passed:
            lines += ["", "```text", output, "```", ""]
    lines += ["", "## What the terminal and the notebooks print", ""]
    for title, shell, code, output in observed:
        lines += [f"### {title}", "", "```text", f"> {shell}", output] + ([f"(exit code {code})"] if code is not None else []) + ["```", ""]
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
    (ROOT / "data").mkdir(parents=True)
    run(["uv", "python", "install", PYTHON], ROOT)
    run([sys.executable, "-c", "import urllib.request, sys; urllib.request.urlretrieve(sys.argv[1], sys.argv[2])", "https://storage.googleapis.com/simmer-python-course-data/simmer-store/v1/sessions_export_2024_03.csv", str(ROOT / "data" / "sessions_export_2024_03.csv")], ROOT)
    videos()
    topic_10_1()
    topic_10_2()
    topic_10_3()
    final_exercise()
    sys.exit(0 if report() else 1)


main()
